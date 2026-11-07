import sqlite3
import uuid
from typing import Any, Dict, List, Optional
from backend.app.services.custody_service import get_active_custody_by_person

def get_persons_list(conn: sqlite3.Connection, search: Optional[str] = None) -> List[Dict[str, Any]]:
    """Lists all persons with the count of assets currently held in custody."""
    cur = conn.cursor()
    query = """
        SELECT
            p.id, p.name, p.phone, p.relationship, p.notes, p.created_at,
            COUNT(a.id) AS active_custody_count
        FROM persons p
        LEFT JOIN assets a ON p.id = a.assigned_person_id AND a.status = 'with_person'
        WHERE 1=1
    """
    params: List[Any] = []

    if search:
        search_like = f"%{search.strip()}%"
        query += " AND (p.name LIKE ? OR p.phone LIKE ? OR p.relationship LIKE ?)"
        params.extend([search_like, search_like, search_like])

    query += " GROUP BY p.id ORDER BY p.name ASC;"
    cur.execute(query, params)
    return [dict(r) for r in cur.fetchall()]

def get_person_detail(conn: sqlite3.Connection, person_id: str) -> Optional[Dict[str, Any]]:
    """Gets person details along with all currently held active assets in custody."""
    cur = conn.cursor()
    cur.execute("SELECT * FROM persons WHERE id = ?;", (person_id,))
    row = cur.fetchone()
    if not row:
        return None

    data = dict(row)
    active_assets = get_active_custody_by_person(conn, person_id)
    data["active_custody_count"] = len(active_assets)
    data["active_assets"] = active_assets
    return data

def create_person(conn: sqlite3.Connection, data: Dict[str, Any]) -> Dict[str, Any]:
    """Creates a new person."""
    cur = conn.cursor()
    person_id = str(uuid.uuid4())
    cur.execute(
        """
        INSERT INTO persons (id, name, phone, relationship, notes, created_at)
        VALUES (?, ?, ?, ?, ?, datetime('now'));
        """,
        (person_id, data["name"].strip(), data.get("phone"), data.get("relationship"), data.get("notes")),
    )
    return get_person_detail(conn, person_id) or {"id": person_id}

def update_person(conn: sqlite3.Connection, person_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Updates person fields."""
    cur = conn.cursor()
    cur.execute("SELECT id FROM persons WHERE id = ?;", (person_id,))
    if not cur.fetchone():
        return None

    fields = []
    vals = []
    if "name" in data and data["name"] is not None:
        fields.append("name = ?")
        vals.append(data["name"].strip())
    if "phone" in data:
        fields.append("phone = ?")
        vals.append(data["phone"])
    if "relationship" in data:
        fields.append("relationship = ?")
        vals.append(data["relationship"])
    if "notes" in data:
        fields.append("notes = ?")
        vals.append(data["notes"])

    if fields:
        vals.append(person_id)
        cur.execute(f"UPDATE persons SET {', '.join(fields)} WHERE id = ?;", vals)

    return get_person_detail(conn, person_id)

def delete_person(conn: sqlite3.Connection, person_id: str) -> bool:
    """Deletes a person if they have no active custody."""
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) AS count FROM assets WHERE assigned_person_id = ? AND status = 'with_person';", (person_id,))
    if cur.fetchone()["count"] > 0:
        raise ValueError("Cannot delete person who currently holds active assets in custody.")

    cur.execute("DELETE FROM persons WHERE id = ?;", (person_id,))
    return cur.rowcount > 0
