"""
Celery application and task definitions for async pre-authorization processing.
Implements: async queuing, result persistence, fault tolerance with retries.
"""
from __future__ import annotations

import asyncio
import time
import uuid
from datetime import datetime, timezone
from typing import Any

from celery import Celery
from celery.signals import worker_ready, worker_shutdown
from celery.utils.log import get_task_logger

from app.core.config import get_settings

settings = get_settings()
logger = get_task_logger(__name__)

# ── Celery App ────────────────────────────────────────────────────────────────

celery_app = Celery(
    "preauth_worker",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,  # Fair distribution for long tasks
    task_reject_on_worker_lost=True,
    broker_connection_retry_on_startup=True,
    result_expires=86400,  # Results expire after 24h
    worker_max_tasks_per_child=settings.celery_max_tasks_per_child,
    task_soft_time_limit=settings.agent_wall_clock_timeout_s + 30,
    task_time_limit=settings.agent_wall_clock_timeout_s + 60,
    # Routing
    task_routes={
        "workers.tasks.run_preauth": {"queue": "preauth"},
        "workers.tasks.run_evaluation": {"queue": "eval"},
    },
)


@worker_ready.connect
def on_worker_ready(**kwargs: Any) -> None:
    logger.info("Celery worker ready — Pre-Authorization Desk")


@worker_shutdown.connect
def on_worker_shutdown(**kwargs: Any) -> None:
    logger.info("Celery worker shutting down gracefully")


# ── Database persistence helper ───────────────────────────────────────────────

def _persist_result(run_id: str, result: dict[str, Any], status: str) -> None:
    """Persist the fast-polling result copy to Redis."""
    import json
    import redis as redis_lib

    r = redis_lib.Redis.from_url(settings.redis_url, decode_responses=True)
    key = f"preauth:result:{run_id}"
    r.setex(
        key,
        settings.cache_full_run_ttl_s * 4,  # keep results longer
        json.dumps({
            "run_id": run_id,
            "status": status,
            "result": result,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }),
    )


def _update_status(run_id: str, status: str) -> None:
    """Update run status in Redis."""
    import json
    import redis as redis_lib

    r = redis_lib.Redis.from_url(settings.redis_url, decode_responses=True)
    status_key = f"preauth:status:{run_id}"
    existing_raw = r.get(status_key)
    if existing_raw:
        existing = json.loads(existing_raw)
    else:
        existing = {}
    existing["status"] = status
    existing["updated_at"] = datetime.now(timezone.utc).isoformat()
    r.setex(status_key, 86400, json.dumps(existing))


def _update_db_run(loop: asyncio.AbstractEventLoop, run_id: str, **fields: Any) -> None:
    """Best-effort durable update; Redis still carries the live task state."""
    try:
        from app.services.persistence import update_run_record

        loop.run_until_complete(update_run_record(run_id, **fields))
    except Exception as exc:
        logger.warning(f"[{run_id}] PostgreSQL run update failed: {exc}")


# ── Main Task ─────────────────────────────────────────────────────────────────

@celery_app.task(
    bind=True,
    name="workers.tasks.run_preauth",
    max_retries=3,
    default_retry_delay=5,
    acks_late=True,
)
def run_preauth(
    self: Any,
    run_id: str,
    request_context: dict[str, Any],
    correlation_id: str,
    prompt_version: str = "v1",
) -> dict[str, Any]:
    """
    Async pre-authorization task.
    Runs the LangGraph pipeline and persists the result.
    """
    from app.core.logging import configure_logging, set_correlation_id, set_run_id
    configure_logging()
    set_correlation_id(correlation_id)
    set_run_id(run_id)

    logger.info(f"[{run_id}] Starting pre-auth pipeline")
    t0 = time.monotonic()

    _update_status(run_id, "processing")

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    _update_db_run(loop, run_id, status="processing")

    try:
        from app.agents.pipeline import run_preauth_pipeline

        # Run async pipeline in sync context
        result = loop.run_until_complete(
            run_preauth_pipeline(
                request_context=request_context,
                run_id=run_id,
                correlation_id=correlation_id,
                prompt_version=prompt_version,
            )
        )

        elapsed_ms = (time.monotonic() - t0) * 1000
        result["processing_time_ms"] = round(elapsed_ms, 1)
        result["run_id"] = run_id
        result["correlation_id"] = correlation_id
        result["completed_at"] = datetime.now(timezone.utc).isoformat()

        _persist_result(run_id, result, "completed")
        _update_db_run(
            loop,
            run_id,
            status="completed",
            outcome=result.get("outcome"),
            recommendation=result.get("recommendation"),
            escalation_reason=result.get("escalation_reason"),
            prompt_version=result.get("prompt_version", prompt_version),
            processing_time_ms=result.get("processing_time_ms"),
            citations=result.get("citations", []),
            agent_steps=result.get("step_logs", []),
            token_usage=result.get("token_usage", {}),
            completed_at=datetime.now(timezone.utc),
        )
        logger.info(
            f"[{run_id}] Pipeline completed in {elapsed_ms:.0f}ms — "
            f"outcome: {result.get('outcome')}"
        )
        return result

    except Exception as exc:
        logger.error(f"[{run_id}] Pipeline failed: {exc}")
        _update_status(run_id, "failed")
        _update_db_run(loop, run_id, status="failed")

        # Retry with exponential backoff
        try:
            raise self.retry(
                exc=exc,
                countdown=2 ** self.request.retries,
            )
        except self.MaxRetriesExceededError:
            error_result = {
                "run_id": run_id,
                "status": "failed",
                "outcome": "medical-review",
                "recommendation": f"Processing failed after {self.max_retries} retries. Escalated to medical review.",
                "escalation_reason": str(exc),
                "citations": [],
                "error": str(exc),
            }
            _persist_result(run_id, error_result, "failed")
            _update_db_run(
                loop,
                run_id,
                status="failed",
                outcome=error_result["outcome"],
                recommendation=error_result["recommendation"],
                escalation_reason=error_result["escalation_reason"],
                citations=[],
                agent_steps=[],
                token_usage={},
                completed_at=datetime.now(timezone.utc),
            )
            return error_result
    finally:
        loop.close()


@celery_app.task(
    name="workers.tasks.run_evaluation",
    max_retries=1,
)
def run_evaluation(scenario_batch: list[dict[str, Any]]) -> dict[str, Any]:
    """Run a batch of evaluation scenarios."""
    from app.cli.evaluate import run_batch_evaluation

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(run_batch_evaluation(scenario_batch))
    finally:
        loop.close()
