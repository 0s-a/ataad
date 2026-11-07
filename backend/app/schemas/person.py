from typing import Optional, List
from pydantic import BaseModel, Field
from backend.app.schemas.asset import AssetResponse

class PersonBase(BaseModel):
    name: str
    phone: Optional[str] = None
    relationship: Optional[str] = None
    notes: Optional[str] = None

class PersonCreate(PersonBase):
    pass

class PersonUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    relationship: Optional[str] = None
    notes: Optional[str] = None

class PersonResponse(PersonBase):
    id: str
    active_custody_count: int = 0
    created_at: Optional[str] = None

class PersonDetail(PersonResponse):
    active_assets: List[AssetResponse] = Field(default_factory=list)
