from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.health import router as health_router
from app.api.market_prices import router as market_prices_router
from app.api.settings import router as settings_router
from app.api.trending import router as trending_router
from app.core.config import FRONTEND_DIST
from app.db import init_db
from app.scheduler import shutdown_scheduler, start_scheduler


def create_app() -> FastAPI:
    app = FastAPI(title="Window of Eternity", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://127.0.0.1:5173", "http://localhost:5173", "http://127.0.0.1:3030", "http://localhost:3030"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(health_router)
    app.include_router(settings_router)
    app.include_router(trending_router)
    app.include_router(market_prices_router)

    @app.on_event("startup")
    def on_startup() -> None:
        init_db()
        start_scheduler()

    @app.on_event("shutdown")
    def on_shutdown() -> None:
        shutdown_scheduler()

    _mount_frontend(app, FRONTEND_DIST)
    return app


def _mount_frontend(app: FastAPI, dist_dir: Path) -> None:
    assets_dir = dist_dir / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/{path:path}", include_in_schema=False)
    def spa_fallback(path: str):
        index_file = dist_dir / "index.html"
        candidate = (dist_dir / path).resolve()
        if dist_dir.exists() and candidate.is_file() and dist_dir in candidate.parents:
            return FileResponse(candidate)
        if index_file.exists():
            return FileResponse(index_file)
        return JSONResponse(
            status_code=404,
            content={
                "detail": "Frontend build not found. Run the Vite build or use the Docker image that includes frontend/dist."
            },
        )


app = create_app()

