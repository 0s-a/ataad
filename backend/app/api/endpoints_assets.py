import sqlite3
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from backend.app.core.database import get_db_session
from backend.app.schemas.asset import (
    AssetResponse,
    AssetCreate,
    AssetUpdate,
    MountRequest,
    UnmountRequest,
)
from backend.app.services.asset_service import (
    get_drawer_assets,
    get_asset_by_id,
    create_manual_asset,
    update_asset,
    delete_asset,
    mount_component,
    unmount_component,
)

router = APIRouter(prefix="/assets", tags=["Assets & Drawer"])

@router.get("/drawer", response_model=List[AssetResponse])
def list_drawer_parts(
    category: Optional[str] = Query(None, description="Category slug: RAM, STORAGE, GPU, CPU, etc."),
    search: Optional[str] = Query(None, description="Search query"),
    conn: sqlite3.Connection = Depends(get_db_session),
):
    """Fetches all spare parts stored in drawer boxes ('in_storage')."""
    return get_drawer_assets(conn, category=category, search=search)

@router.get("/{asset_id}", response_model=AssetResponse)
def get_asset(
    asset_id: str,
    conn: sqlite3.Connection = Depends(get_db_session),
):
    """Gets details of an individual asset."""
    asset = get_asset_by_id(conn, asset_id)
    if not asset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")
    return asset

@router.post("", response_model=AssetResponse, status_code=status.HTTP_201_CREATED)
def create_asset(
    payload: AssetCreate,
    conn: sqlite3.Connection = Depends(get_db_session),
):
    """Manually registers a new hardware component or spare part."""
    return create_manual_asset(conn, payload.model_dump())

@router.put("/{asset_id}", response_model=AssetResponse)
def modify_asset(
    asset_id: str,
    payload: AssetUpdate,
    conn: sqlite3.Connection = Depends(get_db_session),
):
    """Updates editable asset details."""
    updated = update_asset(conn, asset_id, payload.model_dump(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")
    return updated

@router.delete("/{asset_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_asset(
    asset_id: str,
    conn: sqlite3.Connection = Depends(get_db_session),
):
    """Deletes an asset from the inventory."""
    success = delete_asset(conn, asset_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")
    return None

@router.post("/{asset_id}/mount")
def mount_asset_to_device(
    asset_id: str,
    payload: MountRequest,
    conn: sqlite3.Connection = Depends(get_db_session),
):
    """Mounts a component asset into a destination host device."""
    try:
        return mount_component(
            conn,
            asset_id=asset_id,
            target_device_id=payload.target_device_id,
            slot_or_bus=payload.slot_or_bus,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/{asset_id}/unmount")
def unmount_asset_to_drawer(
    asset_id: str,
    payload: UnmountRequest,
    conn: sqlite3.Connection = Depends(get_db_session),
):
    """Unmounts a component asset from its device into a storage box in the drawer."""
    try:
        return unmount_component(
            conn,
            asset_id=asset_id,
            storage_box_label=payload.storage_box_label,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
