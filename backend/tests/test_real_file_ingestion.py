import json
import sqlite3
import uuid
from pathlib import Path
import pytest

from backend.app.parsers.cpuz_parser import CPUZParser
from backend.app.services.ingest_service import ingest_cpuz_data
from backend.app.services.asset_service import (
    mount_component,
    unmount_component,
    get_asset_by_id,
    get_drawer_assets,
)
from backend.app.services.custody_service import (
    assign_custody,
    return_custody,
    get_custody_logs,
)

BASE_DIR = Path(__file__).resolve().parent.parent.parent
SCHEMA_FILE = BASE_DIR / "schema.sql"
REAL_FILE = BASE_DIR / "MINWINPC.txt"


@pytest.fixture
def db_conn():
    """Provides a fresh, isolated in-memory SQLite database initialized with schema.sql."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")

    assert SCHEMA_FILE.exists(), f"Schema file not found at {SCHEMA_FILE}"
    schema_sql = SCHEMA_FILE.read_text(encoding="utf-8")
    conn.executescript(schema_sql)

    yield conn
    conn.close()


@pytest.fixture
def parsed_real_data():
    """Reads and parses the real MINWINPC.txt CPU-Z report."""
    assert REAL_FILE.exists(), f"Real scan report not found at {REAL_FILE}"
    raw_text = REAL_FILE.read_text(encoding="utf-8", errors="ignore")
    parser = CPUZParser(raw_text, filename="MINWINPC.txt")
    data = parser.parse_all()
    return raw_text, data


@pytest.fixture
def ingested_system(db_conn, parsed_real_data):
    """Ingests the parsed real data into the test database."""
    raw_text, parsed_data = parsed_real_data
    ingest_result = ingest_cpuz_data(
        db_conn,
        parsed_data,
        raw_text=raw_text,
        filename="MINWINPC.txt",
    )
    return {
        "conn": db_conn,
        "result": ingest_result,
        "host_asset_id": ingest_result["asset_id"],
        "session_id": ingest_result["session_id"],
        "raw_text": raw_text,
        "parsed_data": parsed_data,
    }


# ============================================================================
# 1. Real File Ingestion Tests (MINWINPC.txt)
# ============================================================================

class TestRealFileIngestion:
    """Validates accurate ingestion and database population from MINWINPC.txt."""

    def test_manufacturer_created(self, ingested_system):
        conn = ingested_system["conn"]
        cur = conn.cursor()
        cur.execute("SELECT * FROM manufacturers WHERE name = ?;", ("Dell Inc.",))
        mfg = cur.fetchone()

        assert mfg is not None, "Manufacturer 'Dell Inc.' was not found in manufacturers table"
        assert mfg["name"] == "Dell Inc."

    def test_asset_model_created(self, ingested_system):
        conn = ingested_system["conn"]
        cur = conn.cursor()
        cur.execute(
            """
            SELECT am.*, m.name AS mfg_name, ct.slug AS comp_slug
            FROM asset_models am
            JOIN manufacturers m ON am.manufacturer_id = m.id
            JOIN component_types ct ON am.component_type_id = ct.id
            WHERE am.name = ?;
            """,
            ("Latitude E6440",),
        )
        model = cur.fetchone()

        assert model is not None, "Asset model 'Latitude E6440' was not found in asset_models"
        assert model["mfg_name"] == "Dell Inc."
        assert model["comp_slug"] == "DEVICE"
        assert model["model_number"] == "5N0GN12"

    def test_host_device_and_profile_populated(self, ingested_system):
        conn = ingested_system["conn"]
        host_id = ingested_system["host_asset_id"]
        cur = conn.cursor()

        # Check in assets table
        cur.execute("SELECT * FROM assets WHERE id = ?;", (host_id,))
        asset = cur.fetchone()
        assert asset is not None, f"Host asset with id '{host_id}' not found in assets"
        assert asset["status"] == "active"
        assert asset["parent_asset_id"] is None
        assert asset["assigned_person_id"] is None
        assert asset["serial_number"] == "5N0GN12"
        assert "Latitude E6440" in asset["name"]

        # Check in device_profiles table
        cur.execute("SELECT * FROM device_profiles WHERE asset_id = ?;", (host_id,))
        profile = cur.fetchone()
        assert profile is not None, "Device profile not found for host asset"

        # Motherboard & Chassis assertions
        assert profile["chassis_subtype"] == "laptop"
        assert profile["system_serial"] == "5N0GN12"
        assert profile["system_uuid"] == "4c4c4544-004e-3010-8047-b5c04f4e3132"
        assert profile["motherboard_vendor"] == "Dell Inc."
        assert profile["motherboard_model"] == "0K9GNV"
        assert profile["motherboard_serial"] == "/5N0GN12/CN129634B40029/"
        assert profile["bios_version"] == "A18"
        assert profile["bios_date"] == "05/19/2017"

        # CPU architecture assertions
        assert profile["cpu_model"] == "Intel Core i7 4600M"
        assert profile["cpu_code_name"] == "Haswell"
        assert profile["cpu_socket"] == "Socket 947 rPGA (0x4)"
        assert profile["cpu_cores"] == 2
        assert profile["cpu_threads"] == 4
        assert profile["cpu_l3_cache_kb"] == 4096
        assert profile["cpu_tdp_watts"] == 37

        # RAM and Storage capacity assertions
        assert profile["ram_slots_count"] == 2
        assert profile["max_ram_capacity_mb"] == 16384
        assert profile["total_ram_mb"] == 8192
        assert profile["total_storage_gb"] == 238.5

        # OS information
        assert "Windows 11" in profile["os_name"]
        assert profile["os_build"] == "22621"

    def test_samsung_ram_modules_installed(self, ingested_system):
        conn = ingested_system["conn"]
        host_id = ingested_system["host_asset_id"]
        cur = conn.cursor()

        cur.execute(
            """
            SELECT a.*, am.name AS model_name, m.name AS mfg_name
            FROM assets a
            JOIN asset_models am ON a.asset_model_id = am.id
            JOIN manufacturers m ON am.manufacturer_id = m.id
            WHERE a.parent_asset_id = ? AND a.status = 'installed' AND am.component_type_id = 'ct-ram'
            ORDER BY a.slot_or_bus;
            """,
            (host_id,),
        )
        rams = [dict(r) for r in cur.fetchall()]

        assert len(rams) == 2, f"Expected 2 installed RAM modules, found {len(rams)}"

        # Verify common manufacturer
        for ram in rams:
            assert ram["mfg_name"] == "Samsung"
            assert ram["parent_asset_id"] == host_id
            assert ram["status"] == "installed"
            specs = json.loads(ram["specs"] or "{}")
            assert specs.get("capacity_mb") == 4096
            assert specs.get("speed_mhz") == 1600
            assert specs.get("voltage") == 1.35
            assert specs.get("type") == "DDR3L"
            assert specs.get("module_format") == "SO-DIMM"

        # Verify slots and serials
        slots = [r["slot_or_bus"] for r in rams]
        serials = [r["serial_number"] for r in rams]
        assert "DIMM 1" in slots
        assert "DIMM 2" in slots
        assert "1770EBC2" in serials
        assert "1770EC34" in serials

    def test_ssd_storage_installed(self, ingested_system):
        conn = ingested_system["conn"]
        host_id = ingested_system["host_asset_id"]
        cur = conn.cursor()

        cur.execute(
            """
            SELECT a.*, am.name AS model_name, ct.slug AS comp_slug
            FROM assets a
            JOIN asset_models am ON a.asset_model_id = am.id
            JOIN component_types ct ON am.component_type_id = ct.id
            WHERE a.parent_asset_id = ? AND a.status = 'installed' AND ct.slug = 'STORAGE';
            """,
            (host_id,),
        )
        drives = [dict(r) for r in cur.fetchall()]

        assert len(drives) == 1, f"Expected 1 installed storage drive, found {len(drives)}"
        drive = drives[0]
        assert drive["parent_asset_id"] == host_id
        assert drive["status"] == "installed"
        assert drive["serial_number"] == "VT256SS034636 VC08"
        assert "SUPERSONIC256" in drive["name"]

        specs = json.loads(drive["specs"] or "{}")
        assert specs.get("capacity_gb") == 238.5
        assert "SSD" in specs.get("media_type", "")

    def test_scan_session_recorded(self, ingested_system):
        conn = ingested_system["conn"]
        host_id = ingested_system["host_asset_id"]
        session_id = ingested_system["session_id"]
        cur = conn.cursor()

        cur.execute("SELECT * FROM scan_sessions WHERE id = ?;", (session_id,))
        session = cur.fetchone()

        assert session is not None, f"Scan session '{session_id}' not found in scan_sessions"
        assert session["asset_id"] == host_id
        assert session["source"] == "CPU-Z"
        assert session["file_name"] == "MINWINPC.txt"
        assert "CPU-Z TXT Report" in session["raw_text"]
        assert "Latitude E6440" in session["raw_text"]

    def test_idempotent_reingestion_no_duplicates(self, ingested_system):
        """Re-ingesting the same file updates last_seen_at without creating duplicate assets."""
        conn = ingested_system["conn"]
        host_id = ingested_system["host_asset_id"]
        raw_text = ingested_system["raw_text"]
        parsed_data = ingested_system["parsed_data"]

        # Run ingestion a second time
        second_result = ingest_cpuz_data(
            conn,
            parsed_data,
            raw_text=raw_text,
            filename="MINWINPC.txt",
        )

        assert second_result["is_new_device"] is False
        assert second_result["asset_id"] == host_id
        assert second_result["drift_count"] == 0

        # Assert no duplicate host assets
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) AS cnt FROM assets WHERE serial_number = '5N0GN12';")
        assert cur.fetchone()["cnt"] == 1

        # Assert exactly 2 RAM modules total in DB
        cur.execute("SELECT COUNT(*) AS cnt FROM assets WHERE serial_number IN ('1770EBC2', '1770EC34');")
        assert cur.fetchone()["cnt"] == 2

        # Assert 2 scan sessions exist now
        cur.execute("SELECT COUNT(*) AS cnt FROM scan_sessions WHERE asset_id = ?;", (host_id,))
        assert cur.fetchone()["cnt"] == 2


# ============================================================================
# 2. Lifecycle Workflow Tests
# ============================================================================

class TestLifecycleWorkflows:
    """Tests physical component movements, drawer storage, and custody transitions."""

    def test_unmount_ram_to_drawer_storage(self, ingested_system):
        """
        Scenario:
        1. An engineer removes one RAM stick (1770EBC2) from the laptop and stores it in drawer 'درج الرامات 1'.
        2. parent_asset_id is cleared (NULL).
        3. status transitions to 'in_storage'.
        4. storage_box_label is recorded.
        5. Action 'uninstalled' is logged in custody_logs.
        6. Host device total_ram_mb is recalculated from 8192 to 4096.
        """
        conn = ingested_system["conn"]
        host_id = ingested_system["host_asset_id"]
        cur = conn.cursor()

        cur.execute("SELECT id, name FROM assets WHERE serial_number = ?;", ("1770EBC2",))
        ram = cur.fetchone()
        assert ram is not None
        ram_id = ram["id"]

        box_label = "درج الرامات 1"
        res = unmount_component(conn, ram_id, storage_box_label=box_label)
        assert res["success"] is True
        assert res["storage_box_label"] == box_label

        # Verify asset state
        cur.execute("SELECT * FROM assets WHERE id = ?;", (ram_id,))
        updated_ram = cur.fetchone()
        assert updated_ram["parent_asset_id"] is None
        assert updated_ram["slot_or_bus"] is None
        assert updated_ram["status"] == "in_storage"
        assert updated_ram["storage_box_label"] == box_label
        assert updated_ram["assigned_person_id"] is None

        # Verify custody audit log
        cur.execute(
            """
            SELECT * FROM custody_logs
            WHERE asset_id = ? AND action = 'uninstalled'
            ORDER BY created_at DESC;
            """,
            (ram_id,),
        )
        log = cur.fetchone()
        assert log is not None, "Custody log with action 'uninstalled' was not created"
        assert box_label in log["notes"]
        assert log["person_id"] is None

        # Verify host device RAM calculation decreased
        cur.execute("SELECT total_ram_mb FROM device_profiles WHERE asset_id = ?;", (host_id,))
        dp = cur.fetchone()
        assert dp["total_ram_mb"] == 4096, f"Expected total_ram_mb to be 4096, got {dp['total_ram_mb']}"

        # Verify drawer query returns the unmounted RAM
        drawer_items = get_drawer_assets(conn, category="RAM")
        drawer_ids = [item["id"] for item in drawer_items]
        assert ram_id in drawer_ids

    def test_mount_ram_from_drawer_to_device(self, ingested_system):
        """
        Scenario:
        1. A spare RAM module is taken from drawer and installed into laptop at slot 'DIMM 1'.
        2. parent_asset_id is set to host_id.
        3. status transitions to 'installed'.
        4. storage_box_label is cleared to NULL.
        5. Action 'installed' is logged in custody_logs.
        6. Host device total_ram_mb is updated accordingly.
        """
        conn = ingested_system["conn"]
        host_id = ingested_system["host_asset_id"]
        cur = conn.cursor()

        # First unmount RAM 1770EBC2 to storage
        cur.execute("SELECT id FROM assets WHERE serial_number = ?;", ("1770EBC2",))
        ram_id = cur.fetchone()["id"]
        unmount_component(conn, ram_id, storage_box_label="درج الفحص")

        # Now mount it back into the laptop at slot 'DIMM 1'
        res = mount_component(conn, ram_id, target_device_id=host_id, slot_or_bus="DIMM 1")
        assert res["success"] is True
        assert res["slot_or_bus"] == "DIMM 1"

        # Verify asset state
        cur.execute("SELECT * FROM assets WHERE id = ?;", (ram_id,))
        remounted_ram = cur.fetchone()
        assert remounted_ram["parent_asset_id"] == host_id
        assert remounted_ram["slot_or_bus"] == "DIMM 1"
        assert remounted_ram["status"] == "installed"
        assert remounted_ram["storage_box_label"] is None
        assert remounted_ram["assigned_person_id"] is None

        # Verify custody audit log
        cur.execute(
            """
            SELECT * FROM custody_logs
            WHERE asset_id = ? AND action = 'installed'
            ORDER BY created_at DESC;
            """,
            (ram_id,),
        )
        log = cur.fetchone()
        assert log is not None, "Custody log with action 'installed' was not created"
        assert "DIMM 1" in log["notes"]

        # Verify host device RAM calculation restored to 8192 MB
        cur.execute("SELECT total_ram_mb FROM device_profiles WHERE asset_id = ?;", (host_id,))
        assert cur.fetchone()["total_ram_mb"] == 8192

    def test_assign_device_custody_to_person(self, ingested_system):
        """
        Scenario:
        1. Create a person 'طارق الفهد'.
        2. Assign host device as custody to this person.
        3. Verify status becomes 'with_person' and assigned_person_id is set.
        4. Verify 'assigned' action logged in custody_logs.
        """
        conn = ingested_system["conn"]
        host_id = ingested_system["host_asset_id"]
        cur = conn.cursor()

        person_id = str(uuid.uuid4())
        cur.execute(
            "INSERT INTO persons (id, name, phone, relationship) VALUES (?, ?, ?, ?);",
            (person_id, "طارق الفهد", "0559988776", "موظف تقنية معلومات"),
        )

        res = assign_custody(
            conn,
            asset_id=host_id,
            person_id=person_id,
            notes="تسليم لابتوب ديل لإجراء مهام الدعم الفني",
        )
        assert res["success"] is True
        assert res["person_name"] == "طارق الفهد"

        # Verify asset state
        cur.execute("SELECT * FROM assets WHERE id = ?;", (host_id,))
        assigned_asset = cur.fetchone()
        assert assigned_asset["status"] == "with_person"
        assert assigned_asset["assigned_person_id"] == person_id
        assert assigned_asset["assigned_at"] is not None
        assert assigned_asset["parent_asset_id"] is None

        # Verify custody audit trail
        logs = get_custody_logs(conn, asset_id=host_id)
        assert len(logs) > 0
        latest_log = logs[0]
        assert latest_log["action"] == "assigned"
        assert latest_log["person_id"] == person_id
        assert "تسليم لابتوب ديل" in latest_log["notes"]

    def test_return_device_custody(self, ingested_system):
        """
        Scenario:
        1. Device is assigned to person.
        2. Custodian returns the device to active inventory ('active').
        3. assigned_person_id is cleared (NULL).
        4. Action 'returned' is logged in custody_logs.
        """
        conn = ingested_system["conn"]
        host_id = ingested_system["host_asset_id"]
        cur = conn.cursor()

        # Setup person and assign first
        person_id = str(uuid.uuid4())
        cur.execute("INSERT INTO persons (id, name) VALUES (?, ?);", (person_id, "سارة العتيبي"))
        assign_custody(conn, host_id, person_id, "عهدة مشروع مؤقت")

        # Return custody
        res = return_custody(
            conn,
            asset_id=host_id,
            destination="active",
            notes="تم استلام الجهاز سليم مع الشاحن",
        )
        assert res["success"] is True
        assert res["status"] == "active"

        # Verify asset state
        cur.execute("SELECT * FROM assets WHERE id = ?;", (host_id,))
        returned_asset = cur.fetchone()
        assert returned_asset["status"] == "active"
        assert returned_asset["assigned_person_id"] is None
        assert returned_asset["assigned_at"] is None

        # Verify audit trail
        logs = get_custody_logs(conn, asset_id=host_id)
        latest_log = logs[0]
        assert latest_log["action"] == "returned"
        assert latest_log["person_id"] == person_id
        assert "تم استلام الجهاز سليم" in latest_log["notes"]


# ============================================================================
# 3. Integrity Constraints Tests (Database-Level CHECK Constraints)
# ============================================================================

class TestIntegrityConstraints:
    """Verifies that SQLite CHECK and FOREIGN KEY constraints strictly protect data integrity."""

    def test_installed_status_without_parent_asset_id_fails(self, db_conn):
        """CHECK constraint: status='installed' MUST have parent_asset_id IS NOT NULL."""
        cur = db_conn.cursor()
        asset_id = str(uuid.uuid4())

        with pytest.raises(sqlite3.IntegrityError, match="CHECK constraint failed"):
            cur.execute(
                """
                INSERT INTO assets (id, name, status, parent_asset_id, assigned_person_id)
                VALUES (?, 'Orphan Installed Part', 'installed', NULL, NULL);
                """,
                (asset_id,),
            )

    def test_with_person_status_without_assigned_person_id_fails(self, db_conn):
        """CHECK constraint: status='with_person' MUST have assigned_person_id IS NOT NULL."""
        cur = db_conn.cursor()
        asset_id = str(uuid.uuid4())

        with pytest.raises(sqlite3.IntegrityError, match="CHECK constraint failed"):
            cur.execute(
                """
                INSERT INTO assets (id, name, status, parent_asset_id, assigned_person_id)
                VALUES (?, 'Ghost Custody Asset', 'with_person', NULL, NULL);
                """,
                (asset_id,),
            )

    def test_in_storage_status_with_parent_asset_id_fails(self, db_conn):
        """CHECK constraint: status='in_storage' MUST have parent_asset_id IS NULL."""
        cur = db_conn.cursor()
        host_id = str(uuid.uuid4())
        part_id = str(uuid.uuid4())

        # Create valid host device
        cur.execute("INSERT INTO assets (id, name, status) VALUES (?, 'Host PC', 'active');", (host_id,))

        with pytest.raises(sqlite3.IntegrityError, match="CHECK constraint failed"):
            cur.execute(
                """
                INSERT INTO assets (id, name, status, parent_asset_id, assigned_person_id)
                VALUES (?, 'Storage part with host', 'in_storage', ?, NULL);
                """,
                (part_id, host_id),
            )

    def test_in_storage_status_with_person_id_fails(self, db_conn):
        """CHECK constraint: status='in_storage' MUST have assigned_person_id IS NULL."""
        cur = db_conn.cursor()
        person_id = str(uuid.uuid4())
        part_id = str(uuid.uuid4())

        # Create valid person
        cur.execute("INSERT INTO persons (id, name) VALUES (?, 'خالد');", (person_id,))

        with pytest.raises(sqlite3.IntegrityError, match="CHECK constraint failed"):
            cur.execute(
                """
                INSERT INTO assets (id, name, status, parent_asset_id, assigned_person_id)
                VALUES (?, 'Storage part with person', 'in_storage', NULL, ?);
                """,
                (part_id, person_id),
            )

    def test_installed_status_with_person_id_fails(self, db_conn):
        """CHECK constraint: status='installed' CANNOT simultaneously be assigned to a person."""
        cur = db_conn.cursor()
        host_id = str(uuid.uuid4())
        person_id = str(uuid.uuid4())
        part_id = str(uuid.uuid4())

        cur.execute("INSERT INTO assets (id, name, status) VALUES (?, 'Host PC', 'active');", (host_id,))
        cur.execute("INSERT INTO persons (id, name) VALUES (?, 'خالد');", (person_id,))

        with pytest.raises(sqlite3.IntegrityError, match="CHECK constraint failed"):
            cur.execute(
                """
                INSERT INTO assets (id, name, status, parent_asset_id, assigned_person_id)
                VALUES (?, 'Conflicted Installed Part', 'installed', ?, ?);
                """,
                (part_id, host_id, person_id),
            )

    def test_with_person_status_with_parent_asset_id_fails(self, db_conn):
        """CHECK constraint: status='with_person' CANNOT have parent_asset_id (must be unmounted)."""
        cur = db_conn.cursor()
        host_id = str(uuid.uuid4())
        person_id = str(uuid.uuid4())
        part_id = str(uuid.uuid4())

        cur.execute("INSERT INTO assets (id, name, status) VALUES (?, 'Host PC', 'active');", (host_id,))
        cur.execute("INSERT INTO persons (id, name) VALUES (?, 'خالد');", (person_id,))

        with pytest.raises(sqlite3.IntegrityError, match="CHECK constraint failed"):
            cur.execute(
                """
                INSERT INTO assets (id, name, status, parent_asset_id, assigned_person_id)
                VALUES (?, 'Conflicted Custody Part', 'with_person', ?, ?);
                """,
                (part_id, host_id, person_id),
            )

    def test_invalid_status_enum_rejected(self, db_conn):
        """CHECK constraint: status must be one of allowed enum values."""
        cur = db_conn.cursor()
        asset_id = str(uuid.uuid4())

        with pytest.raises(sqlite3.IntegrityError, match="CHECK constraint failed"):
            cur.execute(
                """
                INSERT INTO assets (id, name, status)
                VALUES (?, 'Invalid Status Item', 'floating_in_space');
                """,
                (asset_id,),
            )

    def test_foreign_key_violation_rejected(self, db_conn):
        """PRAGMA foreign_keys: inserting custody log for non-existent asset fails."""
        cur = db_conn.cursor()
        log_id = str(uuid.uuid4())
        non_existent_asset_id = str(uuid.uuid4())

        with pytest.raises(sqlite3.IntegrityError, match="FOREIGN KEY constraint failed"):
            cur.execute(
                """
                INSERT INTO custody_logs (id, asset_id, action, notes)
                VALUES (?, ?, 'installed', 'Test ghost log');
                """,
                (log_id, non_existent_asset_id),
            )
