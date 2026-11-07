import sqlite3
from fastapi import APIRouter, Depends
from backend.app.core.database import get_db_session
from backend.app.schemas.stats import SystemStats
from backend.app.services.stats_service import get_system_stats
from backend.app.api.endpoints_devices import router as devices_router
from backend.app.api.endpoints_assets import router as assets_router
from backend.app.api.endpoints_persons import router as persons_router
from backend.app.api.endpoints_custody import router as custody_router
from backend.app.api.endpoints_ingest import router as ingest_router

api_router = APIRouter()

api_router.include_router(devices_router)
api_router.include_router(assets_router)
api_router.include_router(persons_router)
api_router.include_router(custody_router)
api_router.include_router(ingest_router)

@api_router.get("/stats", response_model=SystemStats, tags=["System Stats"])
def system_overview_stats(conn: sqlite3.Connection = Depends(get_db_session)):
    """Fetches real-time inventory aggregation metrics for the dashboard header."""
    return get_system_stats(conn)
