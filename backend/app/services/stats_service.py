import sqlite3
from typing import Any, Dict

def get_system_stats(conn: sqlite3.Connection) -> Dict[str, Any]:
    """Calculates high-level inventory metrics for the dashboard."""
    cur = conn.cursor()

    # Total and active devices
    cur.execute(
        """
        SELECT
            COUNT(a.id) AS devices_count,
            SUM(CASE WHEN a.status = 'active' THEN 1 ELSE 0 END) AS active_devices_count
        FROM assets a
        LEFT JOIN asset_models am ON a.asset_model_id = am.id
        LEFT JOIN component_types ct ON am.component_type_id = ct.id
        WHERE ct.slug = 'DEVICE' OR a.id IN (SELECT asset_id FROM device_profiles);
        """
    )
    dev_counts = cur.fetchone()
    devices_count = dev_counts["devices_count"] or 0
    active_devices_count = dev_counts["active_devices_count"] or 0

    # Total RAM and Storage on all host devices
    cur.execute(
        """
        SELECT
            SUM(total_ram_mb) AS sum_ram_mb,
            SUM(total_storage_gb) AS sum_storage_gb
        FROM device_profiles;
        """
    )
    totals = cur.fetchone()
    sum_ram_mb = totals["sum_ram_mb"] or 0
    sum_storage_gb = totals["sum_storage_gb"] or 0.0

    # Drawer spare parts (status = 'in_storage')
    cur.execute("SELECT COUNT(*) AS count FROM assets WHERE status = 'in_storage';")
    drawer_parts_count = cur.fetchone()["count"]

    # Active custody count (status = 'with_person')
    cur.execute("SELECT COUNT(*) AS count FROM assets WHERE status = 'with_person';")
    custody_active_count = cur.fetchone()["count"]

    # Persons count
    cur.execute("SELECT COUNT(*) AS count FROM persons;")
    persons_count = cur.fetchone()["count"]

    return {
        "devices_count": devices_count,
        "active_devices_count": active_devices_count,
        "total_ram_gb": round(sum_ram_mb / 1024, 1),
        "total_storage_tb": round(sum_storage_gb / 1024, 2),
        "drawer_parts_count": drawer_parts_count,
        "custody_active_count": custody_active_count,
        "persons_count": persons_count,
    }
