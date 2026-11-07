import sqlite3
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from backend.app.core.database import get_db_session
from backend.app.schemas.custody import (
    CustodyAssignRequest,
    CustodyReturnRequest,
    CustodyLogResponse,
)
from backend.app.services.custody_service import (
    assign_custody,
    return_custody,
    get_custody_logs,
)

router = APIRouter(prefix="/custody", tags=["Custody Operations"])

@router.post("/assign")
def assign_asset_custody(
    payload: CustodyAssignRequest,
    conn: sqlite3.Connection = Depends(get_db_session),
):
    """Assigns an asset to a person and logs the action."""
    try:
        return assign_custody(
            conn,
            asset_id=payload.asset_id,
            person_id=payload.person_id,
            notes=payload.notes,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/return")
def return_asset_custody(
    payload: CustodyReturnRequest,
    conn: sqlite3.Connection = Depends(get_db_session),
):
    """Returns an asset from custody to storage (drawer) or to active status."""
    try:
        return return_custody(
            conn,
            asset_id=payload.asset_id,
            destination=payload.destination,
            storage_box_label=payload.storage_box_label,
            notes=payload.notes,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/logs", response_model=List[CustodyLogResponse])
def list_custody_logs(
    asset_id: Optional[str] = Query(None, description="Filter by asset ID"),
    person_id: Optional[str] = Query(None, description="Filter by person ID"),
    limit: int = Query(100, ge=1, le=500, description="Max logs to return"),
    conn: sqlite3.Connection = Depends(get_db_session),
):
    """Fetches the immutable audit trail of physical and custody movements."""
    return get_custody_logs(conn, asset_id=asset_id, person_id=person_id, limit=limit)
