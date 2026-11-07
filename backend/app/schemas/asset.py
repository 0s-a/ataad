from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

class AssetBase(BaseModel):
    name: Optional[str] = None
    serial_number: Optional[str] = None
    slot_or_bus: Optional[str] = None
    storage_box_label: Optional[str] = None
    notes: Optional[str] = None
    specs: Dict[str, Any] = Field(default_factory=dict)

class AssetCreate(AssetBase):
    component_type_slug: str = "RAM"  # RAM, STORAGE, GPU, CPU, etc.
    manufacturer: Optional[str] = None
    model_name: Optional[str] = None
    status: str = "in_storage"  # in_storage, active, installed, etc.
    parent_asset_id: Optional[str] = None

class AssetUpdate(BaseModel):
    name: Optional[str] = None
    serial_number: Optional[str] = None
    storage_box_label: Optional[str] = None
    notes: Optional[str] = None
    specs: Optional[Dict[str, Any]] = None
    status: Optional[str] = None

class AssetResponse(BaseModel):
    id: str
    name: Optional[str] = None
    serial_number: Optional[str] = None
    slot_or_bus: Optional[str] = None
    status: str
    storage_box_label: Optional[str] = None
    notes: Optional[str] = None
    specs: Dict[str, Any] = Field(default_factory=dict)
    component_type_slug: Optional[str] = None
    component_type_label: Optional[str] = None
    component_type_icon: Optional[str] = None
    manufacturer: Optional[str] = None
    model_name: Optional[str] = None
    parent_asset_id: Optional[str] = None
    parent_asset_name: Optional[str] = None
    assigned_person_id: Optional[str] = None
    assigned_person_name: Optional[str] = None
    assigned_at: Optional[str] = None
    first_seen_at: Optional[str] = None
    last_seen_at: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class MountRequest(BaseModel):
    target_device_id: str
    slot_or_bus: str

class UnmountRequest(BaseModel):
    storage_box_label: str
