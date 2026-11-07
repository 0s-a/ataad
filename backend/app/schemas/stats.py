from pydantic import BaseModel

class SystemStats(BaseModel):
    devices_count: int
    active_devices_count: int
    total_ram_gb: float
    total_storage_tb: float
    drawer_parts_count: int
    custody_active_count: int
    persons_count: int
