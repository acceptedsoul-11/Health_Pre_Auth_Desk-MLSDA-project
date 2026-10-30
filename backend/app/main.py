"""
FastAPI application — main entry point.
Implements: REST endpoints, middleware, rate limiting, OTEL tracing, Prometheus metrics.
"""
from __future__ import annotations

import time
import uuid
from contextlib import asynccontextmanager
from typing import Any

import orjson
from fastapi import FastAPI, Request, Response, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator

from app.core.config import get_settings
from app.core.guardrails import run_all_input_guardrails
from app.core.logging import configure_logging, get_logger, set_correlation_id, set_run_id
from app.core.metrics import (
    http_requests_total,
    runs_submitted_total,
    queue_depth,
)
from app.schemas.preauth import (
    FeedbackRequest,
    PreAuthRequest,
    PreAuthSubmitResponse,
    PreAuthResponse,
    QuarantineRecord,
    RunStatus,
)

settings = get_settings()
log = get_logger(__name__)


# ── Lifespan ──────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    log.info("startup", service="preauth-backend", env=settings.app_env)
    # Initialize OTEL tracing
    try:
        from app.core.tracing import setup_tracing
        setup_tracing()
    except Exception as e:
        log.warning("tracing_init_warning", error=str(e))
    # Pre-load vector store on startup
    try:
        from app.services.vector_store import get_vector_store
        store = get_vector_store()
        log.info("vector_store_ready", chunks=store.chunk_count)
    except Exception as e:
        log.warning("vector_store_startup_warning", error=str(e))
    yield
    log.info("shutdown", service="preauth-backend")


# ── App Factory ───────────────────────────────────────────────────────────────

def create_app() -> FastAPI:
    app = FastAPI(
        title="Health Insurance Pre-Authorization Desk",
        description=(
            "Production-grade asynchronous multi-agent microservice for "
            "health insurance pre-authorization using Star Health Insurance Policy corpus."
        ),
        version="1.0.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
        lifespan=lifespan,
    )

    # ── CORS ──────────────────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Prometheus ────────────────────────────────────────────────────────────
    Instrumentator(
        should_group_status_codes=False,
        excluded_handlers=["/healthz", "/metrics"],
    ).instrument(app).expose(app, endpoint="/metrics")

    # ── Correlation ID Middleware ─────────────────────────────────────────────
    @app.middleware("http")
    async def correlation_middleware(request: Request, call_next: Any) -> Response:
        cid = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
        set_correlation_id(cid)
        request.state.correlation_id = cid
        response = await call_next(request)
        response.headers["X-Correlation-ID"] = cid
        return response

    # ── Request Timing Middleware ─────────────────────────────────────────────
    @app.middleware("http")
    async def timing_middleware(request: Request, call_next: Any) -> Response:
        t0 = time.perf_counter()
        response = await call_next(request)
        elapsed = (time.perf_counter() - t0) * 1000
        response.headers["X-Response-Time-Ms"] = f"{elapsed:.1f}"
        return response

    # ── Include Routers ───────────────────────────────────────────────────────
    from app.api.v1 import preauth, feedback, admin, dashboard
    app.include_router(preauth.router, prefix="/api/v1", tags=["Pre-Authorization"])
    app.include_router(feedback.router, prefix="/api/v1", tags=["Feedback"])
    app.include_router(admin.router, prefix="/api/v1/admin", tags=["Admin"])
    app.include_router(dashboard.router, prefix="/api/v1", tags=["Dashboard"])

    # ── Health check ──────────────────────────────────────────────────────────
    @app.get("/healthz", include_in_schema=False)
    async def health() -> dict[str, str]:
        return {"status": "ok", "service": "preauth-backend"}

    @app.get("/readyz", include_in_schema=False)
    async def readiness() -> dict[str, Any]:
        checks: dict[str, Any] = {}
        # Redis check
        try:
            import redis
            r = redis.Redis.from_url(settings.redis_url)
            r.ping()
            checks["redis"] = "ok"
        except Exception as e:
            checks["redis"] = f"error: {e}"
        # PostgreSQL is the durable run-history store for live submissions.
        try:
            from sqlalchemy import text
            from app.db.models import get_engine

            async with get_engine().connect() as conn:
                await conn.execute(text("SELECT 1"))
            checks["postgres"] = "ok"
        except Exception as e:
            checks["postgres"] = f"error: {e}"
        # Vector store check
        try:
            from app.services.vector_store import get_vector_store
            store = get_vector_store()
            checks["vector_store"] = f"ok ({store.chunk_count} chunks)"
        except Exception as e:
            checks["vector_store"] = f"error: {e}"

        all_ok = all(v == "ok" or v.startswith("ok") for v in checks.values())
        return {"status": "ready" if all_ok else "degraded", "checks": checks}

    return app


app = create_app()
