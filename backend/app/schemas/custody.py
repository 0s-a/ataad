from typing import Optional
from pydantic import BaseModel

class CustodyAssignRequest(BaseModel):
    asset_id: str
    person_id: str
    notes: Optional[str] = None

class CustodyReturnRequest(BaseModel):
    asset_id: str
    destination: str = "in_storage"  # "in_storage" or "active"
    storage_box_label: Optional[str] = None
    notes: Optional[str] = None

class CustodyLogResponse(BaseModel):
    id: str
    asset_id: str
    asset_name: Optional[str] = None
    serial_number: Optional[str] = None
    person_id: Optional[str] = None
    person_name: Optional[str] = None
    action: str
    notes: Optional[str] = None
    created_at: str
