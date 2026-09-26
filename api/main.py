"""
FastAPI Backend Application Entry Point for Gistly / Jitsly.
Architecture:
  Streamlit UI / External Clients
             ↓ HTTP (REST)
       FastAPI Backend (/api/v1)
             ↓ Dependency Injection
    Core Subsystems & LangGraph Workflow
"""

import time
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI, Request, status, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError

from core.logger import get_logger
from core.config import CORS_ORIGINS, API_HOST, API_PORT
from core.session_store import DEFAULT_SESSION_STORE
from api.routes import (
    health_router,
    meetings_router,
    chat_router,
    actions_router,
    voice_router,
)
from api.schemas.common import ErrorResponse

logger = get_logger("gistly.api")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan management for initialization and clean shutdown."""
    logger.info("Initializing Gistly FastAPI backend service...")
    # Optional pre-warming or diagnostic check
    yield
    logger.info("Shutting down Gistly FastAPI backend service...")


app = FastAPI(
    title="Gistly AI Meeting & Video Intelligence API",
    description=(
        "Production-grade REST API layer for Gistly. "
        "Provides endpoints for meeting ingestion, multilingual transcription, "
        "executive summarization, structured intelligence extraction, "
        "LangGraph-orchestrated grounded chat, and MCP-controlled actions."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# ─── CORS Middleware ─────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS if CORS_ORIGINS else ["http://localhost:8501"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


# ─── Global Error Handlers ──────────────────────────────────────────────────────
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Clean JSON envelope for standard HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "status_code": exc.status_code},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Clean JSON envelope for Pydantic schema validation failures."""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Request validation failed.",
            "status_code": status.HTTP_422_UNPROCESSABLE_ENTITY,
            "detail": exc.errors(),
        },
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """Catch-all unhandled exception handler: logs internally without leaking secrets."""
    logger.exception("Unhandled server exception processing %s %s", request.method, request.url)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "An internal server error occurred while processing the request.",
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
        },
    )


# ─── Root Endpoint ──────────────────────────────────────────────────────────────
@app.get(
    "/",
    tags=["Root"],
    summary="API Root Information",
)
def read_root():
    return {
        "service": "gistly-api",
        "version": "1.0.0",
        "docs_url": "/docs",
        "api_v1_prefix": "/api/v1",
        "status": "online",
    }


# ─── Route Registration (/api/v1) ───────────────────────────────────────────────
API_V1_PREFIX = "/api/v1"
app.include_router(health_router, prefix=API_V1_PREFIX)
app.include_router(meetings_router, prefix=API_V1_PREFIX)
app.include_router(chat_router, prefix=API_V1_PREFIX)
app.include_router(actions_router, prefix=API_V1_PREFIX)
app.include_router(voice_router, prefix=API_V1_PREFIX)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.main:app", host=API_HOST, port=API_PORT, reload=True)
