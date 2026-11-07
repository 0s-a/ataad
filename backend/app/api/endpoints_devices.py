import sqlite3
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from backend.app.core.database import get_db_session
from backend.app.schemas.device import DeviceListItem, DeviceDetail, DeviceCreate, DeviceUpdate
from backend.app.services.device_service import (
    get_devices_list,
    get_device_detail,
    create_manual_device,
    update_device,
)
from backend.app.services.asset_service import delete_asset

router = APIRouter(prefix="/devices", tags=["Devices"])

@router.get("", response_model=List[DeviceListItem])
def list_devices(
    search: Optional[str] = Query(None, description="Search by name, model, serial, or cpu"),
    conn: sqlite3.Connection = Depends(get_db_session),
):
    """Lists all computer devices and assemblies."""
    return get_devices_list(conn, search=search)

@router.get("/{device_id}", response_model=DeviceDetail)
def get_device(
    device_id: str,
    conn: sqlite3.Connection = Depends(get_db_session),
):
    """Gets complete device specifications and tree of mounted components."""
    device = get_device_detail(conn, device_id)
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")
    return device

@router.post("", response_model=DeviceDetail, status_code=status.HTTP_201_CREATED)
def create_device(
    payload: DeviceCreate,
    conn: sqlite3.Connection = Depends(get_db_session),
):
    """Manually registers a new computer device."""
    return create_manual_device(conn, payload.model_dump())

@router.put("/{device_id}", response_model=DeviceDetail)
def modify_device(
    device_id: str,
    payload: DeviceUpdate,
    conn: sqlite3.Connection = Depends(get_db_session),
):
    """Updates host device details."""
    updated = update_device(conn, device_id, payload.model_dump(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")
    return updated

@router.delete("/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_device(
    device_id: str,
    conn: sqlite3.Connection = Depends(get_db_session),
):
    """Deletes a device."""
    success = delete_asset(conn, device_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")
    return None
