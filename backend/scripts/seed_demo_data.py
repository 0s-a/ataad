#!/usr/bin/env python3
"""
عَتاد (Ataad) - سكريبت زراعة البيانات التأسيسية والعرض التوضيحي (Seed Demo Data Script)
========================================================================================
يقوم هذا السكريبت بتهيئة قاعدة البيانات وملئها ببيانات تجريبية واقعية وغنية متوافقة
مع المخطط الشامل v3.0 ونظام التصميم Medusa UI:
1. تهيئة قاعدة البيانات والتأكد من تفعيل Foreign Keys والقيود الصارمة.
2. إضافة 3 أجهزة حاسوبية واقعية مع بروفايلاتها الكاملة:
   - لابتوب Dell Latitude E6440 (مطابق لتقرير CPU-Z الفعلي MINWINPC.txt)
   - خادم التخزين المنزلي HomeLab NAS (Supermicro X10SL7-F / Xeon E3-1240 v3)
   - حاسوب الألعاب والتصميم Custom Gaming Rig (ASUS B550 / Ryzen 7 5800X / RTX 3070)
3. تركيب المكونات الداخلية (RAM, Storage, GPU) داخل الأجهزة.
4. إضافة 8 قطع مفكوكة في درج قطع الغيار (in_storage) مع بطاقات أماكن حفظ واضحة.
5. إضافة 3 أشخاص (Persons) مع عُهد نشطة وسجل تاريخي دقيق في custody_logs.
"""

import argparse
import json
import os
import sqlite3
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# ضبط مسار المشروع الأساسي لتمكين استيراد وحدات backend
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.core.config import settings
from backend.app.core.database import init_db, get_db
from backend.app.services.asset_service import recalculate_device_totals
from backend.app.services.stats_service import get_system_stats

# دالة توليد معرفات UUID ثابتة ومتكررة لكل كيان تأسيسي لضمان ثبات البيانات عبر مرات التشغيل
def seed_id(name: str) -> str:
    """Generates deterministic UUIDv5 strings for seed entities."""
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, f"ataad.seed.v3.{name}"))

def clean_json(data: Dict[str, Any]) -> str:
    """Serializes dictionary to clean UTF-8 JSON string."""
    return json.dumps(data, ensure_ascii=False)


def seed_demo_data(reset: bool = True) -> Dict[str, Any]:
    """
    Seeds comprehensive and realistic demo data into the Ataad SQLite database.
    """
    print("=" * 75)
    print("🚀 بدء عملية زراعة البيانات التأسيسية لمشروع عَتاد (Ataad v3.0)...")
    print(f"📂 مسار قاعدة البيانات: {settings.db_path}")
    print("=" * 75)

    # 1. تهيئة قاعدة البيانات
    init_db()

    with get_db() as conn:
        cur = conn.cursor()

        # إذا طُلب التصفير الكامل، نمسح البيانات التجريبية السابقة مع الحفاظ على جدول component_types المدمج
        if reset:
            print("🧹 جاري تصفير البيانات القديمة لضمان بيئة نظيفة...")
            cur.execute("PRAGMA foreign_keys = OFF;")
            cur.execute("DELETE FROM hardware_drift_logs;")
            cur.execute("DELETE FROM scan_sessions;")
            cur.execute("DELETE FROM custody_logs;")
            cur.execute("DELETE FROM device_profiles;")
            cur.execute("DELETE FROM assets;")
            cur.execute("DELETE FROM asset_models;")
            cur.execute("DELETE FROM persons;")
            cur.execute("DELETE FROM manufacturers;")
            cur.execute("PRAGMA foreign_keys = ON;")
            print("✅ تم تفريغ الجداول بنجاح.")

        # ------------------------------------------------------------------------
        # 2. المصنعون والشركات (Manufacturers)
        # ------------------------------------------------------------------------
        print("🏢 إضافة الشركات المصنعة (Manufacturers)...")
        manufacturers_data = [
            ("mfg.dell", "Dell Inc.", "https://www.dell.com", "شركة تصنيع الحواسيب المحمولة والمكتبية ومحطات العمل"),
            ("mfg.supermicro", "Supermicro", "https://www.supermicro.com", "حلول الخوادم المتقدمة واللوحات الصناعية"),
            ("mfg.asus", "ASUSTeK COMPUTER INC.", "https://www.asus.com", "لوحات ألعاب ROG وكروت شاشة وتجهيزات عالية الأداء"),
            ("mfg.hp", "HP Inc.", "https://www.hp.com", "أجهزة لابتوب أعمال وسلاسل ProBook و EliteBook"),
            ("mfg.samsung", "Samsung Electronics", "https://semiconductor.samsung.com", "ذواكر أشباه الموصلات وأقراص NVMe فائقة السرعة"),
            ("mfg.micron", "Micron Technology", "https://www.micron.com", "ذواكر الخوادم ومحطات العمل وشرائح ECC"),
            ("mfg.crucial", "Crucial", "https://www.crucial.com", "ذواكر وتخزين المستهلكين"),
            ("mfg.kingston", "Kingston Technology", "https://www.kingston.com", "ذواكر رام Fury ووحدات تخزين SSD"),
            ("mfg.seagate", "Seagate Technology", "https://www.seagate.com", "أقراص صلبة متخصصة لأنظمة التخزين الشبكي NAS"),
            ("mfg.wd", "Western Digital", "https://www.westerndigital.com", "محركات أقراص صلبة WD Blue و Red"),
            ("mfg.msi", "MSI", "https://www.msi.com", "كروت الشاشة وعتاد الألعاب الموجه للاعبين"),
            ("mfg.corsair", "Corsair Gaming", "https://www.corsair.com", "ذواكر عشوائية RGB وتجهيزات احترافية"),
            ("mfg.supersonic", "SUPERSONIC", None, "محركات أقراص SSD التجارية"),
            ("mfg.intel", "Intel Corporation", "https://www.intel.com", "المعالجات والشرائح وبطاقات الشبكة اللاسلكية"),
            ("mfg.amd", "Advanced Micro Devices (AMD)", "https://www.amd.com", "معالجات Ryzen عالية الأداء ومعمارية Zen"),
        ]

        mfg_map = {}
        for key, name, website, notes in manufacturers_data:
            m_id = seed_id(key)
            mfg_map[key] = m_id
            cur.execute(
                """
                INSERT INTO manufacturers (id, name, website, notes, created_at)
                VALUES (?, ?, ?, ?, datetime('now'))
                ON CONFLICT(name) DO UPDATE SET website=excluded.website, notes=excluded.notes;
                """,
                (m_id, name, website, notes),
            )
        print(f"✅ تم تسجيل {len(manufacturers_data)} مصنعين.")

        # ------------------------------------------------------------------------
        # 3. كتالوج الموديلات (Asset Models)
        # ------------------------------------------------------------------------
        print("📑 إضافة كتالوج الموديلات (Asset Models)...")
        models_data = [
            # Host Devices
            ("model.dell-e6440", mfg_map["mfg.dell"], "ct-device", "Latitude E6440", "05BD", {"chassis_subtype": "laptop"}),
            ("model.smc-nas", mfg_map["mfg.supermicro"], "ct-device", "SuperServer 5028D-NAS", "SYS-5028D", {"chassis_subtype": "server_rack"}),
            ("model.rig-5800x", mfg_map["mfg.asus"], "ct-device", "ROG Strix Custom Gaming Rig", "ROG-B550-STATION", {"chassis_subtype": "desktop_tower"}),
            ("model.hp-probook", mfg_map["mfg.hp"], "ct-device", "HP ProBook 450 G2", "G2-BROADWELL", {"chassis_subtype": "laptop"}),

            # RAM Models
            ("model.ram-samsung-ddr3l", mfg_map["mfg.samsung"], "ct-ram", "Samsung 4GB DDR3L 1600MHz SO-DIMM", "M471B5173DB0-YK0", {"capacity_mb": 4096, "type": "DDR3L", "speed_mhz": 1600, "module_format": "SO-DIMM"}),
            ("model.ram-micron-ecc", mfg_map["mfg.micron"], "ct-ram", "Micron 8GB DDR3 ECC UDIMM 1600MHz", "18KSF1G72AZ-1G6E1", {"capacity_mb": 8192, "type": "DDR3", "speed_mhz": 1600, "module_format": "UDIMM", "ecc": True}),
            ("model.ram-corsair-rgb", mfg_map["mfg.corsair"], "ct-ram", "Corsair Vengeance RGB PRO 16GB DDR4 3600MHz", "CMW32GX4M2D3600C18", {"capacity_mb": 16384, "type": "DDR4", "speed_mhz": 3600, "module_format": "UDIMM"}),
            ("model.ram-corsair-lpx", mfg_map["mfg.corsair"], "ct-ram", "Corsair Vengeance LPX 16GB DDR4 3200MHz", "CMK16GX4M1E3200C16", {"capacity_mb": 16384, "type": "DDR4", "speed_mhz": 3200, "module_format": "UDIMM"}),
            ("model.ram-kingston-fury", mfg_map["mfg.kingston"], "ct-ram", "Kingston Fury Beast 16GB DDR4 3200MHz", "KF432C16BB/16", {"capacity_mb": 16384, "type": "DDR4", "speed_mhz": 3200, "module_format": "UDIMM"}),
            ("model.ram-crucial-ddr3l", mfg_map["mfg.crucial"], "ct-ram", "Crucial 8GB DDR3L 1600MHz SO-DIMM", "CT102464BF160B", {"capacity_mb": 8192, "type": "DDR3L", "speed_mhz": 1600, "module_format": "SO-DIMM"}),
            ("model.ram-samsung-ddr4", mfg_map["mfg.samsung"], "ct-ram", "Samsung 4GB DDR4 2666MHz SO-DIMM", "M471A5244CB0-CTD", {"capacity_mb": 4096, "type": "DDR4", "speed_mhz": 2666, "module_format": "SO-DIMM"}),

            # Storage Models
            ("model.ssd-supersonic", mfg_map["mfg.supersonic"], "ct-storage", "SUPERSONIC 256GB SSD", "SUPERSONIC256", {"capacity_gb": 238.5, "interface": "SATA", "form_factor": "2.5\""}),
            ("model.ssd-kc600", mfg_map["mfg.kingston"], "ct-storage", "Kingston KC600 256GB SSD", "SKC600/256G", {"capacity_gb": 256.0, "interface": "SATA", "form_factor": "2.5\""}),
            ("model.hdd-ironwolf-4tb", mfg_map["mfg.seagate"], "ct-storage", "Seagate IronWolf 4TB NAS HDD", "ST4000VN008", {"capacity_gb": 4000.0, "interface": "SATA", "form_factor": "3.5\"", "rpm": 5900}),
            ("model.ssd-samsung-980", mfg_map["mfg.samsung"], "ct-storage", "Samsung 980 1TB NVMe M.2 SSD", "MZ-V8V1T0BW", {"capacity_gb": 1000.0, "interface": "NVMe", "form_factor": "M.2 2280"}),
            ("model.ssd-samsung-980pro", mfg_map["mfg.samsung"], "ct-storage", "Samsung 980 PRO 1TB NVMe M.2 SSD", "MZ-V8P1T0BW", {"capacity_gb": 1000.0, "interface": "NVMe", "form_factor": "M.2 2280"}),
            ("model.hdd-wd-blue-2tb", mfg_map["mfg.wd"], "ct-storage", "WD Blue 2TB 3.5\" SATA HDD", "WD20EZAZ", {"capacity_gb": 2000.0, "interface": "SATA", "form_factor": "3.5\"", "rpm": 5400}),
            ("model.ssd-kingston-a400", mfg_map["mfg.kingston"], "ct-storage", "Kingston A400 240GB 2.5\" SATA SSD", "SA400S37/240G", {"capacity_gb": 240.0, "interface": "SATA", "form_factor": "2.5\""}),

            # GPU Models
            ("model.gpu-amd-8600m", mfg_map["mfg.dell"], "ct-gpu", "AMD Radeon HD 8600M", "HD-8600M", {"vram_mb": 2048, "vram_type": "GDDR5", "is_integrated": False}),
            ("model.gpu-rtx3070", mfg_map["mfg.asus"], "ct-gpu", "ASUS TUF Gaming GeForce RTX 3070 OC 8GB", "TUF-RTX3070-O8G-GAMING", {"vram_mb": 8192, "vram_type": "GDDR6", "is_integrated": False}),
            ("model.gpu-gtx1660s", mfg_map["mfg.msi"], "ct-gpu", "MSI GeForce GTX 1660 SUPER VENTUS XS OC 6GB", "GTX-1660S-VENTUS", {"vram_mb": 6144, "vram_type": "GDDR6", "is_integrated": False}),

            # Screen Model
            ("model.screen-dell-u2419h", mfg_map["mfg.dell"], "ct-screen", "Dell UltraSharp 24 Monitor", "U2419H", {"size_inch": 24.0, "resolution": "1920x1080", "panel_type": "IPS"}),
        ]

        model_map = {}
        for key, m_id, comp_type_id, m_name, model_no, def_specs in models_data:
            model_id = seed_id(key)
            model_map[key] = model_id
            cur.execute(
                """
                INSERT INTO asset_models (id, manufacturer_id, component_type_id, name, model_number, default_specs, created_at)
                VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
                ON CONFLICT(manufacturer_id, model_number) DO UPDATE SET
                    name=excluded.name,
                    default_specs=excluded.default_specs;
                """,
                (model_id, m_id, comp_type_id, m_name, model_no, clean_json(def_specs)),
            )
        print(f"✅ تم تسجيل {len(models_data)} موديل في الكتالوج.")

        # ------------------------------------------------------------------------
        # 4. جدول جهات الاتصال والأشخاص (Persons)
        # ------------------------------------------------------------------------
        print("👥 إضافة جهات الاتصال للعُهد (Persons)...")
        persons_data = [
            ("person.khalid", "م. خالد العمري", "+966 50 123 4567", "زميل عمل", "مهندس برمجيات وزميل في الفريق التقني"),
            ("person.ahmad", "أحمد المنصور", "+966 55 987 6543", "صديق", "صديق مقرب وزميل دراسة سابق"),
            ("person.sarah", "سارة علي", "+966 56 333 8899", "عائلة", "أختي - تستخدم شاشات وملحقات للعمل عن بعد"),
        ]

        person_map = {}
        for key, p_name, phone, rel, notes in persons_data:
            p_id = seed_id(key)
            person_map[key] = p_id
            cur.execute(
                """
                INSERT INTO persons (id, name, phone, relationship, notes, created_at)
                VALUES (?, ?, ?, ?, ?, datetime('now'));
                """,
                (p_id, p_name, phone, rel, notes),
            )
        print("✅ تم تسجيل 3 أشخاص بنجاح.")

        # ------------------------------------------------------------------------
        # 5. الأجهزة الحاسوبية الرئيسية والبروفايلات (Host Devices & Profiles)
        # ------------------------------------------------------------------------
        print("💻 إنشاء الأجهزة الحاسوبية الثلاثة والبروفايلات التفصيلية...")

        # قراءة تقرير CPU-Z الفعلي الخاص بلابتوب ديل لربطه في scan_sessions
        raw_cpuz_text = ""
        cpuz_file_path = PROJECT_ROOT / "MINWINPC.txt"
        if cpuz_file_path.exists():
            with open(cpuz_file_path, "r", encoding="latin-1") as f:
                raw_cpuz_text = f.read()

        # 5.1 الجهاز الأول: لابتوب العمل Dell Latitude E6440 (مطابق لملف MINWINPC.txt)
        dell_id = seed_id("device.dell-e6440")
        cur.execute(
            """
            INSERT INTO assets (
                id, asset_model_id, name, serial_number, status, specs,
                first_seen_at, last_seen_at, created_at, updated_at
            ) VALUES (?, ?, ?, ?, 'active', '{}', '2026-08-10 08:30:00', '2026-11-07 20:00:00', '2026-08-10 08:30:00', '2026-11-07 20:00:00');
            """,
            (dell_id, model_map["model.dell-e6440"], "لابتوب العمل Dell Latitude E6440", "5N0GN12"),
        )

        cur.execute(
            """
            INSERT INTO device_profiles (
                asset_id, chassis_subtype, system_uuid, system_serial,
                motherboard_vendor, motherboard_model, motherboard_serial, chipset,
                bios_version, bios_date, max_ram_capacity_mb, ram_slots_count,
                m2_slots_count, sata_ports_count, pcie_slots_summary,
                cpu_model, cpu_code_name, cpu_socket, cpu_cores, cpu_threads,
                cpu_base_clock_mhz, cpu_boost_clock_mhz, cpu_l3_cache_kb, cpu_tdp_watts,
                cpu_has_virtualization, cpu_summary, screen_size_inch, screen_resolution,
                power_supply_watts, battery_design_mwh, os_name, os_build, hostname,
                network_summary, primary_mac_address, total_ram_mb, total_storage_gb, last_scanned_at
            ) VALUES (
                ?, 'laptop', '4c4c4544-004e-3010-8047-b5c04f4e3132', '5N0GN12',
                'Dell Inc.', '0K9GNV', '/5N0GN12/CN129634B40029/', 'Intel Haswell / QM87',
                'A18', '05/19/2017', 16384, 2,
                0, 2, '1x Mini PCIe (WLAN), 1x Half Mini PCIe (WWAN)',
                'Intel Core i7 4600M', 'Haswell', 'Socket 947 rPGA', 2, 4,
                2900, 3600, 4096, 37,
                1, 'Intel(R) Core(TM) i7-4600M CPU @ 2.90GHz', 14.0, '1920x1080',
                65, 65000, 'Microsoft Windows 11 (10.0) Ultimate Edition 64-bit', '22621', 'MINWINPC',
                'Intel I217-LM Gigabit Ethernet / Intel Centrino Advanced-N 6235 Wi-Fi',
                '34:17:EB:C2:59:93', 8192, 238.5, '2026-11-07 20:00:00'
            );
            """,
            (dell_id,),
        )

        # ربط جلسة فحص CPU-Z حقيقية للجهاز
        dell_scan_id = seed_id("scan.dell-cpuz")
        cur.execute(
            """
            INSERT INTO scan_sessions (id, asset_id, scanned_at, source, file_name, raw_text, created_at)
            VALUES (?, ?, '2026-11-07 20:00:00', 'CPU-Z', 'MINWINPC.txt', ?, '2026-11-07 20:00:00');
            """,
            (dell_scan_id, dell_id, raw_cpuz_text),
        )

        # تسجيل حدث Hardware Drift تم توثيقه
        drift_id = seed_id("drift.dell-ram-upgrade")
        cur.execute(
            """
            INSERT INTO hardware_drift_logs (
                id, scan_session_id, asset_id, change_type, identifier,
                old_state, new_state, is_acknowledged, detected_at
            ) VALUES (?, ?, ?, 'PART_ADDED', 'DIMM 2', '{}', '{"model":"M471B5173DB0-YK0","capacity_mb":4096}', 1, '2026-11-07 20:00:00');
            """,
            (drift_id, dell_scan_id, dell_id),
        )

        # 5.2 الجهاز الثاني: خادم التخزين المنزلي HomeLab NAS
        nas_id = seed_id("device.homelab-nas")
        cur.execute(
            """
            INSERT INTO assets (
                id, asset_model_id, name, serial_number, status, specs,
                first_seen_at, last_seen_at, created_at, updated_at
            ) VALUES (?, ?, ?, ?, 'active', '{}', '2026-08-20 10:00:00', '2026-11-06 12:00:00', '2026-08-20 10:00:00', '2026-11-06 12:00:00');
            """,
            (nas_id, model_map["model.smc-nas"], "خادم التخزين المنزلي HomeLab NAS", "SMC-NAS-2024-X10"),
        )

        cur.execute(
            """
            INSERT INTO device_profiles (
                asset_id, chassis_subtype, system_uuid, system_serial,
                motherboard_vendor, motherboard_model, motherboard_serial, chipset,
                bios_version, bios_date, max_ram_capacity_mb, ram_slots_count,
                m2_slots_count, sata_ports_count, pcie_slots_summary,
                cpu_model, cpu_code_name, cpu_socket, cpu_cores, cpu_threads,
                cpu_base_clock_mhz, cpu_boost_clock_mhz, cpu_l3_cache_kb, cpu_tdp_watts,
                cpu_has_virtualization, cpu_summary, screen_size_inch, screen_resolution,
                power_supply_watts, battery_design_mwh, os_name, os_build, hostname,
                network_summary, primary_mac_address, total_ram_mb, total_storage_gb, last_scanned_at
            ) VALUES (
                ?, 'server_rack', '58a2d104-e314-41b9-8e77-96a84d2f0102', 'SMC-NAS-2024-X10',
                'Supermicro', 'X10SL7-F', 'ZM148S009871', 'Intel C222 Express PCH',
                '3.3a', '2022-06-20', 32768, 4,
                1, 8, '1x PCIe 3.0 x8 (in x16 slot), 1x PCIe 2.0 x4',
                'Intel Xeon E3-1240 v3', 'Haswell-WS', 'LGA1150', 4, 8,
                3400, 3800, 8192, 80,
                1, 'Intel(R) Xeon(TM) CPU E3-1240 v3 @ 3.40GHz', NULL, NULL,
                350, NULL, 'TrueNAS CORE 13.0-U6.1 (FreeBSD 13.1)', '13.0-RELEASE-p12', 'homelab-nas.local',
                'Dual 1GbE Intel i210-AT + Dedicated IPMI LAN', '00:25:90:AB:CD:12',
                32768, 8256.0, '2026-11-06 12:00:00'
            );
            """,
            (nas_id,),
        )

        # 5.3 الجهاز الثالث: حاسوب الألعاب والتصميم Custom Gaming Rig
        rig_id = seed_id("device.gaming-rig")
        cur.execute(
            """
            INSERT INTO assets (
                id, asset_model_id, name, serial_number, status, specs,
                first_seen_at, last_seen_at, created_at, updated_at
            ) VALUES (?, ?, ?, ?, 'active', '{}', '2026-09-10 12:00:00', '2026-11-05 18:30:00', '2026-09-10 12:00:00', '2026-11-05 18:30:00');
            """,
            (rig_id, model_map["model.rig-5800x"], "حاسوب الألعاب والتصميم Custom Gaming Rig", "ASUS-RIG-5800X-3070"),
        )

        cur.execute(
            """
            INSERT INTO device_profiles (
                asset_id, chassis_subtype, system_uuid, system_serial,
                motherboard_vendor, motherboard_model, motherboard_serial, chipset,
                bios_version, bios_date, max_ram_capacity_mb, ram_slots_count,
                m2_slots_count, sata_ports_count, pcie_slots_summary,
                cpu_model, cpu_code_name, cpu_socket, cpu_cores, cpu_threads,
                cpu_base_clock_mhz, cpu_boost_clock_mhz, cpu_l3_cache_kb, cpu_tdp_watts,
                cpu_has_virtualization, cpu_summary, screen_size_inch, screen_resolution,
                power_supply_watts, battery_design_mwh, os_name, os_build, hostname,
                network_summary, primary_mac_address, total_ram_mb, total_storage_gb, last_scanned_at
            ) VALUES (
                ?, 'desktop_tower', '71a938c0-8209-42b7-a8fe-35cf8e26b149', 'ASUS-RIG-5800X-3070',
                'ASUSTeK COMPUTER INC.', 'ROG STRIX B550-F GAMING', '210484918204912', 'AMD B550',
                '3404', '10/18/2023', 131072, 4,
                2, 6, '1x PCIe 4.0 x16, 1x PCIe 3.0 x16 (@x4), 3x PCIe 3.0 x1',
                'AMD Ryzen 7 5800X', 'Vermeer (Zen 3)', 'Socket AM4', 8, 16,
                3800, 4700, 32768, 105,
                1, 'AMD Ryzen 7 5800X 8-Core Processor @ 3.80GHz', NULL, NULL,
                750, NULL, 'Microsoft Windows 11 Pro 64-bit', '26100', 'APEX-STATION',
                'Intel I225-V 2.5GbE Ethernet / Wi-Fi 6 AX200', 'AC:12:03:FE:84:AA',
                32768, 1000.0, '2026-11-05 18:30:00'
            );
            """,
            (rig_id,),
        )

        # 5.4 جهاز رابع عهدة نشطة: لابتوب HP قديم بحوزة أحمد المنصور (with_person)
        hp_id = seed_id("device.hp-probook")
        cur.execute(
            """
            INSERT INTO assets (
                id, asset_model_id, assigned_person_id, assigned_at, name, serial_number, status, specs,
                first_seen_at, last_seen_at, created_at, updated_at
            ) VALUES (?, ?, ?, '2026-10-12 11:00:00', ?, ?, 'with_person', '{}', '2026-07-01 10:00:00', '2026-10-12 11:00:00', '2026-07-01 10:00:00', '2026-10-12 11:00:00');
            """,
            (hp_id, model_map["model.hp-probook"], person_map["person.ahmad"], "لابتوب HP ProBook 450 G2", "5CD61234XYZ"),
        )

        cur.execute(
            """
            INSERT INTO device_profiles (
                asset_id, chassis_subtype, system_uuid, system_serial,
                motherboard_vendor, motherboard_model, motherboard_serial, chipset,
                bios_version, bios_date, max_ram_capacity_mb, ram_slots_count,
                m2_slots_count, sata_ports_count, pcie_slots_summary,
                cpu_model, cpu_code_name, cpu_socket, cpu_cores, cpu_threads,
                cpu_base_clock_mhz, cpu_boost_clock_mhz, cpu_l3_cache_kb, cpu_tdp_watts,
                cpu_has_virtualization, cpu_summary, screen_size_inch, screen_resolution,
                power_supply_watts, battery_design_mwh, os_name, os_build, hostname,
                network_summary, primary_mac_address, total_ram_mb, total_storage_gb, last_scanned_at
            ) VALUES (
                ?, 'laptop', 'e14b9c10-5321-4d32-bc90-998811223344', '5CD61234XYZ',
                'Hewlett-Packard', 'HP 2248', 'PEFRB0182941', 'Intel Broadwell-U',
                'M74 Ver. 01.49', '08/12/2019', 16384, 2,
                0, 1, '1x Mini PCIe (WLAN)',
                'Intel Core i5-5200U', 'Broadwell', 'Socket 1168 BGA', 2, 4,
                2200, 2700, 3072, 15,
                1, 'Intel(R) Core(TM) i5-5200U CPU @ 2.20GHz', 15.6, '1366x768',
                45, 44000, 'Microsoft Windows 10 Pro 64-bit', '19045.4291', 'AHMAD-PROBOOK',
                'Realtek PCIe GBE Family Controller / Realtek RTL8723BE Wi-Fi', 'B8:88:E3:4A:21:67',
                8192, 256.0, '2026-10-12 11:00:00'
            );
            """,
            (hp_id,),
        )
        print("✅ تم إنشاء الأجهزة وبروفايلاتها الكاملة.")

        # ------------------------------------------------------------------------
        # 6. تركيب المكونات داخل الأجهزة (Installed Components)
        # ------------------------------------------------------------------------
        print("🛠️ تركيب الرامات والهاردات وكروت الشاشة داخل الأجهزة...")
        installed_components = [
            # مكونات لابتوب Dell Latitude E6440
            ("comp.dell.ram1", model_map["model.ram-samsung-ddr3l"], dell_id, "Samsung 4GB DDR3L 1600MHz SO-DIMM", "1770EBC2", "DIMM 1",
             {"capacity_mb": 4096, "type": "DDR3L", "speed_mhz": 1600, "voltage": 1.35, "module_format": "SO-DIMM", "timings": "11-11-11-28"}),
            ("comp.dell.ram2", model_map["model.ram-samsung-ddr3l"], dell_id, "Samsung 4GB DDR3L 1600MHz SO-DIMM", "1770EC34", "DIMM 2",
             {"capacity_mb": 4096, "type": "DDR3L", "speed_mhz": 1600, "voltage": 1.35, "module_format": "SO-DIMM", "timings": "11-11-11-28"}),
            ("comp.dell.ssd", model_map["model.ssd-supersonic"], dell_id, "SUPERSONIC 256GB SSD", "VT256SS034636 VC08", "Drive 0",
             {"capacity_gb": 238.5, "interface": "SATA", "form_factor": "2.5\"", "nand_type": "TLC", "firmware": "T1130A0"}),
            ("comp.dell.gpu", model_map["model.gpu-amd-8600m"], dell_id, "AMD Radeon HD 8600M 2GB", "AMD-8600M-DELL", "PCIe bus 1",
             {"vram_mb": 2048, "vram_type": "GDDR5", "interface": "PCIe x8", "is_integrated": False, "tdp_watts": 35}),

            # مكونات خادم HomeLab NAS
            ("comp.nas.ram1", model_map["model.ram-micron-ecc"], nas_id, "Micron 8GB DDR3 ECC UDIMM 1600MHz", "0B2E1091", "DIMM A1",
             {"capacity_mb": 8192, "type": "DDR3", "speed_mhz": 1600, "voltage": 1.35, "module_format": "UDIMM", "timings": "11-11-11-28", "ecc": True}),
            ("comp.nas.ram2", model_map["model.ram-micron-ecc"], nas_id, "Micron 8GB DDR3 ECC UDIMM 1600MHz", "0B2E1092", "DIMM A2",
             {"capacity_mb": 8192, "type": "DDR3", "speed_mhz": 1600, "voltage": 1.35, "module_format": "UDIMM", "timings": "11-11-11-28", "ecc": True}),
            ("comp.nas.ram3", model_map["model.ram-micron-ecc"], nas_id, "Micron 8GB DDR3 ECC UDIMM 1600MHz", "0B2E1093", "DIMM B1",
             {"capacity_mb": 8192, "type": "DDR3", "speed_mhz": 1600, "voltage": 1.35, "module_format": "UDIMM", "timings": "11-11-11-28", "ecc": True}),
            ("comp.nas.ram4", model_map["model.ram-micron-ecc"], nas_id, "Micron 8GB DDR3 ECC UDIMM 1600MHz", "0B2E1094", "DIMM B2",
             {"capacity_mb": 8192, "type": "DDR3", "speed_mhz": 1600, "voltage": 1.35, "module_format": "UDIMM", "timings": "11-11-11-28", "ecc": True}),
            ("comp.nas.boot", model_map["model.ssd-kc600"], nas_id, "Kingston KC600 256GB SSD (Boot)", "50026B7684091A01", "SATA 0 (Boot)",
             {"capacity_gb": 256.0, "interface": "SATA", "form_factor": "2.5\"", "nand_type": "TLC"}),
            ("comp.nas.hdd1", model_map["model.hdd-ironwolf-4tb"], nas_id, "Seagate IronWolf 4TB NAS HDD #1", "ZGY3A89K", "SATA 1",
             {"capacity_gb": 4000.0, "interface": "SATA", "form_factor": "3.5\"", "rpm": 5900}),
            ("comp.nas.hdd2", model_map["model.hdd-ironwolf-4tb"], nas_id, "Seagate IronWolf 4TB NAS HDD #2", "ZGY3A92L", "SATA 2",
             {"capacity_gb": 4000.0, "interface": "SATA", "form_factor": "3.5\"", "rpm": 5900}),

            # مكونات حاسوب الألعاب والتصميم Custom Gaming Rig
            ("comp.rig.ram1", model_map["model.ram-corsair-rgb"], rig_id, "Corsair Vengeance RGB PRO 16GB DDR4 3600MHz", "049812401", "DIMM_A2",
             {"capacity_mb": 16384, "type": "DDR4", "speed_mhz": 3600, "voltage": 1.35, "module_format": "UDIMM", "timings": "18-22-22-42"}),
            ("comp.rig.ram2", model_map["model.ram-corsair-rgb"], rig_id, "Corsair Vengeance RGB PRO 16GB DDR4 3600MHz", "049812402", "DIMM_B2",
             {"capacity_mb": 16384, "type": "DDR4", "speed_mhz": 3600, "voltage": 1.35, "module_format": "UDIMM", "timings": "18-22-22-42"}),
            ("comp.rig.nvme", model_map["model.ssd-samsung-980"], rig_id, "Samsung 980 1TB NVMe M.2 SSD", "S64ANX0R512049", "M.2_1 (PCIe 4.0 x4)",
             {"capacity_gb": 1000.0, "interface": "NVMe", "form_factor": "M.2 2280", "nand_type": "TLC"}),
            ("comp.rig.gpu", model_map["model.gpu-rtx3070"], rig_id, "ASUS TUF Gaming GeForce RTX 3070 OC 8GB", "M9C0YZ008124", "PCIe 4.0 x16",
             {"vram_mb": 8192, "vram_type": "GDDR6", "interface": "PCIe x16", "tdp_watts": 240, "is_integrated": False}),
        ]

        installed_map = {}
        for key, m_id, parent_id, c_name, serial, slot, specs in installed_components:
            comp_id = seed_id(key)
            installed_map[key] = comp_id
            cur.execute(
                """
                INSERT INTO assets (
                    id, asset_model_id, parent_asset_id, assigned_person_id, name,
                    serial_number, slot_or_bus, specs, status, storage_box_label,
                    first_seen_at, last_seen_at, created_at, updated_at
                ) VALUES (
                    ?, ?, ?, NULL, ?,
                    ?, ?, ?, 'installed', NULL,
                    '2026-08-10 10:00:00', datetime('now'), '2026-08-10 10:00:00', datetime('now')
                );
                """,
                (comp_id, m_id, parent_id, c_name, serial, slot, clean_json(specs)),
            )

            # توثيق حركة التركيب في custody_logs
            cur.execute(
                """
                INSERT INTO custody_logs (id, asset_id, person_id, action, notes, created_at)
                VALUES (?, ?, NULL, 'installed', ?, '2026-08-10 10:00:00');
                """,
                (seed_id(f"log.install.{key}"), comp_id, f"تم تركيب القطعة في المنفذ {slot}"),
            )
        print(f"✅ تم تركيب {len(installed_components)} قطعة بنجاح داخل الأجهزة.")

        # ------------------------------------------------------------------------
        # 7. قطع الغيار المفكوكة في الدرج (8 Spare Parts in Drawer - in_storage)
        # ------------------------------------------------------------------------
        print("🗄️ إضافة 8 قطع مفكوكة في درج قطع الغيار (status = 'in_storage')...")
        drawer_parts = [
            # 1. رامات مفكوكة (3 قطع)
            ("drawer.ram-kingston-fury", model_map["model.ram-kingston-fury"], "Kingston Fury Beast 16GB DDR4 3200MHz", "9905702-049.A00G-1", "درج 1 - علبة A",
             {"capacity_mb": 16384, "type": "DDR4", "speed_mhz": 3200, "voltage": 1.35, "module_format": "UDIMM", "timings": "16-18-18-36"}),
            ("drawer.ram-crucial-ddr3l", model_map["model.ram-crucial-ddr3l"], "Crucial 8GB DDR3L 1600MHz SO-DIMM", "CT8G3S160BM-81", "درج 1 - علبة A",
             {"capacity_mb": 8192, "type": "DDR3L", "speed_mhz": 1600, "voltage": 1.35, "module_format": "SO-DIMM", "timings": "11-11-11-28"}),
            ("drawer.ram-samsung-ddr4", model_map["model.ram-samsung-ddr4"], "Samsung 4GB DDR4 2666MHz SO-DIMM", "19283746-SAM4", "درج 1 - علبة A",
             {"capacity_mb": 4096, "type": "DDR4", "speed_mhz": 2666, "voltage": 1.2, "module_format": "SO-DIMM", "timings": "19-19-19-43"}),

            # 2. هاردات مفكوكة (3 قطع)
            ("drawer.ssd-samsung-980pro", model_map["model.ssd-samsung-980pro"], "Samsung 980 PRO 1TB NVMe M.2 SSD", "S5GXNF0R918231", "صندوق قطع الغيار B",
             {"capacity_gb": 1000.0, "interface": "NVMe", "form_factor": "M.2 2280", "nand_type": "TLC", "read_speed_mbps": 7000}),
            ("drawer.hdd-wd-blue", model_map["model.hdd-wd-blue-2tb"], "WD Blue 2TB 3.5\" SATA HDD", "WD-WCC4M3289012", "درج 1 - علبة A",
             {"capacity_gb": 2000.0, "interface": "SATA", "form_factor": "3.5\"", "rpm": 5400}),
            ("drawer.ssd-kingston-a400", model_map["model.ssd-kingston-a400"], "Kingston A400 240GB 2.5\" SATA SSD", "50026B7782049102", "درج 1 - علبة A",
             {"capacity_gb": 240.0, "interface": "SATA", "form_factor": "2.5\"", "nand_type": "TLC"}),

            # 3. كرت شاشة مفكوك (قطعة 1)
            ("drawer.gpu-msi-gtx1660s", model_map["model.gpu-gtx1660s"], "MSI GeForce GTX 1660 SUPER VENTUS XS OC 6GB", "602-V375-380B2009001928", "صندوق قطع الغيار B",
             {"vram_mb": 6144, "vram_type": "GDDR6", "interface": "PCIe x16", "tdp_watts": 125, "is_integrated": False}),

            # 4. الشاشة المسترجعة من سارة علي بعد انتهاء إعارتها (القطعة الثامنة)
            ("drawer.screen-dell-u2419h", model_map["model.screen-dell-u2419h"], "شاشة Dell UltraSharp U2419H 24 بوصة", "CN-08K90N-74261-98A-1234", "صندوق قطع الغيار B",
             {"size_inch": 24.0, "resolution": "1920x1080", "panel_type": "IPS", "refresh_hz": 60}),
        ]

        drawer_map = {}
        for key, m_id, d_name, serial, box_label, specs in drawer_parts:
            part_id = seed_id(key)
            drawer_map[key] = part_id
            cur.execute(
                """
                INSERT INTO assets (
                    id, asset_model_id, parent_asset_id, assigned_person_id, name,
                    serial_number, slot_or_bus, specs, status, storage_box_label,
                    first_seen_at, last_seen_at, created_at, updated_at
                ) VALUES (
                    ?, ?, NULL, NULL, ?,
                    ?, NULL, ?, 'in_storage', ?,
                    '2026-09-01 12:00:00', datetime('now'), '2026-09-01 12:00:00', datetime('now')
                );
                """,
                (part_id, m_id, d_name, serial, clean_json(specs), box_label),
            )

            # توثيق حركة التخزين في custody_logs
            cur.execute(
                """
                INSERT INTO custody_logs (id, asset_id, person_id, action, notes, created_at)
                VALUES (?, ?, NULL, 'stored', ?, '2026-09-10 12:00:00');
                """,
                (seed_id(f"log.store.{key}"), part_id, f"تم حفظ القطعة في {box_label}"),
            )
        print("✅ تم إضافة 8 قطع مفكوكة في درج قطع الغيار بنجاح.")

        # ------------------------------------------------------------------------
        # 8. عُهد الأشخاص وحركات التاريخ (Custody Assignments & History)
        # ------------------------------------------------------------------------
        print("🤝 تسجيل العُهد النشطة وتوثيق الحركات التاريخية (Timeline Logs)...")

        # 8.1 عهدة نشطة لم. خالد العمري (شريحة رام Corsair Vengeance LPX 16GB)
        khalid_ram_id = seed_id("custody.ram-khalid")
        cur.execute(
            """
            INSERT INTO assets (
                id, asset_model_id, parent_asset_id, assigned_person_id, assigned_at, name,
                serial_number, slot_or_bus, specs, status, storage_box_label,
                first_seen_at, last_seen_at, created_at, updated_at
            ) VALUES (
                ?, ?, NULL, ?, '2026-10-25 14:30:00', ?,
                'COR-16G-DDR4-991', NULL, ?, 'with_person', NULL,
                '2026-09-01 10:00:00', '2026-10-25 14:30:00', '2026-09-01 10:00:00', '2026-10-25 14:30:00'
            );
            """,
            (
                khalid_ram_id,
                model_map["model.ram-corsair-lpx"],
                person_map["person.khalid"],
                "Corsair Vengeance LPX 16GB DDR4 3200MHz",
                clean_json({"capacity_mb": 16384, "type": "DDR4", "speed_mhz": 3200, "voltage": 1.35, "module_format": "UDIMM"}),
            ),
        )

        cur.execute(
            """
            INSERT INTO custody_logs (id, asset_id, person_id, action, notes, created_at)
            VALUES (?, ?, ?, 'assigned', 'إعارة شريحة رام لاختبار ترقية بيئة العمل ومشاريع المحاكاة', '2026-10-25 14:30:00');
            """,
            (seed_id("log.khalid-assigned"), khalid_ram_id, person_map["person.khalid"]),
        )

        # 8.2 حركة تسليم لابتوب HP لأحمد المنصور
        cur.execute(
            """
            INSERT INTO custody_logs (id, asset_id, person_id, action, notes, created_at)
            VALUES (?, ?, ?, 'assigned', 'تسليم لابتوب HP ProBook لإكمال مشروع التخرج الجامعي', '2026-10-12 11:00:00');
            """,
            (seed_id("log.ahmad-assigned"), hp_id, person_map["person.ahmad"]),
        )

        # 8.3 توثيق حركة تسليم واسترجاع شاشة سارة علي (Dell UltraSharp U2419H)
        sarah_screen_id = drawer_map["drawer.screen-dell-u2419h"]
        cur.execute(
            """
            INSERT INTO custody_logs (id, asset_id, person_id, action, notes, created_at)
            VALUES (?, ?, ?, 'assigned', 'تسليم شاشة Dell UltraSharp للعمل عن بُعد من المنزل', '2026-09-01 10:00:00');
            """,
            (seed_id("log.sarah-assigned"), sarah_screen_id, person_map["person.sarah"]),
        )

        cur.execute(
            """
            INSERT INTO custody_logs (id, asset_id, person_id, action, notes, created_at)
            VALUES (?, ?, ?, 'returned', 'تم استرجاع الشاشة بحالة ممتازة وحفظها في صندوق قطع الغيار B', '2026-10-15 16:45:00');
            """,
            (seed_id("log.sarah-returned"), sarah_screen_id, person_map["person.sarah"]),
        )

        # توثيق حركة سابقة: فك كرت الشاشة GTX 1660 Super بعد ترقية كرت الألعاب
        msi_gpu_id = drawer_map["drawer.gpu-msi-gtx1660s"]
        cur.execute(
            """
            INSERT INTO custody_logs (id, asset_id, person_id, action, notes, created_at)
            VALUES (?, ?, NULL, 'uninstalled', 'فك الكرت من جهاز الألعاب السابق بعد شراء RTX 3070 وحفظه بالصندوق', '2026-09-10 15:30:00');
            """,
            (seed_id("log.gtx1660s-uninstalled"), msi_gpu_id),
        )

        # ------------------------------------------------------------------------
        # 9. إعادة حساب إجماليات الرام والتخزين لجميع الأجهزة
        # ------------------------------------------------------------------------
        print("🔄 إعادة حساب إجماليات الرام والتخزين الفعلي للأجهزة...")
        for dev_id in [dell_id, nas_id, rig_id, hp_id]:
            recalculate_device_totals(conn, dev_id)

    # ------------------------------------------------------------------------
    # 10. التحقق من صحة الإحصائيات العامة
    # ------------------------------------------------------------------------
    with get_db() as conn:
        stats = get_system_stats(conn)
        print("\n" + "=" * 75)
        print("📊 ملخص مؤشرات لوحة التحكم بعد زراعة البيانات:")
        print(f"  • إجمالي الحواسيب:        {stats['devices_count']} أجهزة (منها {stats['active_devices_count']} نشطة)")
        print(f"  • إجمالي الذاكرة العشوائية: {stats['total_ram_gb']} GB")
        print(f"  • إجمالي سعة التخزين:     {stats['total_storage_tb']} TB")
        print(f"  • قطع الغيار في الدرج:     {stats['drawer_parts_count']} قطع (in_storage)")
        print(f"  • العُهد النشطة حالياً:    {stats['custody_active_count']} عُهد (with_person)")
        print(f"  • جهات الاتصال المسجلة:    {stats['persons_count']} أشخاص")
        print("=" * 75)
        print("✨ اكتملت زراعة البيانات التأسيسية بنجاح 100%! قاعدة البيانات جاهزة ومبهرة.\n")

    return stats


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed Ataad database with rich demo data.")
    parser.add_argument(
        "--no-reset",
        action="store_true",
        help="Do not wipe existing tables before seeding",
    )
    args = parser.parse_args()

    seed_demo_data(reset=not args.no_reset)
