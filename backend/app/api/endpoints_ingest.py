import sqlite3
from typing import Optional
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import BaseModel
from backend.app.core.database import get_db_session
from backend.app.parsers.cpuz_parser import CPUZParser
from backend.app.schemas.ingest import IngestPreviewResponse, IngestCommitResponse
from backend.app.services.ingest_service import preview_ingest, ingest_cpuz_data

router = APIRouter(prefix="/ingest", tags=["CPU-Z Ingestion Engine"])

def decode_text_bytes(content: bytes) -> str:
    """Decodes raw text bytes trying UTF-8, CP1252 (standard Windows CPU-Z export), and Latin-1."""
    for enc in ("utf-8", "cp1252", "latin-1", "utf-16", "utf-16-le"):
        try:
            return content.decode(enc)
        except UnicodeDecodeError:
            continue
    return content.decode("utf-8", errors="replace")

class RawTextPayload(BaseModel):
    raw_text: str
    filename: Optional[str] = "cpuz_report.txt"

@router.post("/preview", response_model=IngestPreviewResponse)
async def preview_upload(
    file: UploadFile = File(...),
    conn: sqlite3.Connection = Depends(get_db_session),
):
    """
    Parses an uploaded CPU-Z report file (.txt) and returns a pre-flight preview:
    - Host device specifications detected.
    - Matching status with existing devices.
    - Component rollups (RAM modules, drives, GPUs).
    - Forecasted hardware drift if the device already exists.
    """
    content = await file.read()
    raw_text = decode_text_bytes(content)
    if not raw_text.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty.")

    try:
        parser = CPUZParser(raw_text, filename=file.filename)
        parsed_data = parser.parse_all()
        return preview_ingest(conn, parsed_data)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Failed to parse report: {str(e)}")

@router.post("/preview-raw", response_model=IngestPreviewResponse)
def preview_raw_text(
    payload: RawTextPayload,
    conn: sqlite3.Connection = Depends(get_db_session),
):
    """Generates preview from raw CPU-Z text payload."""
    if not payload.raw_text.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Raw text is empty.")
    try:
        parser = CPUZParser(payload.raw_text, filename=payload.filename)
        parsed_data = parser.parse_all()
        return preview_ingest(conn, parsed_data)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Failed to parse report: {str(e)}")

@router.post("/commit", response_model=IngestCommitResponse)
async def commit_upload(
    file: UploadFile = File(...),
    conn: sqlite3.Connection = Depends(get_db_session),
):
    """
    Performs full ingestion of the uploaded CPU-Z report:
    - Upserts catalog models and manufacturers.
    - Upserts host device and components into assets.
    - Detects and documents hardware drift (PART_ADDED, PART_REMOVED, PART_SWAPPED).
    - Records scan session in scan_sessions.
    """
    content = await file.read()
    raw_text = decode_text_bytes(content)
    if not raw_text.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty.")

    try:
        parser = CPUZParser(raw_text, filename=file.filename)
        parsed_data = parser.parse_all()
        result = ingest_cpuz_data(conn, parsed_data, raw_text=raw_text, filename=file.filename)
        return result
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Ingestion failed: {str(e)}")

@router.post("/commit-raw", response_model=IngestCommitResponse)
def commit_raw_text(
    payload: RawTextPayload,
    conn: sqlite3.Connection = Depends(get_db_session),
):
    """Commits CPU-Z report from raw text payload."""
    if not payload.raw_text.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Raw text is empty.")
    try:
        parser = CPUZParser(payload.raw_text, filename=payload.filename)
        parsed_data = parser.parse_all()
        result = ingest_cpuz_data(conn, parsed_data, raw_text=payload.raw_text, filename=payload.filename)
        return result
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Ingestion failed: {str(e)}")
