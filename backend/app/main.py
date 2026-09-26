"""
SentinelSIF – FastAPI Main Application Entry Point
==================================================
Wires together CORS middleware, logging configuration, database initialization,
and API routers:
  - GET /health
  - POST /classify
  - POST /upload-report
  - GET /risk-summary
  - GET /alerts
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from dotenv import load_dotenv
load_dotenv()

from .database import Base, engine
from .routes import (
    analytics_router,
    auth_router,
    classify_router,
    health_router,
    reports_router,
)

# ─── Configure Application Logging ───────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("sentinelsif.main")


# ─── Lifespan Context Manager ────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application startup and shutdown lifecycle management.
    Ensures all database tables exist before taking requests.
    """
    logger.info("Initializing SentinelSIF backend...")
    try:
        # Automatically create tables if not present
        Base.metadata.create_all(bind=engine)
        logger.info("Database schema verified / initialized successfully.")
    except Exception as e:
        logger.error(f"Error initializing database schema: {e}", exc_info=True)

    yield

    logger.info("Shutting down SentinelSIF backend.")


# ─── FastAPI Application ──────────────────────────────────────────────────────
app = FastAPI(
    title="SentinelSIF",
    description="SIF (Serious Injury & Fatality) Precursor Detection System API for Oil Industry Workplace Safety",
    version="0.2.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ─── CORS Middleware ──────────────────────────────────────────────────────────
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Register Routers ─────────────────────────────────────────────────────────
app.include_router(health_router)
app.include_router(auth_router)
app.include_router(classify_router)
app.include_router(reports_router)
app.include_router(analytics_router)

@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint providing API information and documentation links.
    """
    return {
        "service": "SentinelSIF API",
        "status": "online",
        "docs": "/docs",
        "health": "/health",
        "endpoints": [
            "POST /classify",
            "POST /upload-report",
            "GET /risk-summary",
            "GET /alerts",
        ],
    }
