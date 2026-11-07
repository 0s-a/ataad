import json
import sqlite3
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

def get_or_create_manufacturer(conn: sqlite3.Connection, name: Optional[str]) -> Optional[str]:
    """Upserts manufacturer and returns its ID."""
    clean_name = (name or "").strip()
    if not clean_name:
        return None

    cur = conn.cursor()
    cur.execute("SELECT id FROM manufacturers WHERE LOWER(name) = LOWER(?);", (clean_name,))
    row = cur.fetchone()
    if row:
        return row["id"]

    mfg_id = str(uuid.uuid4())
    cur.execute(
        "INSERT INTO manufacturers (id, name, created_at) VALUES (?, ?, datetime('now'));",
        (mfg_id, clean_name),
    )
    return mfg_id

def get_or_create_asset_model(
    conn: sqlite3.Connection,
    manufacturer_id: Optional[str],
    component_type_id: str,
    name: str,
    model_number: Optional[str] = None,
    default_specs: Optional[Dict[str, Any]] = None,
) -> str:
    """Upserts asset model and returns its ID."""
    cur = conn.cursor()
    specs_json = json.dumps(default_specs or {})
    clean_name = (name or "Unknown Model").strip()
    clean_model_number = (model_number or "").strip() or None

    # Try matching by (manufacturer_id, model_number) if model_number exists
    if clean_model_number:
        if manufacturer_id:
            cur.execute(
                "SELECT id FROM asset_models WHERE manufacturer_id = ? AND model_number = ?;",
                (manufacturer_id, clean_model_number),
            )
        else:
            cur.execute(
                "SELECT id FROM asset_models WHERE manufacturer_id IS NULL AND model_number = ?;",
                (clean_model_number,),
            )
        row = cur.fetchone()
        if row:
            return row["id"]

    # Otherwise match by (manufacturer_id, component_type_id, name)
    if manufacturer_id:
        cur.execute(
            """
            SELECT id FROM asset_models
            WHERE manufacturer_id = ? AND component_type_id = ? AND LOWER(name) = LOWER(?);
            """,
            (manufacturer_id, component_type_id, clean_name),
        )
    else:
        cur.execute(
            """
            SELECT id FROM asset_models
            WHERE manufacturer_id IS NULL AND component_type_id = ? AND LOWER(name) = LOWER(?);
            """,
            (component_type_id, clean_name),
        )
    row = cur.fetchone()
    if row:
        return row["id"]

    # Insert new model
    model_id = str(uuid.uuid4())
    cur.execute(
        """
        INSERT INTO asset_models (
            id, manufacturer_id, component_type_id, name, model_number, default_specs, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, datetime('now'));
        """,
        (model_id, manufacturer_id, component_type_id, clean_name, clean_model_number, specs_json),
    )
    return model_id

def find_host_device(
    conn: sqlite3.Connection,
    system_uuid: Optional[str],
    system_serial: Optional[str],
    motherboard_serial: Optional[str],
) -> Optional[sqlite3.Row]:
    """Finds existing host device by system_uuid, system_serial, or motherboard_serial."""
    cur = conn.cursor()

    if system_uuid:
        cur.execute(
            """
            SELECT dp.*, a.name AS asset_name, a.status AS asset_status
            FROM device_profiles dp
            JOIN assets a ON dp.asset_id = a.id
            WHERE LOWER(dp.system_uuid) = LOWER(?);
            """,
            (system_uuid.strip(),),
        )
        row = cur.fetchone()
        if row:
            return row

    if system_serial:
        cur.execute(
            """
            SELECT dp.*, a.name AS asset_name, a.status AS asset_status
            FROM device_profiles dp
            JOIN assets a ON dp.asset_id = a.id
            WHERE LOWER(dp.system_serial) = LOWER(?);
            """,
            (system_serial.strip(),),
        )
        row = cur.fetchone()
        if row:
            return row

    if motherboard_serial:
        cur.execute(
            """
            SELECT dp.*, a.name AS asset_name, a.status AS asset_status
            FROM device_profiles dp
            JOIN assets a ON dp.asset_id = a.id
            WHERE LOWER(dp.motherboard_serial) = LOWER(?);
            """,
            (motherboard_serial.strip(),),
        )
        row = cur.fetchone()
        if row:
            return row

    return None

def preview_ingest(conn: sqlite3.Connection, parsed_data: Dict[str, Any]) -> Dict[str, Any]:
    """Generates a preview of the CPU-Z ingestion without modifying database state."""
    dev = parsed_data.get("device", {})
    system_uuid = dev.get("system_uuid")
    system_serial = dev.get("system_serial")
    mb_serial = dev.get("motherboard_serial")

    existing_device = find_host_device(conn, system_uuid, system_serial, mb_serial)
    is_existing = existing_device is not None
    existing_id = existing_device["asset_id"] if existing_device else None
    existing_name = existing_device["asset_name"] if existing_device else None

    drift_forecast = []
    if is_existing and existing_id:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT a.id, a.name, a.serial_number, a.slot_or_bus, a.specs, ct.slug AS comp_slug
            FROM assets a
            LEFT JOIN asset_models am ON a.asset_model_id = am.id
            LEFT JOIN component_types ct ON am.component_type_id = ct.id
            WHERE a.parent_asset_id = ? AND a.status = 'installed';
            """,
            (existing_id,),
        )
        current_installed = [dict(r) for r in cur.fetchall()]

        # Forecast additions, removals, swaps
        incoming_rams = parsed_data.get("ram_modules", [])
        incoming_storage = parsed_data.get("storage_drives", [])
        incoming_gpus = parsed_data.get("display_adapters", [])

        # Match RAMs by slot_or_bus
        curr_rams_by_slot = {
            r["slot_or_bus"]: r for r in current_installed if r.get("comp_slug") == "RAM" and r.get("slot_or_bus")
        }
        for ram in incoming_rams:
            slot = ram.get("slot_or_bus")
            serial = ram.get("serial_number")
            if slot in curr_rams_by_slot:
                curr = curr_rams_by_slot[slot]
                if serial and curr.get("serial_number") and serial != curr.get("serial_number"):
                    drift_forecast.append({
                        "change_type": "PART_SWAPPED",
                        "component": "RAM",
                        "slot": slot,
                        "old": curr.get("name") or curr.get("serial_number"),
                        "new": ram.get("model_name") or serial,
                    })
            else:
                drift_forecast.append({
                    "change_type": "PART_ADDED",
                    "component": "RAM",
                    "slot": slot,
                    "new": ram.get("model_name") or serial,
                })

        incoming_ram_slots = {ram.get("slot_or_bus") for ram in incoming_rams}
        for slot, curr in curr_rams_by_slot.items():
            if slot not in incoming_ram_slots:
                drift_forecast.append({
                    "change_type": "PART_REMOVED",
                    "component": "RAM",
                    "slot": slot,
                    "old": curr.get("name") or curr.get("serial_number"),
                })

    return {
        "is_existing": is_existing,
        "existing_device_id": existing_id,
        "existing_device_name": existing_name,
        "device": dev,
        "ram_modules": parsed_data.get("ram_modules", []),
        "storage_drives": parsed_data.get("storage_drives", []),
        "display_adapters": parsed_data.get("display_adapters", []),
        "drift_forecast": drift_forecast,
    }

def ingest_cpuz_data(
    conn: sqlite3.Connection,
    parsed_data: Dict[str, Any],
    raw_text: Optional[str] = None,
    filename: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Core ingestion service:
    1. Upserts manufacturer and host device model.
    2. Matches or creates host asset and updates device_profiles.
    3. Records scan session in scan_sessions.
    4. Upserts parts (RAM, Storage, GPU) and detects drift.
    5. Recalculates device totals.
    """
    dev = parsed_data.get("device", {})
    mfg_name = dev.get("manufacturer") or "Generic OEM"
    model_name = dev.get("model") or "Custom PC"
    system_uuid = dev.get("system_uuid")
    system_serial = dev.get("system_serial")
    mb_serial = dev.get("motherboard_serial")

    cur = conn.cursor()

    # 1. Upsert Manufacturer
    mfg_id = get_or_create_manufacturer(conn, mfg_name)

    # 2. Upsert Device Model in asset_models
    dev_model_id = get_or_create_asset_model(
        conn,
        manufacturer_id=mfg_id,
        component_type_id="ct-device",
        name=model_name,
        model_number=system_serial,
        default_specs={"chassis_subtype": dev.get("chassis_subtype")},
    )

    # 3. Match or Create Host Asset
    existing_device = find_host_device(conn, system_uuid, system_serial, mb_serial)
    is_new_device = existing_device is None

    if is_new_device:
        host_asset_id = str(uuid.uuid4())
        dev_display_name = f"{mfg_name} {model_name}" if mfg_name not in model_name else model_name
        cur.execute(
            """
            INSERT INTO assets (
                id, asset_model_id, name, serial_number, status, specs,
                first_seen_at, last_seen_at, created_at, updated_at
            ) VALUES (?, ?, ?, ?, 'active', '{}', datetime('now'), datetime('now'), datetime('now'), datetime('now'));
            """,
            (host_asset_id, dev_model_id, dev_display_name, system_serial or mb_serial),
        )

        cur.execute(
            """
            INSERT INTO device_profiles (
                asset_id, chassis_subtype, system_uuid, system_serial,
                motherboard_vendor, motherboard_model, motherboard_serial, chipset,
                bios_version, bios_date, max_ram_capacity_mb, ram_slots_count,
                cpu_model, cpu_code_name, cpu_socket, cpu_cores, cpu_threads,
                cpu_base_clock_mhz, cpu_boost_clock_mhz, cpu_l3_cache_kb, cpu_tdp_watts,
                cpu_has_virtualization, cpu_summary, screen_size_inch, screen_resolution,
                power_supply_watts, battery_design_mwh, os_name, os_build, hostname,
                network_summary, primary_mac_address, total_ram_mb, total_storage_gb, last_scanned_at
            ) VALUES (
                ?, ?, ?, ?,
                ?, ?, ?, ?,
                ?, ?, ?, ?,
                ?, ?, ?, ?, ?,
                ?, ?, ?, ?,
                ?, ?, ?, ?,
                ?, ?, ?, ?, ?,
                ?, ?, ?, ?, datetime('now')
            );
            """,
            (
                host_asset_id,
                dev.get("chassis_subtype"),
                system_uuid,
                system_serial,
                dev.get("motherboard_vendor"),
                dev.get("motherboard_model"),
                mb_serial,
                dev.get("chipset"),
                dev.get("bios_version"),
                dev.get("bios_date"),
                dev.get("max_ram_capacity_mb"),
                dev.get("ram_slots_count") or 2,
                dev.get("cpu_model"),
                dev.get("cpu_code_name"),
                dev.get("cpu_socket"),
                dev.get("cpu_cores"),
                dev.get("cpu_threads"),
                dev.get("cpu_base_clock_mhz"),
                dev.get("cpu_boost_clock_mhz"),
                dev.get("cpu_l3_cache_kb"),
                dev.get("cpu_tdp_watts"),
                dev.get("cpu_has_virtualization", 1),
                dev.get("cpu_summary"),
                dev.get("screen_size_inch"),
                dev.get("screen_resolution"),
                dev.get("power_supply_watts"),
                dev.get("battery_design_mwh"),
                dev.get("os_name"),
                dev.get("os_build"),
                dev.get("hostname"),
                dev.get("network_summary"),
                dev.get("primary_mac_address"),
                dev.get("total_ram_mb", 0),
                dev.get("total_storage_gb", 0.0),
            ),
        )
    else:
        host_asset_id = existing_device["asset_id"]
        # Update assets table
        cur.execute(
            """
            UPDATE assets
            SET last_seen_at = datetime('now'),
                asset_model_id = COALESCE(asset_model_id, ?)
            WHERE id = ?;
            """,
            (dev_model_id, host_asset_id),
        )
        # Update device profile
        cur.execute(
            """
            UPDATE device_profiles
            SET chassis_subtype = COALESCE(?, chassis_subtype),
                system_uuid = COALESCE(?, system_uuid),
                system_serial = COALESCE(?, system_serial),
                motherboard_vendor = COALESCE(?, motherboard_vendor),
                motherboard_model = COALESCE(?, motherboard_model),
                motherboard_serial = COALESCE(?, motherboard_serial),
                chipset = COALESCE(?, chipset),
                bios_version = COALESCE(?, bios_version),
                bios_date = COALESCE(?, bios_date),
                max_ram_capacity_mb = COALESCE(?, max_ram_capacity_mb),
                ram_slots_count = COALESCE(?, ram_slots_count),
                cpu_model = COALESCE(?, cpu_model),
                cpu_code_name = COALESCE(?, cpu_code_name),
                cpu_socket = COALESCE(?, cpu_socket),
                cpu_cores = COALESCE(?, cpu_cores),
                cpu_threads = COALESCE(?, cpu_threads),
                cpu_base_clock_mhz = COALESCE(?, cpu_base_clock_mhz),
                cpu_boost_clock_mhz = COALESCE(?, cpu_boost_clock_mhz),
                cpu_l3_cache_kb = COALESCE(?, cpu_l3_cache_kb),
                cpu_tdp_watts = COALESCE(?, cpu_tdp_watts),
                cpu_has_virtualization = COALESCE(?, cpu_has_virtualization),
                cpu_summary = COALESCE(?, cpu_summary),
                screen_size_inch = COALESCE(?, screen_size_inch),
                screen_resolution = COALESCE(?, screen_resolution),
                power_supply_watts = COALESCE(?, power_supply_watts),
                battery_design_mwh = COALESCE(?, battery_design_mwh),
                os_name = COALESCE(?, os_name),
                os_build = COALESCE(?, os_build),
                hostname = COALESCE(?, hostname),
                network_summary = COALESCE(?, network_summary),
                primary_mac_address = COALESCE(?, primary_mac_address),
                total_ram_mb = ?,
                total_storage_gb = ?,
                last_scanned_at = datetime('now')
            WHERE asset_id = ?;
            """,
            (
                dev.get("chassis_subtype"),
                system_uuid,
                system_serial,
                dev.get("motherboard_vendor"),
                dev.get("motherboard_model"),
                mb_serial,
                dev.get("chipset"),
                dev.get("bios_version"),
                dev.get("bios_date"),
                dev.get("max_ram_capacity_mb"),
                dev.get("ram_slots_count"),
                dev.get("cpu_model"),
                dev.get("cpu_code_name"),
                dev.get("cpu_socket"),
                dev.get("cpu_cores"),
                dev.get("cpu_threads"),
                dev.get("cpu_base_clock_mhz"),
                dev.get("cpu_boost_clock_mhz"),
                dev.get("cpu_l3_cache_kb"),
                dev.get("cpu_tdp_watts"),
                dev.get("cpu_has_virtualization", 1),
                dev.get("cpu_summary"),
                dev.get("screen_size_inch"),
                dev.get("screen_resolution"),
                dev.get("power_supply_watts"),
                dev.get("battery_design_mwh"),
                dev.get("os_name"),
                dev.get("os_build"),
                dev.get("hostname"),
                dev.get("network_summary"),
                dev.get("primary_mac_address"),
                dev.get("total_ram_mb", 0),
                dev.get("total_storage_gb", 0.0),
                host_asset_id,
            ),
        )

    # 4. Create Scan Session
    session_id = str(uuid.uuid4())
    cur.execute(
        """
        INSERT INTO scan_sessions (id, asset_id, scanned_at, source, file_name, raw_text, created_at)
        VALUES (?, ?, datetime('now'), 'CPU-Z', ?, ?, datetime('now'));
        """,
        (session_id, host_asset_id, filename or parsed_data.get("source_file"), raw_text),
    )

    # 5. Retrieve existing installed components for drift detection
    cur.execute(
        """
        SELECT a.id, a.name, a.serial_number, a.slot_or_bus, a.specs, ct.slug AS comp_slug, a.asset_model_id
        FROM assets a
        LEFT JOIN asset_models am ON a.asset_model_id = am.id
        LEFT JOIN component_types ct ON am.component_type_id = ct.id
        WHERE a.parent_asset_id = ? AND a.status = 'installed';
        """,
        (host_asset_id,),
    )
    existing_installed = [dict(r) for r in cur.fetchall()]
    installed_by_slot = {r["slot_or_bus"]: r for r in existing_installed if r.get("slot_or_bus")}
    installed_by_serial = {r["serial_number"]: r for r in existing_installed if r.get("serial_number")}

    drift_logs_count = 0
    components_processed = 0
    active_component_ids = set()

    # Helper function for components
    def process_component(
        comp_type_id: str,
        comp_slug: str,
        comp_data: Dict[str, Any],
    ):
        nonlocal drift_logs_count, components_processed
        components_processed += 1

        slot = comp_data.get("slot_or_bus")
        comp_mfg = comp_data.get("manufacturer") or "Generic"
        comp_model_name = comp_data.get("model_name") or f"{comp_slug} Module"
        part_num = comp_data.get("part_number")
        serial = comp_data.get("serial_number")
        specs = comp_data.get("specs") or {}

        # Upsert manufacturer & model
        c_mfg_id = get_or_create_manufacturer(conn, comp_mfg)
        c_model_id = get_or_create_asset_model(
            conn,
            manufacturer_id=c_mfg_id,
            component_type_id=comp_type_id,
            name=comp_model_name,
            model_number=part_num,
            default_specs=specs,
        )

        # Check if this component already exists in DB
        matching_asset_id = None
        old_component = None

        # 1. Match by serial if present
        if serial:
            cur.execute("SELECT * FROM assets WHERE serial_number = ?;", (serial,))
            row = cur.fetchone()
            if row:
                matching_asset_id = row["id"]
                old_component = dict(row)

        # 2. Match by slot on this host device if not found by serial
        if not matching_asset_id and slot and slot in installed_by_slot:
            cand = installed_by_slot[slot]
            if cand.get("comp_slug") == comp_slug:
                # Same slot and same category
                # If neither has serial, treat as same asset
                if not serial and not cand.get("serial_number"):
                    matching_asset_id = cand["id"]
                    old_component = cand

        # Drift scenario analysis
        if not is_new_device:
            # Check slot swap
            if slot and slot in installed_by_slot:
                prev = installed_by_slot[slot]
                if prev.get("comp_slug") == comp_slug:
                    prev_serial = prev.get("serial_number")
                    if serial and prev_serial and serial != prev_serial:
                        # PART_SWAPPED: old component in slot was replaced
                        drift_id = str(uuid.uuid4())
                        cur.execute(
                            """
                            INSERT INTO hardware_drift_logs (
                                id, scan_session_id, asset_id, changed_asset_id,
                                change_type, identifier, old_state, new_state, detected_at
                            ) VALUES (?, ?, ?, ?, 'PART_SWAPPED', ?, ?, ?, datetime('now'));
                            """,
                            (
                                drift_id,
                                session_id,
                                host_asset_id,
                                matching_asset_id,
                                slot,
                                json.dumps(prev),
                                json.dumps(comp_data),
                            ),
                        )
                        drift_logs_count += 1
                        # Mark old component as in_storage
                        cur.execute(
                            """
                            UPDATE assets
                            SET parent_asset_id = NULL,
                                slot_or_bus = NULL,
                                status = 'in_storage',
                                notes = COALESCE(notes || ' | ', '') || 'Unmounted during scan swap'
                            WHERE id = ?;
                            """,
                            (prev["id"],),
                        )

            # Check new addition
            if not matching_asset_id and (slot not in installed_by_slot):
                # PART_ADDED
                drift_id = str(uuid.uuid4())
                cur.execute(
                    """
                    INSERT INTO hardware_drift_logs (
                        id, scan_session_id, asset_id, changed_asset_id,
                        change_type, identifier, old_state, new_state, detected_at
                    ) VALUES (?, ?, ?, NULL, 'PART_ADDED', ?, '{}', ?, datetime('now'));
                    """,
                    (drift_id, session_id, host_asset_id, slot, json.dumps(comp_data)),
                )
                drift_logs_count += 1

        # Upsert asset record
        if matching_asset_id:
            cur.execute(
                """
                UPDATE assets
                SET asset_model_id = ?,
                    parent_asset_id = ?,
                    slot_or_bus = ?,
                    status = 'installed',
                    storage_box_label = NULL,
                    assigned_person_id = NULL,
                    assigned_at = NULL,
                    specs = ?,
                    last_seen_at = datetime('now')
                WHERE id = ?;
                """,
                (c_model_id, host_asset_id, slot, json.dumps(specs), matching_asset_id),
            )
            active_component_ids.add(matching_asset_id)
        else:
            new_asset_id = str(uuid.uuid4())
            cur.execute(
                """
                INSERT INTO assets (
                    id, asset_model_id, parent_asset_id, assigned_person_id,
                    name, serial_number, slot_or_bus, specs, status,
                    storage_box_label, first_seen_at, last_seen_at, created_at, updated_at
                ) VALUES (
                    ?, ?, ?, NULL,
                    ?, ?, ?, ?, 'installed',
                    NULL, datetime('now'), datetime('now'), datetime('now'), datetime('now')
                );
                """,
                (
                    new_asset_id,
                    c_model_id,
                    host_asset_id,
                    comp_model_name,
                    serial,
                    slot,
                    json.dumps(specs),
                ),
            )
            active_component_ids.add(new_asset_id)

    # Ingest RAM modules
    for ram in parsed_data.get("ram_modules", []):
        process_component("ct-ram", "RAM", ram)

    # Ingest Storage drives
    for storage in parsed_data.get("storage_drives", []):
        process_component("ct-storage", "STORAGE", storage)

    # Ingest Display adapters (GPUs)
    for gpu in parsed_data.get("display_adapters", []):
        process_component("ct-gpu", "GPU", gpu)

    # Check for removed components (PART_REMOVED)
    if not is_new_device:
        for prev in existing_installed:
            if prev["id"] not in active_component_ids:
                drift_id = str(uuid.uuid4())
                cur.execute(
                    """
                    INSERT INTO hardware_drift_logs (
                        id, scan_session_id, asset_id, changed_asset_id,
                        change_type, identifier, old_state, new_state, detected_at
                    ) VALUES (?, ?, ?, ?, 'PART_REMOVED', ?, ?, '{}', datetime('now'));
                    """,
                    (
                        drift_id,
                        session_id,
                        host_asset_id,
                        prev["id"],
                        prev.get("slot_or_bus"),
                        json.dumps(prev),
                    ),
                )
                drift_logs_count += 1
                # Mark asset as in_storage
                cur.execute(
                    """
                    UPDATE assets
                    SET parent_asset_id = NULL,
                        slot_or_bus = NULL,
                        status = 'in_storage',
                        notes = COALESCE(notes || ' | ', '') || 'Part detected removed during scan'
                    WHERE id = ?;
                    """,
                    (prev["id"],),
                )

    # Recalculate totals in device_profiles
    cur.execute(
        """
        SELECT a.specs
        FROM assets a
        JOIN asset_models am ON a.asset_model_id = am.id
        WHERE a.parent_asset_id = ? AND a.status = 'installed' AND am.component_type_id = 'ct-ram';
        """,
        (host_asset_id,),
    )
    total_ram_mb = 0
    for r in cur.fetchall():
        s = json.loads(r["specs"] or "{}")
        total_ram_mb += int(s.get("capacity_mb", 0) or 0)

    cur.execute(
        """
        SELECT a.specs
        FROM assets a
        JOIN asset_models am ON a.asset_model_id = am.id
        WHERE a.parent_asset_id = ? AND a.status = 'installed' AND am.component_type_id = 'ct-storage';
        """,
        (host_asset_id,),
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
        (total_ram_mb, total_storage_gb, host_asset_id),
    )

    cur.execute("SELECT name FROM assets WHERE id = ?;", (host_asset_id,))
    final_name_row = cur.fetchone()
    device_name = final_name_row["name"] if final_name_row else model_name

    return {
        "session_id": session_id,
        "asset_id": host_asset_id,
        "is_new_device": is_new_device,
        "device_name": device_name,
        "components_count": components_processed,
        "drift_count": drift_logs_count,
        "message": f"Successfully ingested {components_processed} components. {drift_logs_count} drift events recorded.",
    }
