"""
backend/main.py
────────────────
FastAPI application entry point.
Registers all routes and startup checks.

Run: uvicorn backend.main:app --reload --port 8000
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from backend.database.connection import check_connection
from backend.routes import stream, alerts, hotspots

app = FastAPI(
    title="SIH1605 Women Safety Analytics API",
    description="Real-time CCTV analytics backend for threat detection.",
    version="1.0.0",
)

# ── CORS (allow React dev server on :5173) ────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routes ────────────────────────────────────────────────────────────────────
app.include_router(stream.router)
app.include_router(alerts.router)
app.include_router(hotspots.router)


@app.on_event("startup")
async def startup():
    logger.info("Starting SIH1605 backend...")
    if check_connection():
        logger.info("Database: ✓ Connected")
    else:
        logger.warning("Database: ✗ Not connected — alerts won't be persisted")


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "SIH1605 Women Safety Analytics"}
