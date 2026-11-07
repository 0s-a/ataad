import sqlite3
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from backend.app.core.database import get_db_session
from backend.app.schemas.person import PersonResponse, PersonDetail, PersonCreate, PersonUpdate
from backend.app.schemas.asset import AssetResponse
from backend.app.services.person_service import (
    get_persons_list,
    get_person_detail,
    create_person,
    update_person,
    delete_person,
)
from backend.app.services.custody_service import get_active_custody_by_person, get_custody_logs

router = APIRouter(prefix="/persons", tags=["Persons & Custody"])

@router.get("", response_model=List[PersonResponse])
def list_persons(
    search: Optional[str] = Query(None, description="Search by name, phone, or relationship"),
    conn: sqlite3.Connection = Depends(get_db_session),
):
    """Lists all contacts and indicates their active custody count."""
    return get_persons_list(conn, search=search)

@router.get("/{person_id}", response_model=PersonDetail)
def get_person(
    person_id: str,
    conn: sqlite3.Connection = Depends(get_db_session),
):
    """Gets person contact details and their active custody assets."""
    person = get_person_detail(conn, person_id)
    if not person:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Person not found")
    return person

@router.post("", response_model=PersonDetail, status_code=status.HTTP_201_CREATED)
def add_person(
    payload: PersonCreate,
    conn: sqlite3.Connection = Depends(get_db_session),
):
    """Registers a new person in the contacts book."""
    return create_person(conn, payload.model_dump())

@router.put("/{person_id}", response_model=PersonDetail)
def modify_person(
    person_id: str,
    payload: PersonUpdate,
    conn: sqlite3.Connection = Depends(get_db_session),
):
    """Updates person details."""
    updated = update_person(conn, person_id, payload.model_dump(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Person not found")
    return updated

@router.delete("/{person_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_person(
    person_id: str,
    conn: sqlite3.Connection = Depends(get_db_session),
):
    """Deletes a person from contacts (only if no active assets held in custody)."""
    try:
        success = delete_person(conn, person_id)
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Person not found")
        return None
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/{person_id}/custody", response_model=List[AssetResponse])
def get_person_custody(
    person_id: str,
    conn: sqlite3.Connection = Depends(get_db_session),
):
    """Gets all assets currently held in custody by this person."""
    person = get_person_detail(conn, person_id)
    if not person:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Person not found")
    return get_active_custody_by_person(conn, person_id)
