import re
from typing import Any, Dict, List, Optional
from backend.app.parsers.cpuz_cleaners import (
    clean_text,
    clean_oem_string,
    clean_uuid,
    clean_manufacturer,
    extract_number,
    normalize_chassis_type,
)

class CPUZParser:
    """Robust parser for CPU-Z text export reports (.txt), tested on real-world outputs."""

    def __init__(self, raw_text: str, filename: Optional[str] = None):
        self.raw_text = raw_text
        self.filename = filename or "cpuz_report.txt"
        self.sections: Dict[str, str] = {}
        self._split_into_sections()

    def _split_into_sections(self) -> None:
        """Splits the raw CPU-Z report into logical sections based on horizontal divider lines."""
        lines = self.raw_text.splitlines()
        current_section = "Header"
        section_lines: Dict[str, List[str]] = {current_section: []}

        i = 0
        while i < len(lines):
            line = lines[i].rstrip()
            if (
                i + 1 < len(lines)
                and lines[i + 1].strip().startswith("-----")
                and len(lines[i + 1].strip()) >= 10
            ):
                candidate_title = line.strip()
                if candidate_title:
                    current_section = candidate_title
                    if current_section not in section_lines:
                        section_lines[current_section] = []
                    i += 2
                    continue
            section_lines[current_section].append(line)
            i += 1

        self.sections = {sec.strip(): "\n".join(lns) for sec, lns in section_lines.items()}

        # Split composite sections like "DMI" into their sub-blocks
        if "DMI" in self.sections:
            dmi_text = self.sections["DMI"]
            dmi_blocks = re.split(r"\n(?=DMI\s+[A-Za-z0-9#_ ]+)", "\n" + dmi_text)
            for block in dmi_blocks:
                block_lines = block.strip().splitlines()
                if block_lines:
                    header = block_lines[0].strip()
                    content = "\n".join(block_lines[1:])
                    self.sections[header] = content
                    if "System Information" in header or "System Info" in header:
                        self.sections["DMI System Info"] = content

    def _get_section_matching(self, *candidates: str) -> str:
        """Returns the first matching section text based on candidates."""
        for c in candidates:
            for k, v in self.sections.items():
                if k.lower() == c.lower() or k.lower().startswith(c.lower()):
                    return v
        return ""

    def _parse_key_values(self, text: str) -> Dict[str, str]:
        """Extracts key-value pairs separated by tabs or >=2 spaces."""
        kv = {}
        for line in text.splitlines():
            line = line.strip()
            if not line or line.startswith("---"):
                continue
            parts = re.split(r"\t+|\s{2,}", line, maxsplit=1)
            if len(parts) == 2:
                key, val = parts[0].strip(), parts[1].strip()
                if key:
                    kv[key] = val
                    kv[key.lower()] = val
        return kv

    def parse_device_info(self) -> Dict[str, Any]:
        """Extracts host device, motherboard, bios, and processor baseline metadata."""
        dmi_sys = self._parse_key_values(self._get_section_matching("DMI System Info", "DMI System Information"))
        dmi_board = self._parse_key_values(self._get_section_matching("DMI Baseboard"))
        dmi_bios = self._parse_key_values(self._get_section_matching("DMI BIOS", "BIOS"))
        dmi_chassis = self._parse_key_values(self._get_section_matching("DMI System Enclosure"))
        dmi_mem_array = self._parse_key_values(self._get_section_matching("DMI Physical Memory Array"))
        software = self._parse_key_values(self._get_section_matching("Software"))
        chipset_sec = self._parse_key_values(self._get_section_matching("Chipset"))

        proc_sec = self._get_section_matching("Processors Information", "Processors")
        proc_kv = self._parse_key_values(proc_sec)

        manufacturer = clean_manufacturer(dmi_sys.get("manufacturer")) or "Generic OEM"
        model = clean_oem_string(dmi_sys.get("product")) or "Custom PC / System"
        system_serial = clean_oem_string(dmi_sys.get("serial"))
        system_uuid = clean_uuid(dmi_sys.get("uuid"))
        chassis_subtype = normalize_chassis_type(dmi_chassis.get("chassis type"))

        mb_vendor = clean_manufacturer(dmi_board.get("vendor"))
        mb_model = clean_oem_string(dmi_board.get("model"))
        mb_serial = clean_oem_string(dmi_board.get("serial"))
        chipset = clean_text(chipset_sec.get("northbridge") or chipset_sec.get("southbridge"))

        bios_version = clean_text(dmi_bios.get("version"))
        bios_date = clean_text(dmi_bios.get("date"))

        max_ram_raw = dmi_mem_array.get("max capacity")
        max_ram_mb = None
        if max_ram_raw:
            num = extract_number(max_ram_raw)
            if num:
                max_ram_mb = int(num * 1024) if "gb" in max_ram_raw.lower() else int(num)

        ram_slots_raw = dmi_mem_array.get("number of devices") or dmi_mem_array.get("max# of devices")
        ram_slots_count = int(extract_number(ram_slots_raw)) if ram_slots_raw else 2

        cpu_name = clean_text(proc_kv.get("name")) or "Unknown Processor"
        cpu_code_name = clean_text(proc_kv.get("codename") or proc_kv.get("code name"))
        cpu_spec = clean_text(proc_kv.get("specification")) or cpu_name
        cpu_socket = clean_text(proc_kv.get("package (platform id)") or proc_kv.get("package"))

        tdp_raw = proc_kv.get("tdp limit") or proc_kv.get("tdp") or proc_kv.get("max tdp")
        cpu_tdp = int(extract_number(tdp_raw)) if tdp_raw else None

        l3_raw = proc_kv.get("l3 cache") or proc_kv.get("l3 data cache")
        cpu_l3_kb = None
        if l3_raw:
            l3_num = extract_number(l3_raw)
            if l3_num:
                cpu_l3_kb = int(l3_num * 1024) if "mbyte" in l3_raw.lower() or "mb" in l3_raw.lower() else int(l3_num)

        clock_raw = proc_kv.get("core speed") or proc_kv.get("base frequency")
        base_clock = int(extract_number(clock_raw)) if clock_raw else None

        num_threads = int(extract_number(proc_kv.get("number of threads")) or 1)
        num_cores_raw = proc_kv.get("number of cores")
        if num_cores_raw:
            num_cores = int(extract_number(num_cores_raw))
        else:
            apic_matches = re.findall(r"Core\s+(\d+)|APIC ID\s+(\d+)", proc_sec)
            num_cores = len(set(apic_matches)) if apic_matches else max(1, int(num_threads / 2))

        instructions = proc_kv.get("instructions", "")
        has_virt = 1 if any(v in instructions for v in ["VT-x", "AMD-V"]) else 0

        os_name = clean_text(software.get("windows version") or software.get("os version"))
        os_build = None
        if os_name and "build" in os_name.lower():
            build_match = re.search(r"build\s+(\d+)", os_name, re.I)
            if build_match:
                os_build = build_match.group(1)

        return {
            "manufacturer": manufacturer,
            "model": model,
            "system_serial": system_serial,
            "system_uuid": system_uuid,
            "chassis_subtype": chassis_subtype,
            "motherboard_vendor": mb_vendor,
            "motherboard_model": mb_model,
            "motherboard_serial": mb_serial,
            "chipset": chipset,
            "bios_version": bios_version,
            "bios_date": bios_date,
            "max_ram_capacity_mb": max_ram_mb,
            "ram_slots_count": ram_slots_count,
            "cpu_model": cpu_name,
            "cpu_code_name": cpu_code_name,
            "cpu_socket": cpu_socket,
            "cpu_cores": num_cores,
            "cpu_threads": num_threads,
            "cpu_base_clock_mhz": base_clock,
            "cpu_l3_cache_kb": cpu_l3_kb,
            "cpu_tdp_watts": cpu_tdp,
            "cpu_has_virtualization": has_virt,
            "cpu_summary": cpu_spec,
            "os_name": os_name,
            "os_build": os_build,
        }

    def parse_ram_modules(self) -> List[Dict[str, Any]]:
        """Parses individual RAM sticks from the Memory SPD section."""
        modules = []
        spd_text = self._get_section_matching("Memory SPD")
        if not spd_text:
            return modules

        dimm_blocks = re.split(r"(DIMM\s*#?\s*\t*\d+)", spd_text)

        for i in range(1, len(dimm_blocks), 2):
            raw_slot = dimm_blocks[i].strip()
            slot_name = re.sub(r"[#\t\s]+", " ", raw_slot).strip()
            if not slot_name.startswith("DIMM"):
                slot_name = f"DIMM {slot_name}"

            block_content = dimm_blocks[i + 1] if i + 1 < len(dimm_blocks) else ""
            kv = self._parse_key_values(block_content)

            size_raw = kv.get("size")
            capacity_mb = int(extract_number(size_raw)) if size_raw else None
            if not capacity_mb or capacity_mb <= 0:
                continue

            mfg_raw = (
                kv.get("module manufacturer(id)")
                or kv.get("module manufacturer (id)")
                or kv.get("manufacturer (id)")
                or kv.get("sdram manufacturer (id)")
                or kv.get("manufacturer")
            )
            mfg = clean_manufacturer(mfg_raw) or "Generic"
            mem_type = clean_text(kv.get("memory type")) or "DDR"
            mod_format = clean_text(kv.get("module format")) or "SO-DIMM"
            part_number = clean_oem_string(kv.get("part number"))
            serial_number = clean_oem_string(kv.get("serial number"))

            speed_raw = kv.get("max bandwidth", "")
            speed_match = re.search(r"\((\d+)\s*MHz\)", speed_raw)
            speed_mhz = int(speed_match.group(1)) * 2 if speed_match else None

            voltage = extract_number(kv.get("nominal voltage"))

            model_name = part_number or f"{mfg} {capacity_mb}MB {mem_type}"

            modules.append({
                "slot_or_bus": slot_name,
                "manufacturer": mfg,
                "model_name": model_name,
                "part_number": part_number,
                "serial_number": serial_number,
                "specs": {
                    "capacity_mb": capacity_mb,
                    "type": mem_type,
                    "module_format": mod_format,
                    "speed_mhz": speed_mhz,
                    "voltage": voltage,
                }
            })

        return modules

    def parse_storage_drives(self) -> List[Dict[str, Any]]:
        """Parses hard drives and SSDs from the Storage section."""
        drives = []
        storage_text = self._get_section_matching("Storage")
        if not storage_text:
            return drives

        drive_blocks = re.split(r"(Drive\s*#?\s*\t*\d+)", storage_text)

        for i in range(1, len(drive_blocks), 2):
            raw_drive = drive_blocks[i].strip()
            drive_label = re.sub(r"[\t\s]+", " ", raw_drive).strip()

            block_content = drive_blocks[i + 1] if i + 1 < len(drive_blocks) else ""
            kv = self._parse_key_values(block_content)

            model_name = clean_text(kv.get("name"))
            if not model_name:
                continue

            serial_number = clean_oem_string(kv.get("serial number") or kv.get("serial"))
            capacity_raw = kv.get("capacity")
            capacity_gb = extract_number(capacity_raw)
            drive_type = clean_text(kv.get("type")) or "Fixed"
            bus_type = clean_text(kv.get("bus type")) or "SATA"
            firmware = clean_text(kv.get("revision"))

            drives.append({
                "slot_or_bus": drive_label,
                "manufacturer": model_name.split()[0] if model_name else "Unknown",
                "model_name": model_name,
                "serial_number": serial_number,
                "specs": {
                    "capacity_gb": capacity_gb,
                    "interface": bus_type,
                    "media_type": drive_type,
                    "firmware": firmware,
                }
            })

        return drives

    def parse_display_adapters(self) -> List[Dict[str, Any]]:
        """Parses display adapters / GPUs."""
        gpus = []
        disp_text = self._get_section_matching("Display Adapters", "Graphics")
        if not disp_text:
            return gpus

        adapter_blocks = re.split(r"(Display\s*adapter\s*#?\s*\d+)", disp_text, flags=re.I)

        for i in range(1, len(adapter_blocks), 2):
            adapter_label = re.sub(r"[\t\s]+", " ", adapter_blocks[i].strip())
            block_content = adapter_blocks[i + 1] if i + 1 < len(adapter_blocks) else ""
            kv = self._parse_key_values(block_content)

            gpu_name = clean_text(kv.get("name")) or clean_text(kv.get("description"))
            if not gpu_name:
                continue

            mfg = clean_manufacturer(kv.get("board manufacturer")) or "Generic"
            vram_raw = kv.get("memory size")
            vram_mb = int(extract_number(vram_raw)) if vram_raw else None

            is_integrated = True if any(k in gpu_name.lower() for k in ["intel", "hd graphics", "uhd graphics", "radeon graphics", "integrated"]) else False

            gpus.append({
                "slot_or_bus": adapter_label,
                "manufacturer": mfg,
                "model_name": gpu_name,
                "serial_number": None,
                "specs": {
                    "vram_mb": vram_mb,
                    "is_integrated": is_integrated,
                }
            })

        return gpus

    def parse_all(self) -> Dict[str, Any]:
        """Runs the entire parser and outputs a structured contract ready for ingestion."""
        dev = self.parse_device_info()
        rams = self.parse_ram_modules()
        storage = self.parse_storage_drives()
        gpus = self.parse_display_adapters()

        total_ram = sum(r["specs"].get("capacity_mb", 0) for r in rams)
        total_storage = sum(s["specs"].get("capacity_gb", 0) for s in storage)

        dev["total_ram_mb"] = total_ram
        dev["total_storage_gb"] = total_storage

        return {
            "source_file": self.filename,
            "device": dev,
            "ram_modules": rams,
            "storage_drives": storage,
            "display_adapters": gpus,
        }
