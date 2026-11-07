from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from backend.app.core.config import settings
from backend.app.core.database import init_db
from backend.app.api.router import api_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan event handler: initializes SQLite database and seed data on startup."""
    init_db()
    yield

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="عَتاد (Ataad) - Hardware Inventory & Custody Management System API v3.0",
    lifespan=lifespan,
)

# CORS Middleware setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount all API endpoints under /api
app.include_router(api_router, prefix="/api")

@app.get("/api/health", tags=["Health"])
def health():
    """Explicit health check endpoint."""
    return {
        "app": settings.app_name,
        "version": settings.app_version,
        "status": "online",
        "docs_url": "/docs",
    }

# Frontend SPA and static files integration
frontend_dist = settings.frontend_dist_path
if frontend_dist.exists() and (frontend_dist / "index.html").exists():
    assets_dir = frontend_dist / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

    @app.get("/", tags=["Root"])
    async def root_or_spa(request: Request):
        accept = request.headers.get("accept", "")
        # If browser requests HTML, serve index.html. Otherwise (curl, test clients, APIs) return health info
        if "text/html" in accept:
            return FileResponse(frontend_dist / "index.html")
        return {
            "app": settings.app_name,
            "version": settings.app_version,
            "status": "online",
            "docs_url": "/docs",
        }

    @app.get("/{full_path:path}", tags=["SPA"])
    async def serve_spa_paths(full_path: str):
        # Don't intercept API or docs routes
        if full_path.startswith("api") or full_path.startswith("docs") or full_path.startswith("openapi.json"):
            raise HTTPException(status_code=404, detail="Not Found")

        file_path = frontend_dist / full_path
        if full_path and file_path.is_file():
            return FileResponse(file_path)

        return FileResponse(frontend_dist / "index.html")
else:
    @app.get("/", tags=["Health"])
    def root():
        """Health check and application identity endpoint."""
        return {
            "app": settings.app_name,
            "version": settings.app_version,
            "status": "online",
            "docs_url": "/docs",
        }
