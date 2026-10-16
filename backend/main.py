from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes import router as api_router
from backend.api.websocket import router as websocket_router
from backend.app.config import get_settings
from backend.services.monitoring_service import monitoring_service

settings = get_settings()
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    logger.info("Driver safety API started")
    yield
    logger.info("Stopping monitoring service")
    monitoring_service.stop()
    logger.info("Driver safety API stopped")


app = FastAPI(title="Driver Safety API", version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.frontend_url,
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://[::1]:5173",
    ],
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1|\[::1\]):5173",
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)
app.include_router(api_router)
app.include_router(websocket_router)


@app.get("/api/status")
def status_check() -> dict[str, str]:
    return {"status": "ready", "service": "driver-safety-api", "database": "sqlite", "websocket": "available"}


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "Driver Safety System API is running."}
