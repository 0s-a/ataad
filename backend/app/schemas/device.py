from typing import Optional, List, Any, Dict
from pydantic import BaseModel, Field

class DeviceProfileSchema(BaseModel):
    asset_id: str
    chassis_subtype: Optional[str] = None
    system_uuid: Optional[str] = None
    system_serial: Optional[str] = None
    motherboard_vendor: Optional[str] = None
    motherboard_model: Optional[str] = None
    motherboard_serial: Optional[str] = None
    chipset: Optional[str] = None
    bios_version: Optional[str] = None
    bios_date: Optional[str] = None
    max_ram_capacity_mb: Optional[int] = None
    ram_slots_count: Optional[int] = 2
    m2_slots_count: Optional[int] = 0
    sata_ports_count: Optional[int] = 0
    pcie_slots_summary: Optional[str] = None
    cpu_model: Optional[str] = None
    cpu_code_name: Optional[str] = None
    cpu_socket: Optional[str] = None
    cpu_cores: Optional[int] = None
    cpu_threads: Optional[int] = None
    cpu_base_clock_mhz: Optional[int] = None
    cpu_boost_clock_mhz: Optional[int] = None
    cpu_l3_cache_kb: Optional[int] = None
    cpu_tdp_watts: Optional[int] = None
    cpu_has_virtualization: Optional[int] = 1
    cpu_summary: Optional[str] = None
    screen_size_inch: Optional[float] = None
    screen_resolution: Optional[str] = None
    power_supply_watts: Optional[int] = None
    battery_design_mwh: Optional[int] = None
    os_name: Optional[str] = None
    os_build: Optional[str] = None
    hostname: Optional[str] = None
    network_summary: Optional[str] = None
    primary_mac_address: Optional[str] = None
    total_ram_mb: Optional[int] = 0
    total_storage_gb: Optional[float] = 0.0
    last_scanned_at: Optional[str] = None

class DeviceCreate(BaseModel):
    name: str
    manufacturer: Optional[str] = None
    model_name: Optional[str] = None
    serial_number: Optional[str] = None
    chassis_subtype: Optional[str] = "laptop"
    cpu_model: Optional[str] = None
    notes: Optional[str] = None

class DeviceUpdate(BaseModel):
    name: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    chassis_subtype: Optional[str] = None

class DeviceListItem(BaseModel):
    id: str
    name: Optional[str] = None
    serial_number: Optional[str] = None
    status: str
    storage_box_label: Optional[str] = None
    manufacturer: Optional[str] = None
    model_name: Optional[str] = None
    chassis_subtype: Optional[str] = None
    cpu_model: Optional[str] = None
    total_ram_mb: Optional[int] = 0
    total_storage_gb: Optional[float] = 0.0
    last_scanned_at: Optional[str] = None
    assigned_person_id: Optional[str] = None
    assigned_person_name: Optional[str] = None
    created_at: Optional[str] = None

class InstalledComponentItem(BaseModel):
    id: str
    name: Optional[str] = None
    serial_number: Optional[str] = None
    slot_or_bus: Optional[str] = None
    component_type_slug: str
    component_type_label: str
    manufacturer: Optional[str] = None
    model_name: Optional[str] = None
    specs: Dict[str, Any] = Field(default_factory=dict)
    status: str

class DeviceDetail(BaseModel):
    device: DeviceListItem
    profile: Optional[DeviceProfileSchema] = None
    installed_components: List[InstalledComponentItem] = Field(default_factory=list)
    recent_drift_logs: List[Dict[str, Any]] = Field(default_factory=list)
    scan_sessions_count: int = 0
