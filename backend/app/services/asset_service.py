import json
import sqlite3
import uuid
from typing import Any, Dict, List, Optional
from backend.app.services.ingest_service import get_or_create_manufacturer, get_or_create_asset_model

def recalculate_device_totals(conn: sqlite3.Connection, device_id: str) -> None:
    """Recalculates total RAM and Storage for a host device."""
    cur = conn.cursor()
    # Check if device has a device_profile
    cur.execute("SELECT asset_id FROM device_profiles WHERE asset_id = ?;", (device_id,))
    if not cur.fetchone():
        return

    # Total RAM
    cur.execute(
        """
        SELECT a.specs
        FROM assets a
        JOIN asset_models am ON a.asset_model_id = am.id
        WHERE a.parent_asset_id = ? AND a.status = 'installed' AND am.component_type_id = 'ct-ram';
        """,
        (device_id,),
    )
    total_ram_mb = 0
    for r in cur.fetchall():
        s = json.loads(r["specs"] or "{}")
        total_ram_mb += int(s.get("capacity_mb", 0) or 0)

    # Total Storage
    cur.execute(
        """
        SELECT a.specs
        FROM assets a
        JOIN asset_models am ON a.asset_model_id = am.id
        WHERE a.parent_asset_id = ? AND a.status = 'installed' AND am.component_type_id = 'ct-storage';
        """,
        (device_id,),
    )
    total_storage_gb = 0.0
    for r in cur.fetchall():
        s = json.loads(r["specs"] or "{}")
        total_storage_gb += float(s.get("capacity_gb", 0) or 0.0)

    cur.execute(
        """
        UPDATE device_profiles
        SET total_ram_mb = ?,
            total_storage_gb = ?
        WHERE asset_id = ?;
        """,
        (total_ram_mb, total_storage_gb, device_id),
    )

def mount_component(
    conn: sqlite3.Connection,
    asset_id: str,
    target_device_id: str,
    slot_or_bus: str,
) -> Dict[str, Any]:
    """
    Mounts a component asset into a target device:
    - Sets parent_asset_id = target_device_id
    - Sets status = 'installed'
    - Clears storage_box_label = NULL
    - Clears assigned_person_id = NULL
    - Documents movement in custody_logs (action = 'installed')
    - Recalculates host device totals
    """
    cur = conn.cursor()

    # Verify target device exists
    cur.execute("SELECT id, name, status FROM assets WHERE id = ?;", (target_device_id,))
    target_device = cur.fetchone()
    if not target_device:
        raise ValueError(f"Target device '{target_device_id}' does not exist.")

    # Verify asset exists
    cur.execute("SELECT * FROM assets WHERE id = ?;", (asset_id,))
    asset = cur.fetchone()
    if not asset:
        raise ValueError(f"Asset '{asset_id}' does not exist.")

    if asset["status"] == "installed" and asset["parent_asset_id"] == target_device_id:
        return {"success": True, "message": "Component is already mounted in this device."}

    old_parent_id = asset["parent_asset_id"]

    # Update asset state
    cur.execute(
        """
        UPDATE assets
        SET parent_asset_id = ?,
            slot_or_bus = ?,
            status = 'installed',
            storage_box_label = NULL,
            assigned_person_id = NULL,
            assigned_at = NULL,
            last_seen_at = datetime('now')
        WHERE id = ?;
        """,
        (target_device_id, slot_or_bus.strip(), asset_id),
    )

    # Document in custody_logs
    log_id = str(uuid.uuid4())
    device_name = target_device["name"] or "Device"
    notes = f"Mounted into '{device_name}' at slot '{slot_or_bus}'"
    cur.execute(
        """
        INSERT INTO custody_logs (id, asset_id, person_id, action, notes, created_at)
        VALUES (?, ?, NULL, 'installed', ?, datetime('now'));
        """,
        (log_id, asset_id, notes),
    )

    # Recalculate target device totals (and old parent if transferred)
    recalculate_device_totals(conn, target_device_id)
    if old_parent_id and old_parent_id != target_device_id:
        recalculate_device_totals(conn, old_parent_id)

    return {
        "success": True,
        "asset_id": asset_id,
        "target_device_id": target_device_id,
        "slot_or_bus": slot_or_bus,
        "message": f"Successfully mounted '{asset['name'] or asset_id}' into '{device_name}'",
    }

def unmount_component(
    conn: sqlite3.Connection,
    asset_id: str,
    storage_box_label: str,
) -> Dict[str, Any]:
    """
    Unmounts a component asset from its host device:
    - Sets parent_asset_id = NULL
    - Sets slot_or_bus = NULL
    - Sets status = 'in_storage'
    - Records storage_box_label
    - Documents movement in custody_logs (action = 'uninstalled')
    - Recalculates former host device totals
    """
    cur = conn.cursor()

    cur.execute("SELECT * FROM assets WHERE id = ?;", (asset_id,))
    asset = cur.fetchone()
    if not asset:
        raise ValueError(f"Asset '{asset_id}' does not exist.")

    old_parent_id = asset["parent_asset_id"]
    old_device_name = "Device"
    if old_parent_id:
        cur.execute("SELECT name FROM assets WHERE id = ?;", (old_parent_id,))
        p_row = cur.fetchone()
        if p_row and p_row["name"]:
            old_device_name = p_row["name"]

    box_label = storage_box_label.strip() if storage_box_label else "Unassigned Box"

    cur.execute(
        """
        UPDATE assets
        SET parent_asset_id = NULL,
            slot_or_bus = NULL,
            status = 'in_storage',
            storage_box_label = ?,
            assigned_person_id = NULL,
            assigned_at = NULL
        WHERE id = ?;
        """,
        (box_label, asset_id),
    )

    # Document in custody_logs
    log_id = str(uuid.uuid4())
    notes = f"Unmounted from '{old_device_name}'. Stored in '{box_label}'"
    cur.execute(
        """
        INSERT INTO custody_logs (id, asset_id, person_id, action, notes, created_at)
        VALUES (?, ?, NULL, 'uninstalled', ?, datetime('now'));
        """,
        (log_id, asset_id, notes),
    )

    if old_parent_id:
        recalculate_device_totals(conn, old_parent_id)

    return {
        "success": True,
        "asset_id": asset_id,
        "storage_box_label": box_label,
        "message": f"Successfully unmounted '{asset['name'] or asset_id}' to '{box_label}'",
    }

def get_drawer_assets(
    conn: sqlite3.Connection,
    category: Optional[str] = None,
    search: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Fetches all spare parts currently in storage ('in_storage')."""
    cur = conn.cursor()
    query = """
        SELECT
            a.id, a.name, a.serial_number, a.slot_or_bus, a.specs, a.status,
            a.storage_box_label, a.notes, a.first_seen_at, a.last_seen_at,
            a.created_at, a.updated_at,
            am.name AS model_name,
            m.name AS manufacturer,
            ct.slug AS component_type_slug,
            ct.label_ar AS component_type_label,
            ct.icon AS component_type_icon
        FROM assets a
        LEFT JOIN asset_models am ON a.asset_model_id = am.id
        LEFT JOIN manufacturers m ON am.manufacturer_id = m.id
        LEFT JOIN component_types ct ON am.component_type_id = ct.id
        WHERE a.status = 'in_storage'
    """
    params: List[Any] = []

    if category and category.upper() != "ALL":
        query += " AND UPPER(ct.slug) = UPPER(?)"
        params.append(category)

    if search:
        search_like = f"%{search.strip()}%"
        query += """ AND (
            a.name LIKE ? OR
            a.serial_number LIKE ? OR
            a.storage_box_label LIKE ? OR
            am.name LIKE ? OR
            m.name LIKE ?
        )"""
        params.extend([search_like] * 5)

    query += " ORDER BY a.updated_at DESC;"

    cur.execute(query, params)
    rows = cur.fetchall()

    result = []
    for r in rows:
        d = dict(r)
        d["specs"] = json.loads(d.get("specs") or "{}")
        result.append(d)
    return result

def get_asset_by_id(conn: sqlite3.Connection, asset_id: str) -> Optional[Dict[str, Any]]:
    """Gets detailed info of a single asset."""
    cur = conn.cursor()
    cur.execute(
        """
        SELECT
            a.id, a.name, a.serial_number, a.slot_or_bus, a.specs, a.status,
            a.storage_box_label, a.notes, a.assigned_at, a.first_seen_at, a.last_seen_at,
            a.created_at, a.updated_at,
            a.parent_asset_id,
            p_asset.name AS parent_asset_name,
            a.assigned_person_id,
            pers.name AS assigned_person_name,
            am.name AS model_name,
            m.name AS manufacturer,
            ct.slug AS component_type_slug,
            ct.label_ar AS component_type_label,
            ct.icon AS component_type_icon
        FROM assets a
        LEFT JOIN assets p_asset ON a.parent_asset_id = p_asset.id
        LEFT JOIN persons pers ON a.assigned_person_id = pers.id
        LEFT JOIN asset_models am ON a.asset_model_id = am.id
        LEFT JOIN manufacturers m ON am.manufacturer_id = m.id
        LEFT JOIN component_types ct ON am.component_type_id = ct.id
        WHERE a.id = ?;
        """,
        (asset_id,),
    )
    row = cur.fetchone()
    if not row:
        return None

    d = dict(row)
    d["specs"] = json.loads(d.get("specs") or "{}")
    return d

def create_manual_asset(conn: sqlite3.Connection, data: Dict[str, Any]) -> Dict[str, Any]:
    """Manually creates an asset (part or device) and catalog entries."""
    cur = conn.cursor()
    asset_id = str(uuid.uuid4())

    slug = data.get("component_type_slug", "OTHER").upper()
    cur.execute("SELECT id, slug, label_ar FROM component_types WHERE UPPER(slug) = UPPER(?);", (slug,))
    type_row = cur.fetchone()
    comp_type_id = type_row["id"] if type_row else "ct-other"

    mfg_name = data.get("manufacturer")
    mfg_id = get_or_create_manufacturer(conn, mfg_name) if mfg_name else None

    model_name = data.get("model_name") or data.get("name") or "Generic Item"
    specs = data.get("specs") or {}
    model_id = get_or_create_asset_model(
        conn,
        manufacturer_id=mfg_id,
        component_type_id=comp_type_id,
        name=model_name,
        default_specs=specs,
    )

    status = data.get("status", "in_storage")
    parent_asset_id = data.get("parent_asset_id") if status == "installed" else None
    storage_box = data.get("storage_box_label") if status == "in_storage" else None
    serial = data.get("serial_number")
    name = data.get("name") or model_name

    cur.execute(
        """
        INSERT INTO assets (
            id, asset_model_id, parent_asset_id, name, serial_number, slot_or_bus,
            specs, status, storage_box_label, notes, first_seen_at, last_seen_at, created_at, updated_at
        ) VALUES (
            ?, ?, ?, ?, ?, ?,
            ?, ?, ?, ?, datetime('now'), datetime('now'), datetime('now'), datetime('now')
        );
        """,
        (
            asset_id,
            model_id,
            parent_asset_id,
            name,
            serial,
            data.get("slot_or_bus"),
            json.dumps(specs),
            status,
            storage_box,
            data.get("notes"),
        ),
    )

    # Document in custody_logs
    log_action = "stored" if status == "in_storage" else ("installed" if status == "installed" else "assigned")
    cur.execute(
        """
        INSERT INTO custody_logs (id, asset_id, person_id, action, notes, created_at)
        VALUES (?, ?, NULL, ?, 'Manually created in inventory', datetime('now'));
        """,
        (str(uuid.uuid4()), asset_id, log_action if log_action in ['stored', 'installed', 'assigned'] else 'stored'),
    )

    if parent_asset_id:
        recalculate_device_totals(conn, parent_asset_id)

    return get_asset_by_id(conn, asset_id) or {"id": asset_id}

def update_asset(conn: sqlite3.Connection, asset_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Updates editable asset fields."""
    cur = conn.cursor()
    cur.execute("SELECT id FROM assets WHERE id = ?;", (asset_id,))
    if not cur.fetchone():
        return None

    fields = []
    values = []

    if "name" in data and data["name"] is not None:
        fields.append("name = ?")
        values.append(data["name"])

    if "serial_number" in data and data["serial_number"] is not None:
        fields.append("serial_number = ?")
        values.append(data["serial_number"])

    if "storage_box_label" in data:
        fields.append("storage_box_label = ?")
        values.append(data["storage_box_label"])

    if "notes" in data and data["notes"] is not None:
        fields.append("notes = ?")
        values.append(data["notes"])

    if "specs" in data and data["specs"] is not None:
        fields.append("specs = ?")
        values.append(json.dumps(data["specs"]))

    if "status" in data and data["status"] is not None:
        fields.append("status = ?")
        values.append(data["status"])

    if not fields:
        return get_asset_by_id(conn, asset_id)

    values.append(asset_id)
    cur.execute(f"UPDATE assets SET {', '.join(fields)}, updated_at = datetime('now') WHERE id = ?;", values)

    return get_asset_by_id(conn, asset_id)

def delete_asset(conn: sqlite3.Connection, asset_id: str) -> bool:
    """Deletes an asset and cascades appropriately."""
    cur = conn.cursor()
    cur.execute("SELECT parent_asset_id FROM assets WHERE id = ?;", (asset_id,))
    row = cur.fetchone()
    if not row:
        return False
    parent_id = row["parent_asset_id"]

    cur.execute("DELETE FROM assets WHERE id = ?;", (asset_id,))
    if parent_id:
        recalculate_device_totals(conn, parent_id)
    return True
