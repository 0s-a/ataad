import os
from pathlib import Path
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent

_env_db = os.getenv("ATAAD_DB_PATH") or os.getenv("DATABASE_URL")
DB_FILE = Path(_env_db) if _env_db else BASE_DIR / "ataad.db"

_env_schema = os.getenv("ATAAD_SCHEMA_PATH")
SCHEMA_FILE = Path(_env_schema) if _env_schema else BASE_DIR / "schema.sql"

_env_dist = os.getenv("ATAAD_FRONTEND_DIST")
FRONTEND_DIST = Path(_env_dist) if _env_dist else BASE_DIR / "frontend" / "dist"

class Settings(BaseModel):
    app_name: str = "عَتاد (Ataad)"
    app_version: str = "3.0.0"
    db_path: Path = DB_FILE
    schema_path: Path = SCHEMA_FILE
    frontend_dist_path: Path = FRONTEND_DIST
    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]

settings = Settings()


