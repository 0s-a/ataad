import io
import json
import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from backend.app.core.config import settings
from backend.app.core.database import init_db, get_db
from backend.app.main import app
from backend.app.parsers.cpuz_parser import CPUZParser
from backend.app.services.ingest_service import preview_ingest, ingest_cpuz_data
from backend.app.services.asset_service import (
    mount_component,
    unmount_component,
    get_drawer_assets,
    create_manual_asset,
    get_asset_by_id,
    delete_asset,
)
from backend.app.services.custody_service import (
    assign_custody,
    return_custody,
    get_custody_logs,
    get_active_custody_by_person,
)
from backend.app.services.person_service import (
    create_person,
    get_persons_list,
    get_person_detail,
    delete_person,
)

SAMPLE_CPUZ_PATH = Path(__file__).parent / "sample_cpuz.txt"

@pytest.fixture(scope="function", autouse=True)
def setup_test_db(tmp_path):
    """Configures a temporary SQLite database for each test function."""
    test_db = tmp_path / "test_ataad.db"
    original_db = settings.db_path
    settings.db_path = test_db
    init_db()
    yield test_db
    settings.db_path = original_db

@pytest.fixture
def sample_report_text():
    return SAMPLE_CPUZ_PATH.read_text(encoding="utf-8")

@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c

# ---------------------------------------------------------------------------
# 1. Ingest Service Tests
# ---------------------------------------------------------------------------

def test_ingest_service_initial_scan(sample_report_text):
    """Verifies that an initial CPU-Z report ingestion populates all required catalog and asset records."""
    parser = CPUZParser(sample_report_text, filename="sample_cpuz.txt")
    data = parser.parse_all()

    with get_db() as conn:
        result = ingest_cpuz_data(conn, data, raw_text=sample_report_text, filename="sample_cpuz.txt")
        assert result["is_new_device"] is True
        host_id = result["asset_id"]

        # Check Host Asset
        cur = conn.cursor()
        cur.execute("SELECT * FROM assets WHERE id = ?;", (host_id,))
        host_row = cur.fetchone()
        assert host_row is not None
        assert host_row["status"] == "active"
        assert host_row["serial_number"] == "5N0GN12"

        # Check Device Profile
        cur.execute("SELECT * FROM device_profiles WHERE asset_id = ?;", (host_id,))
        profile_row = cur.fetchone()
        assert profile_row is not None
        assert profile_row["cpu_model"] == "Intel Core i7 4600M"
        assert profile_row["chassis_subtype"] == "laptop"
        assert profile_row["total_ram_mb"] == 8192
        assert profile_row["total_storage_gb"] == 238.5

        # Check Installed Components (RAM, Storage, GPU)
        cur.execute("SELECT * FROM assets WHERE parent_asset_id = ? AND status = 'installed';", (host_id,))
        components = cur.fetchall()
        assert len(components) == 5  # 2 RAMs + 1 Storage + 2 GPUs (Intel + AMD)

        # Check Scan Sessions
        cur.execute("SELECT * FROM scan_sessions WHERE asset_id = ?;", (host_id,))
        session_row = cur.fetchone()
        assert session_row is not None
        assert session_row["file_name"] == "sample_cpuz.txt"

def test_ingest_service_idempotent_rescan(sample_report_text):
    """Verifies that rescanning the identical report updates timestamps without duplicate records or false drift."""
    parser = CPUZParser(sample_report_text, filename="sample_cpuz.txt")
    data = parser.parse_all()

    with get_db() as conn:
        res1 = ingest_cpuz_data(conn, data, raw_text=sample_report_text, filename="sample_cpuz.txt")
        assert res1["is_new_device"] is True

        res2 = ingest_cpuz_data(conn, data, raw_text=sample_report_text, filename="sample_cpuz.txt")
        assert res2["is_new_device"] is False
        assert res2["asset_id"] == res1["asset_id"]
        assert res2["drift_count"] == 0

def test_ingest_hardware_drift_detection(sample_report_text):
    """Verifies PART_SWAPPED and PART_REMOVED drift detection when hardware changes."""
    parser = CPUZParser(sample_report_text, filename="sample_cpuz.txt")
    data = parser.parse_all()

    with get_db() as conn:
        res1 = ingest_cpuz_data(conn, data, raw_text=sample_report_text, filename="sample_cpuz.txt")
        host_id = res1["asset_id"]

        # Modify data: swap DIMM # 1 with a new stick, remove storage drive
        modified_data = json.loads(json.dumps(data))
        # Swap RAM in DIMM # 1
        modified_data["ram_modules"][0]["serial_number"] = "SWAPPED-SN-9999"
        modified_data["ram_modules"][0]["model_name"] = "Kingston 8GB DDR3"
        modified_data["ram_modules"][0]["specs"]["capacity_mb"] = 8192
        # Remove storage drives entirely
        modified_data["storage_drives"] = []

        res2 = ingest_cpuz_data(conn, modified_data, raw_text="modified", filename="scan2.txt")
        assert res2["is_new_device"] is False

        cur = conn.cursor()
        cur.execute("SELECT * FROM hardware_drift_logs WHERE asset_id = ?;", (host_id,))
        drifts = [dict(r) for r in cur.fetchall()]
        change_types = [d["change_type"] for d in drifts]

        assert "PART_SWAPPED" in change_types
        assert "PART_REMOVED" in change_types

def test_preview_ingest_does_not_modify_db(sample_report_text):
    """Verifies that preview_ingest computes match status and forecasts without database mutation."""
    parser = CPUZParser(sample_report_text, filename="sample_cpuz.txt")
    data = parser.parse_all()

    with get_db() as conn:
        preview = preview_ingest(conn, data)
        assert preview["is_existing"] is False
        assert len(preview["ram_modules"]) == 2
        assert len(preview["storage_drives"]) == 1

        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) AS count FROM assets;")
        assert cur.fetchone()["count"] == 0

# ---------------------------------------------------------------------------
# 2. Asset & Mount/Unmount Service Tests
# ---------------------------------------------------------------------------

def test_manual_asset_lifecycle_and_drawer():
    """Verifies manual asset creation, drawer retrieval, and deletion."""
    with get_db() as conn:
        # Create a RAM stick in drawer
        ram = create_manual_asset(
            conn,
            {
                "name": "Corsair Vengeance 16GB",
                "component_type_slug": "RAM",
                "manufacturer": "Corsair",
                "model_name": "CMK16GX4M1A2400C16",
                "serial_number": "CORSAIR-1234",
                "storage_box_label": "Box-RAM-1",
                "status": "in_storage",
                "specs": {"capacity_mb": 16384, "type": "DDR4"},
            },
        )
        assert ram["id"] is not None
        assert ram["status"] == "in_storage"
        assert ram["storage_box_label"] == "Box-RAM-1"

        # Fetch from drawer
        drawer = get_drawer_assets(conn, category="RAM")
        assert any(item["id"] == ram["id"] for item in drawer)

        # Search drawer
        search_res = get_drawer_assets(conn, search="CORSAIR")
        assert len(search_res) == 1

def test_mount_and_unmount_component(sample_report_text):
    """Verifies mounting a drawer component into a device and unmounting it back to drawer."""
    parser = CPUZParser(sample_report_text, filename="sample_cpuz.txt")
    data = parser.parse_all()

    with get_db() as conn:
        res = ingest_cpuz_data(conn, data)
        host_id = res["asset_id"]

        # Create a spare RAM in drawer
        spare_ram = create_manual_asset(
            conn,
            {
                "name": "Crucial 8GB DDR3",
                "component_type_slug": "RAM",
                "manufacturer": "Crucial",
                "model_name": "CT102464BF160B",
                "serial_number": "CRUCIAL-8888",
                "storage_box_label": "Box-1",
                "status": "in_storage",
                "specs": {"capacity_mb": 8192},
            },
        )

        # Mount to device
        mount_res = mount_component(conn, spare_ram["id"], host_id, "DIMM # 3")
        assert mount_res["success"] is True

        updated_asset = get_asset_by_id(conn, spare_ram["id"])
        assert updated_asset["status"] == "installed"
        assert updated_asset["parent_asset_id"] == host_id
        assert updated_asset["slot_or_bus"] == "DIMM # 3"
        assert updated_asset["storage_box_label"] is None

        # Verify custody log recorded
        logs = get_custody_logs(conn, asset_id=spare_ram["id"])
        assert any(l["action"] == "installed" for l in logs)

        # Unmount to drawer
        unmount_res = unmount_component(conn, spare_ram["id"], "Box-Archive-B")
        assert unmount_res["success"] is True

        unmounted_asset = get_asset_by_id(conn, spare_ram["id"])
        assert unmounted_asset["status"] == "in_storage"
        assert unmounted_asset["parent_asset_id"] is None
        assert unmounted_asset["storage_box_label"] == "Box-Archive-B"

        logs_after = get_custody_logs(conn, asset_id=spare_ram["id"])
        assert any(l["action"] == "uninstalled" for l in logs_after)

# ---------------------------------------------------------------------------
# 3. Custody Service Tests
# ---------------------------------------------------------------------------

def test_custody_assignment_and_return():
    """Verifies assigning an asset to a person and returning it to drawer or active."""
    with get_db() as conn:
        person = create_person(
            conn,
            {"name": "أحمد خليل", "phone": "0501234567", "relationship": "زميل عمل"},
        )
        person_id = person["id"]

        spare = create_manual_asset(
            conn,
            {
                "name": "Samsung Portable SSD T7",
                "component_type_slug": "STORAGE",
                "manufacturer": "Samsung",
                "model_name": "T7 1TB",
                "serial_number": "T7-SAM-9000",
                "status": "in_storage",
                "storage_box_label": "Box-External",
            },
        )
        asset_id = spare["id"]

        # Assign custody
        assign_res = assign_custody(conn, asset_id, person_id, notes="عهدة مؤقتة للمشروع")
        assert assign_res["success"] is True

        asset_after_assign = get_asset_by_id(conn, asset_id)
        assert asset_after_assign["status"] == "with_person"
        assert asset_after_assign["assigned_person_id"] == person_id

        # Verify active custody for person
        active_items = get_active_custody_by_person(conn, person_id)
        assert len(active_items) == 1
        assert active_items[0]["id"] == asset_id

        # Return custody to drawer
        return_res = return_custody(conn, asset_id, destination="in_storage", storage_box_label="Box-External", notes="تم الاسترجاع بحالة سليمة")
        assert return_res["success"] is True

        asset_after_return = get_asset_by_id(conn, asset_id)
        assert asset_after_return["status"] == "in_storage"
        assert asset_after_return["assigned_person_id"] is None
        assert asset_after_return["storage_box_label"] == "Box-External"

        # Verify logs
        logs = get_custody_logs(conn, asset_id=asset_id)
        actions = [l["action"] for l in logs]
        assert "assigned" in actions
        assert "returned" in actions

# ---------------------------------------------------------------------------
# 4. REST API Integration Tests (FastAPI TestClient)
# ---------------------------------------------------------------------------

def test_api_root_and_stats(client):
    """Tests health endpoint and real-time dashboard aggregation stats."""
    res = client.get("/")
    assert res.status_code == 200
    assert res.json()["status"] == "online"

    stats_res = client.get("/api/stats")
    assert stats_res.status_code == 200
    stats = stats_res.json()
    assert "devices_count" in stats
    assert "total_ram_gb" in stats
    assert "drawer_parts_count" in stats

def test_api_ingest_endpoints(client, sample_report_text):
    """Tests /api/ingest/preview and /api/ingest/commit with multipart file upload."""
    file_bytes = io.BytesIO(sample_report_text.encode("utf-8"))

    # Preview
    preview_res = client.post(
        "/api/ingest/preview",
        files={"file": ("report.txt", file_bytes, "text/plain")},
    )
    assert preview_res.status_code == 200
    preview_data = preview_res.json()
    assert preview_data["is_existing"] is False
    assert preview_data["device"]["model"] == "Latitude E6440"
    assert len(preview_data["ram_modules"]) == 2

    # Commit
    file_bytes.seek(0)
    commit_res = client.post(
        "/api/ingest/commit",
        files={"file": ("report.txt", file_bytes, "text/plain")},
    )
    assert commit_res.status_code == 200
    commit_data = commit_res.json()
    assert commit_data["is_new_device"] is True
    device_id = commit_data["asset_id"]

    # Verify device exists via API
    dev_get = client.get(f"/api/devices/{device_id}")
    assert dev_get.status_code == 200
    dev_json = dev_get.json()
    assert len(dev_json["installed_components"]) == 5  # 2 RAMs + 1 Storage + 2 GPUs

def test_api_devices_and_assets_crud(client):
    """Tests full CRUD operations on devices and drawer assets."""
    # Create manual device
    dev_payload = {
        "name": "Custom Server Node 1",
        "manufacturer": "Supermicro",
        "model_name": "SYS-5019",
        "serial_number": "SMC-SN-7766",
        "chassis_subtype": "server_rack",
        "cpu_model": "AMD EPYC 7302P",
    }
    dev_res = client.post("/api/devices", json=dev_payload)
    assert dev_res.status_code == 201
    dev_id = dev_res.json()["device"]["id"]

    # List devices
    list_res = client.get("/api/devices?search=Supermicro")
    assert list_res.status_code == 200
    assert len(list_res.json()) >= 1

    # Create part in drawer
    part_payload = {
        "name": "Samsung 32GB ECC RAM",
        "component_type_slug": "RAM",
        "manufacturer": "Samsung",
        "model_name": "M393A4K40BB2-CTD",
        "serial_number": "ECC-RAM-32G",
        "storage_box_label": "Server-Box-1",
        "status": "in_storage",
        "specs": {"capacity_mb": 32768, "type": "DDR4"},
    }
    part_res = client.post("/api/assets", json=part_payload)
    assert part_res.status_code == 201
    part_id = part_res.json()["id"]

    # Drawer parts query
    drawer_res = client.get("/api/assets/drawer?category=RAM")
    assert drawer_res.status_code == 200
    assert any(p["id"] == part_id for p in drawer_res.json())

    # Mount part to device
    mount_res = client.post(
        f"/api/assets/{part_id}/mount",
        json={"target_device_id": dev_id, "slot_or_bus": "DIMM A1"},
    )
    assert mount_res.status_code == 200

    # Verify device installed components
    dev_check = client.get(f"/api/devices/{dev_id}")
    assert any(c["id"] == part_id for c in dev_check.json()["installed_components"])

    # Unmount part back to drawer
    unmount_res = client.post(
        f"/api/assets/{part_id}/unmount",
        json={"storage_box_label": "Server-Box-1"},
    )
    assert unmount_res.status_code == 200

    # Check drawer again
    drawer_res2 = client.get("/api/assets/drawer")
    assert any(p["id"] == part_id for p in drawer_res2.json())

def test_api_persons_and_custody_flow(client):
    """Tests person management, custody assignment, return, and audit logs via API."""
    # 1. Create person
    person_payload = {
        "name": "سارة الشريف",
        "phone": "0559876543",
        "relationship": "صديق",
        "notes": "مهندس شبكات",
    }
    p_res = client.post("/api/persons", json=person_payload)
    assert p_res.status_code == 201
    person_id = p_res.json()["id"]

    # 2. Create asset
    asset_res = client.post(
        "/api/assets",
        json={
            "name": "TP-Link USB Wi-Fi Adapter",
            "component_type_slug": "NETWORK",
            "manufacturer": "TP-Link",
            "model_name": "Archer T3U",
            "status": "in_storage",
            "storage_box_label": "Box-Network",
        },
    )
    asset_id = asset_res.json()["id"]

    # 3. Assign custody
    assign_res = client.post(
        "/api/custody/assign",
        json={"asset_id": asset_id, "person_id": person_id, "notes": "إعارة أسبوع"},
    )
    assert assign_res.status_code == 200
    assert assign_res.json()["success"] is True

    # 4. Check person's active custody
    custody_res = client.get(f"/api/persons/{person_id}/custody")
    assert custody_res.status_code == 200
    assert len(custody_res.json()) == 1

    # Cannot delete person while holding active custody
    del_res = client.delete(f"/api/persons/{person_id}")
    assert del_res.status_code == 400

    # 5. Return custody
    return_res = client.post(
        "/api/custody/return",
        json={"asset_id": asset_id, "destination": "in_storage", "storage_box_label": "Box-Network"},
    )
    assert return_res.status_code == 200

    # Now person has 0 active custody
    custody_res2 = client.get(f"/api/persons/{person_id}/custody")
    assert len(custody_res2.json()) == 0

    # Audit logs
    logs_res = client.get(f"/api/custody/logs?asset_id={asset_id}")
    assert logs_res.status_code == 200
    assert len(logs_res.json()) >= 2
