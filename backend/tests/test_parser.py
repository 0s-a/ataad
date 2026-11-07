from pathlib import Path
from backend.app.parsers.cpuz_parser import CPUZParser

def test_cpuz_parser_with_sample():
    sample_file = Path(__file__).parent / "sample_cpuz.txt"
    assert sample_file.exists()

    with open(sample_file, "r", encoding="utf-8") as f:
        text = f.read()

    parser = CPUZParser(text, filename="sample_cpuz.txt")
    result = parser.parse_all()

    # 1. Device Assertions
    dev = result["device"]
    assert dev["manufacturer"] == "Dell Inc."
    assert dev["model"] == "Latitude E6440"
    assert dev["system_serial"] == "5N0GN12"
    assert dev["system_uuid"] == "4c4c4544-004e-3010-8047-b5c04f4e3132"
    assert dev["chassis_subtype"] == "laptop"
    assert dev["motherboard_vendor"] == "Dell Inc."
    assert dev["motherboard_model"] == "0K9GNV"
    assert dev["motherboard_serial"] == "/5N0GN12/CN129634B40029/"
    assert dev["max_ram_capacity_mb"] == 16384
    assert dev["ram_slots_count"] == 2
    assert dev["cpu_model"] == "Intel Core i7 4600M"
    assert dev["cpu_code_name"] == "Haswell"
    assert dev["cpu_socket"] == "Socket 947 rPGA (0x4)"
    assert dev["cpu_cores"] == 2
    assert dev["cpu_threads"] == 4
    assert dev["cpu_has_virtualization"] == 1
    assert dev["total_ram_mb"] == 8192
    assert dev["total_storage_gb"] == 238.5

    # 2. RAM Modules Assertions
    rams = result["ram_modules"]
    assert len(rams) == 2
    assert rams[0]["manufacturer"] == "Samsung"
    assert rams[0]["part_number"] == "M471B5173DB0-YK0"
    assert rams[0]["serial_number"] == "1770EBC2"
    assert rams[0]["specs"]["capacity_mb"] == 4096
    assert rams[0]["specs"]["speed_mhz"] == 1600
    assert rams[0]["specs"]["voltage"] == 1.35

    assert rams[1]["serial_number"] == "1770EC34"
    assert rams[1]["specs"]["capacity_mb"] == 4096

    # 3. Storage Assertions
    drives = result["storage_drives"]
    assert len(drives) == 1
    assert drives[0]["model_name"] == "SUPERSONIC256"
    assert drives[0]["serial_number"] == "VT256SS034636 VC08"
    assert drives[0]["specs"]["capacity_gb"] == 238.5
    assert drives[0]["specs"]["media_type"] == "Fixed, SSD"

    # 4. Display Adapters Assertions
    gpus = result["display_adapters"]
    assert len(gpus) == 2
    assert "Intel(R) HD Graphics 4600" in gpus[0]["model_name"]
    assert gpus[0]["specs"]["is_integrated"] is True
    assert "AMD Radeon" in gpus[1]["model_name"]
    assert gpus[1]["specs"]["is_integrated"] is False

    print("\n✅ All CPU-Z parser assertions passed with 100% precision!")

