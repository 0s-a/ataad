from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class IngestPreviewResponse(BaseModel):
    is_existing: bool
    existing_device_id: Optional[str] = None
    existing_device_name: Optional[str] = None
    device: Dict[str, Any]
    ram_modules: List[Dict[str, Any]] = Field(default_factory=list)
    storage_drives: List[Dict[str, Any]] = Field(default_factory=list)
    display_adapters: List[Dict[str, Any]] = Field(default_factory=list)
    drift_forecast: List[Dict[str, Any]] = Field(default_factory=list)

class IngestCommitResponse(BaseModel):
    session_id: str
    asset_id: str
    is_new_device: bool
    device_name: str
    components_count: int
    drift_count: int
    message: str
