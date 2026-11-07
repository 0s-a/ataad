import json
import sqlite3
import uuid
from typing import Any, Dict, List, Optional
from backend.app.services.asset_service import recalculate_device_totals

def assign_custody(
    conn: sqlite3.Connection,
    asset_id: str,
    person_id: str,
    notes: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Hands over an asset (device or spare part) to a person:
    - Verifies person and asset exist.
    - If asset was installed in a parent device, unlinks it.
    - Sets assigned_person_id = person_id and assigned_at = now.
    - Sets status = 'with_person'.
    - Clears storage_box_label = NULL.
    - Documents movement in custody_logs (action = 'assigned').
    """
    cur = conn.cursor()

    cur.execute("SELECT id, name FROM persons WHERE id = ?;", (person_id,))
    person = cur.fetchone()
    if not person:
        raise ValueError(f"Person with ID '{person_id}' does not exist.")

    cur.execute("SELECT * FROM assets WHERE id = ?;", (asset_id,))
    asset = cur.fetchone()
    if not asset:
        raise ValueError(f"Asset with ID '{asset_id}' does not exist.")

    old_parent_id = asset["parent_asset_id"]

    cur.execute(
        """
        UPDATE assets
        SET assigned_person_id = ?,
            assigned_at = datetime('now'),
            status = 'with_person',
            parent_asset_id = NULL,
            slot_or_bus = NULL,
            storage_box_label = NULL,
            updated_at = datetime('now')
        WHERE id = ?;
        """,
        (person_id, asset_id),
    )

    log_id = str(uuid.uuid4())
    log_notes = notes or f"Assigned to {person['name']}"
    cur.execute(
        """
        INSERT INTO custody_logs (id, asset_id, person_id, action, notes, created_at)
        VALUES (?, ?, ?, 'assigned', ?, datetime('now'));
        """,
        (log_id, asset_id, person_id, log_notes),
    )

    if old_parent_id:
        recalculate_device_totals(conn, old_parent_id)

    return {
        "success": True,
        "asset_id": asset_id,
        "person_id": person_id,
        "person_name": person["name"],
        "message": f"Asset successfully assigned to {person['name']}",
    }

def return_custody(
    conn: sqlite3.Connection,
    asset_id: str,
    destination: str = "in_storage",
    storage_box_label: Optional[str] = None,
    notes: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Returns an asset from custody:
    - If destination is 'in_storage': status -> 'in_storage' and box label set.
    - If destination is 'active': status -> 'active' (e.g. host PC returned).
    - Clears assigned_person_id and assigned_at.
    - Documents movement in custody_logs (action = 'returned').
    """
    cur = conn.cursor()

    cur.execute("SELECT * FROM assets WHERE id = ?;", (asset_id,))
    asset = cur.fetchone()
    if not asset:
        raise ValueError(f"Asset with ID '{asset_id}' does not exist.")

    previous_person_id = asset["assigned_person_id"]
    prev_person_name = "Custodian"
    if previous_person_id:
        cur.execute("SELECT name FROM persons WHERE id = ?;", (previous_person_id,))
        p_row = cur.fetchone()
        if p_row:
            prev_person_name = p_row["name"]

    target_status = "in_storage" if destination == "in_storage" else "active"
    box_label = storage_box_label.strip() if (destination == "in_storage" and storage_box_label) else None

    cur.execute(
        """
        UPDATE assets
        SET assigned_person_id = NULL,
            assigned_at = NULL,
            status = ?,
            parent_asset_id = NULL,
            slot_or_bus = NULL,
            storage_box_label = ?,
            updated_at = datetime('now')
        WHERE id = ?;
        """,
        (target_status, box_label, asset_id),
    )

    log_id = str(uuid.uuid4())
    log_notes = notes or f"Returned from {prev_person_name} to {target_status}"
    if box_label:
        log_notes += f" ({box_label})"

    cur.execute(
        """
        INSERT INTO custody_logs (id, asset_id, person_id, action, notes, created_at)
        VALUES (?, ?, ?, 'returned', ?, datetime('now'));
        """,
        (log_id, asset_id, previous_person_id, log_notes),
    )

    return {
        "success": True,
        "asset_id": asset_id,
        "destination": destination,
        "status": target_status,
        "storage_box_label": box_label,
        "message": f"Asset returned successfully to {target_status}",
    }

def get_custody_logs(
    conn: sqlite3.Connection,
    asset_id: Optional[str] = None,
    person_id: Optional[str] = None,
    limit: int = 100,
) -> List[Dict[str, Any]]:
    """Fetches full audit trail of custody and physical movements."""
    cur = conn.cursor()
    query = """
        SELECT
            cl.id, cl.asset_id, cl.person_id, cl.action, cl.notes, cl.created_at,
            a.name AS asset_name,
            a.serial_number,
            p.name AS person_name
        FROM custody_logs cl
        LEFT JOIN assets a ON cl.asset_id = a.id
        LEFT JOIN persons p ON cl.person_id = p.id
        WHERE 1=1
    """
    params: List[Any] = []

    if asset_id:
        query += " AND cl.asset_id = ?"
        params.append(asset_id)

    if person_id:
        query += " AND cl.person_id = ?"
        params.append(person_id)

    query += " ORDER BY cl.created_at DESC, cl.rowid DESC LIMIT ?;"
    params.append(limit)

    cur.execute(query, params)
    return [dict(r) for r in cur.fetchall()]

def get_active_custody_by_person(conn: sqlite3.Connection, person_id: str) -> List[Dict[str, Any]]:
    """Fetches all assets currently in custody of a specific person."""
    cur = conn.cursor()
    cur.execute(
        """
        SELECT
            a.id, a.name, a.serial_number, a.slot_or_bus, a.specs, a.status,
            a.assigned_at, a.notes, a.first_seen_at, a.last_seen_at, a.created_at, a.updated_at,
            am.name AS model_name,
            m.name AS manufacturer,
            ct.slug AS component_type_slug,
            ct.label_ar AS component_type_label,
            ct.icon AS component_type_icon
        FROM assets a
        LEFT JOIN asset_models am ON a.asset_model_id = am.id
        LEFT JOIN manufacturers m ON am.manufacturer_id = m.id
        LEFT JOIN component_types ct ON am.component_type_id = ct.id
        WHERE a.assigned_person_id = ? AND a.status = 'with_person'
        ORDER BY a.assigned_at DESC;
        """,
        (person_id,),
    )
    rows = cur.fetchall()
    result = []
    for r in rows:
        d = dict(r)
        d["specs"] = json.loads(d.get("specs") or "{}")
        result.append(d)
    return result
