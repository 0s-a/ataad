import json
import sqlite3
import uuid
from typing import Any, Dict, List, Optional
from backend.app.services.ingest_service import get_or_create_manufacturer, get_or_create_asset_model

def get_devices_list(conn: sqlite3.Connection, search: Optional[str] = None) -> List[Dict[str, Any]]:
    """Fetches list of all computer devices (host systems) with profile summaries."""
    cur = conn.cursor()
    query = """
        SELECT
            a.id, a.name, a.serial_number, a.status, a.storage_box_label, a.created_at,
            am.name AS model_name,
            m.name AS manufacturer,
            dp.chassis_subtype,
            dp.cpu_model,
            dp.total_ram_mb,
            dp.total_storage_gb,
            dp.last_scanned_at,
            a.assigned_person_id,
            p.name AS assigned_person_name
        FROM assets a
        LEFT JOIN device_profiles dp ON a.id = dp.asset_id
        LEFT JOIN asset_models am ON a.asset_model_id = am.id
        LEFT JOIN manufacturers m ON am.manufacturer_id = m.id
        LEFT JOIN component_types ct ON am.component_type_id = ct.id
        LEFT JOIN persons p ON a.assigned_person_id = p.id
        WHERE (ct.slug = 'DEVICE' OR dp.asset_id IS NOT NULL)
    """
    params: List[Any] = []

    if search:
        search_like = f"%{search.strip()}%"
        query += """ AND (
            a.name LIKE ? OR
            a.serial_number LIKE ? OR
            am.name LIKE ? OR
            m.name LIKE ? OR
            dp.cpu_model LIKE ?
        )"""
        params.extend([search_like] * 5)

    query += " ORDER BY a.updated_at DESC;"
    cur.execute(query, params)
    return [dict(r) for r in cur.fetchall()]

def get_device_detail(conn: sqlite3.Connection, device_id: str) -> Optional[Dict[str, Any]]:
    """Fetches complete host device details, full profile, and component assembly tree."""
    cur = conn.cursor()

    # Base asset + model info
    cur.execute(
        """
        SELECT
            a.id, a.name, a.serial_number, a.status, a.storage_box_label, a.created_at,
            am.name AS model_name,
            m.name AS manufacturer,
            dp.chassis_subtype,
            dp.cpu_model,
            dp.total_ram_mb,
            dp.total_storage_gb,
            dp.last_scanned_at,
            a.assigned_person_id,
            p.name AS assigned_person_name
        FROM assets a
        LEFT JOIN device_profiles dp ON a.id = dp.asset_id
        LEFT JOIN asset_models am ON a.asset_model_id = am.id
        LEFT JOIN manufacturers m ON am.manufacturer_id = m.id
        LEFT JOIN persons p ON a.assigned_person_id = p.id
        WHERE a.id = ?;
        """,
        (device_id,),
    )
    device_row = cur.fetchone()
    if not device_row:
        return None

    # Full profile
    cur.execute("SELECT * FROM device_profiles WHERE asset_id = ?;", (device_id,))
    profile_row = cur.fetchone()
    profile = dict(profile_row) if profile_row else None

    # Installed components tree
    cur.execute(
        """
        SELECT
            a.id, a.name, a.serial_number, a.slot_or_bus, a.specs, a.status,
            am.name AS model_name,
            m.name AS manufacturer,
            ct.slug AS component_type_slug,
            ct.label_ar AS component_type_label,
            ct.icon AS component_type_icon
        FROM assets a
        LEFT JOIN asset_models am ON a.asset_model_id = am.id
        LEFT JOIN manufacturers m ON am.manufacturer_id = m.id
        LEFT JOIN component_types ct ON am.component_type_id = ct.id
        WHERE a.parent_asset_id = ? AND a.status = 'installed'
        ORDER BY ct.slug, a.slot_or_bus;
        """,
        (device_id,),
    )
    installed_rows = cur.fetchall()
    installed_components = []
    for r in installed_rows:
        d = dict(r)
        d["specs"] = json.loads(d.get("specs") or "{}")
        installed_components.append(d)

    # Recent drift logs
    cur.execute(
        """
        SELECT id, scan_session_id, change_type, identifier, old_state, new_state, is_acknowledged, detected_at
        FROM hardware_drift_logs
        WHERE asset_id = ?
        ORDER BY detected_at DESC LIMIT 20;
        """,
        (device_id,),
    )
    drift_rows = cur.fetchall()
    recent_drift = []
    for r in drift_rows:
        d = dict(r)
        d["old_state"] = json.loads(d.get("old_state") or "{}")
        d["new_state"] = json.loads(d.get("new_state") or "{}")
        recent_drift.append(d)

    # Scan sessions count
    cur.execute("SELECT COUNT(*) AS count FROM scan_sessions WHERE asset_id = ?;", (device_id,))
    sessions_count = cur.fetchone()["count"]

    return {
        "device": dict(device_row),
        "profile": profile,
        "installed_components": installed_components,
        "recent_drift_logs": recent_drift,
        "scan_sessions_count": sessions_count,
    }

def create_manual_device(conn: sqlite3.Connection, data: Dict[str, Any]) -> Dict[str, Any]:
    """Manually registers a new host device and initializes its profile."""
    cur = conn.cursor()
    asset_id = str(uuid.uuid4())
    mfg_name = data.get("manufacturer") or "Custom"
    model_name = data.get("model_name") or data.get("name") or "PC"

    mfg_id = get_or_create_manufacturer(conn, mfg_name)
    model_id = get_or_create_asset_model(
        conn,
        manufacturer_id=mfg_id,
        component_type_id="ct-device",
        name=model_name,
        default_specs={"chassis_subtype": data.get("chassis_subtype", "desktop_tower")},
    )

    dev_name = data.get("name") or f"{mfg_name} {model_name}"
    cur.execute(
        """
        INSERT INTO assets (
            id, asset_model_id, name, serial_number, status, specs, notes,
            first_seen_at, last_seen_at, created_at, updated_at
        ) VALUES (
            ?, ?, ?, ?, 'active', '{}', ?,
            datetime('now'), datetime('now'), datetime('now'), datetime('now')
        );
        """,
        (asset_id, model_id, dev_name, data.get("serial_number"), data.get("notes")),
    )

    cur.execute(
        """
        INSERT INTO device_profiles (
            asset_id, chassis_subtype, system_serial, cpu_model, last_scanned_at
        ) VALUES (?, ?, ?, ?, datetime('now'));
        """,
        (asset_id, data.get("chassis_subtype", "desktop_tower"), data.get("serial_number"), data.get("cpu_model")),
    )

    # Document in custody_logs
    cur.execute(
        """
        INSERT INTO custody_logs (id, asset_id, person_id, action, notes, created_at)
        VALUES (?, ?, NULL, 'stored', 'Host device created manually', datetime('now'));
        """,
        (str(uuid.uuid4()), asset_id),
    )

    detail = get_device_detail(conn, asset_id)
    return detail or {"id": asset_id}

def update_device(conn: sqlite3.Connection, device_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Updates host device details."""
    cur = conn.cursor()
    cur.execute("SELECT id FROM assets WHERE id = ?;", (device_id,))
    if not cur.fetchone():
        return None

    if data.get("name") or data.get("status") or data.get("notes"):
        fields = []
        vals = []
        if data.get("name"):
            fields.append("name = ?")
            vals.append(data["name"])
        if data.get("status"):
            fields.append("status = ?")
            vals.append(data["status"])
        if data.get("notes"):
            fields.append("notes = ?")
            vals.append(data["notes"])
        vals.append(device_id)
        cur.execute(f"UPDATE assets SET {', '.join(fields)}, updated_at = datetime('now') WHERE id = ?;", vals)

    if data.get("chassis_subtype"):
        cur.execute(
            "UPDATE device_profiles SET chassis_subtype = ? WHERE asset_id = ?;",
            (data["chassis_subtype"], device_id),
        )

    return get_device_detail(conn, device_id)
