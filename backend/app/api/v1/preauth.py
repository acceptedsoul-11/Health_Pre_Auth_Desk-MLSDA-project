"""
Pre-Authorization API Router (F1, D1).
Endpoints:
  POST /api/v1/preauth        — Submit a pre-auth request
  GET  /api/v1/preauth/{run_id} — Poll status
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime
from typing import Any

import redis
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.core.guardrails import run_all_input_guardrails
from app.core.logging import get_logger, get_correlation_id
from app.core.metrics import runs_submitted_total, queue_depth
from app.services.persistence import create_run_record, get_run_record
from app.schemas.preauth import (
    PreAuthRequest,
    PreAuthSubmitResponse,
    PreAuthResponse,
    QuarantineRecord,
    RunStatus,
    OutcomeRoute,
    AdmissionType,
    ClauseCitation,
    AgentStepLog,
    TokenUsage,
)

router = APIRouter()
settings = get_settings()
log = get_logger(__name__)


def get_redis() -> redis.Redis:
    return redis.Redis.from_url(settings.redis_url, decode_responses=True)


def get_celery():
    from workers.tasks import celery_app
    return celery_app


# ── Rate Limiting ─────────────────────────────────────────────────────────────

async def check_rate_limit(request: Request) -> None:
    """Simple Redis-backed sliding window rate limiter."""
    client_ip = request.client.host if request.client else "unknown"
    r = get_redis()
    key = f"ratelimit:{client_ip}:min"
    count = r.incr(key)
    if count == 1:
        r.expire(key, 60)
    if count > settings.rate_limit_per_minute:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": "rate_limit_exceeded",
                "message": f"Max {settings.rate_limit_per_minute} requests per minute",
                "retry_after": 60,
            },
        )


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post(
    "/preauth",
    response_model=PreAuthSubmitResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Submit a pre-authorization request",
    description=(
        "Validates the request payload, runs guardrail checks, then submits "
        "the pre-authorization to the async agent pipeline. Returns a run_id "
        "immediately for status polling."
    ),
)
async def submit_preauth(
    payload: PreAuthRequest,
    request: Request,
    _rate: None = Depends(check_rate_limit),
) -> PreAuthSubmitResponse:
    correlation_id = get_correlation_id()
    run_id = f"RUN-{uuid.uuid4().hex[:16].upper()}"

    log.info(
        "preauth_submitted",
        run_id=run_id,
        request_id=payload.request_id,
        admission_type=payload.medical.admission_type,
        procedure=payload.medical.procedure_name,
        policy_age_months=payload.policy.policy_age_months,
    )

    # ── Guardrail check on free-text fields ──────────────────────────────────
    guardrail_result = run_all_input_guardrails(payload.free_text_notes)
    if not guardrail_result.passed:
        # Quarantine the request
        quarantine = QuarantineRecord(
            request_id=payload.request_id,
            validation_errors=[{"field": "free_text_notes", "violations": guardrail_result.violations}],
            raw_payload=payload.model_dump(mode="json"),
            correlation_id=correlation_id,
        )
        _persist_quarantine(quarantine)
        log.warning(
            "request_quarantined_guardrails",
            run_id=run_id,
            violations=guardrail_result.violations,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "guardrail_violation",
                "message": "Request rejected by input guardrails",
                "violations": guardrail_result.violations,
                "quarantine_id": payload.request_id,
            },
        )

    # ── Build request context for agent ─────────────────────────────────────
    request_context = {
        "request_id": payload.request_id,
        "patient": payload.patient.model_dump(mode="json"),
        "policy": payload.policy.model_dump(mode="json"),
        "hospital": payload.hospital.model_dump(mode="json"),
        "medical": payload.medical.model_dump(mode="json"),
        "policy_age_months": payload.policy.policy_age_months,
        "free_text_notes": payload.free_text_notes,
    }

    # PostgreSQL is the durable run history. Redis remains the fast status and
    # queue store. Persistence is best-effort so a temporary database outage
    # does not prevent the live pre-authorization pipeline from running.
    try:
        await create_run_record(
            run_id=run_id,
            request_id=payload.request_id,
            correlation_id=correlation_id,
            admission_type=payload.medical.admission_type.value,
            prompt_version=settings.active_prompt_version,
            request_payload=request_context,
        )
    except Exception as exc:
        log.warning("run_record_create_failed_continuing", run_id=run_id, error=str(exc))

    # ── Store initial status in Redis ────────────────────────────────────────
    r = get_redis()
    r.setex(
        f"preauth:status:{run_id}",
        86400,
        json.dumps({
            "run_id": run_id,
            "request_id": payload.request_id,
            "status": "pending",
            "correlation_id": correlation_id,
            "submitted_at": payload.submitted_at.isoformat(),
        }),
    )

    # ── Enqueue Celery task ──────────────────────────────────────────────────
    from workers.tasks import run_preauth
    task = run_preauth.apply_async(
        kwargs={
            "run_id": run_id,
            "request_context": request_context,
            "correlation_id": correlation_id,
            "prompt_version": settings.active_prompt_version,
        },
        task_id=run_id,
        queue="preauth",
    )

    # Update metrics
    runs_submitted_total.labels(
        admission_type=payload.medical.admission_type.value
    ).inc()

    # Update queue depth
    try:
        from workers.tasks import celery_app
        inspect = celery_app.control.inspect()
        q_len = len(inspect.active() or {})
        queue_depth.set(q_len)
    except Exception:
        pass

    poll_url = f"/api/v1/preauth/{run_id}"
    return PreAuthSubmitResponse(
        run_id=run_id,
        status=RunStatus.PENDING,
        poll_url=poll_url,
        estimated_wait_s=30,
        correlation_id=correlation_id,
    )


@router.get(
    "/preauth/{run_id}",
    response_model=PreAuthResponse,
    summary="Get pre-authorization run status and result",
)
async def get_preauth_status(run_id: str) -> PreAuthResponse:
    r = get_redis()
    correlation_id = get_correlation_id()

    # Check result store first (completed runs)
    result_raw = r.get(f"preauth:result:{run_id}")
    if result_raw:
        result_data = json.loads(result_raw)
        run_result = result_data.get("result", {})
        return _build_preauth_response(run_id, run_result, correlation_id)

    # Check status store
    status_raw = r.get(f"preauth:status:{run_id}")
    if status_raw:
        status_data = json.loads(status_raw)
        current_status = status_data.get("status", "unknown")
        return PreAuthResponse(
            run_id=run_id,
            request_id=status_data.get("request_id", ""),
            status=RunStatus(current_status) if current_status in [s.value for s in RunStatus] else RunStatus.PENDING,
            correlation_id=correlation_id,
        )

    # Redis results have a TTL. Fall back to PostgreSQL so a run remains
    # reconstructible after the fast cache expires.
    try:
        db_record = await get_run_record(run_id)
    except Exception as exc:
        log.warning("run_record_lookup_failed", run_id=run_id, error=str(exc))
        db_record = None

    if db_record:
        current_status = db_record.get("status", "pending")
        if current_status in (RunStatus.COMPLETED.value, RunStatus.FAILED.value):
            return _build_preauth_response(run_id, db_record, correlation_id)
        return PreAuthResponse(
            run_id=run_id,
            request_id=db_record.get("request_id", ""),
            status=RunStatus(current_status) if current_status in [s.value for s in RunStatus] else RunStatus.PENDING,
            correlation_id=correlation_id,
        )

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail={"error": "run_not_found", "run_id": run_id},
    )


def _build_preauth_response(
    run_id: str, result: dict, correlation_id: str
) -> PreAuthResponse:
    """Convert stored result dict to PreAuthResponse schema."""
    citations = [
        ClauseCitation(**c) if isinstance(c, dict) else c
        for c in result.get("citations", [])
    ]
    step_logs = [
        AgentStepLog(**s) if isinstance(s, dict) else s
        for s in result.get("step_logs", [])
    ]
    token_usage_data = result.get("token_usage", {})
    token_usage = TokenUsage(**token_usage_data) if isinstance(token_usage_data, dict) else TokenUsage()

    outcome_str = result.get("outcome")
    outcome = None
    if outcome_str:
        try:
            outcome = OutcomeRoute(outcome_str)
        except ValueError:
            outcome = OutcomeRoute.MEDICAL_REVIEW

    admission_str = result.get("admission_type_classified")
    admission_type = None
    if admission_str:
        try:
            admission_type = AdmissionType(admission_str)
        except ValueError:
            pass

    stored_status = result.get("status")
    if stored_status in [s.value for s in RunStatus]:
        response_status = RunStatus(stored_status)
    else:
        response_status = RunStatus.COMPLETED if outcome else RunStatus.FAILED

    return PreAuthResponse(
        run_id=run_id,
        request_id=result.get("request_id", ""),
        status=response_status,
        outcome=outcome,
        recommendation=result.get("recommendation"),
        citations=citations,
        escalation_reason=result.get("escalation_reason"),
        admission_type_classified=admission_type,
        agent_steps=step_logs,
        token_usage=token_usage,
        prompt_version=result.get("prompt_version", "v1"),
        correlation_id=correlation_id,
        processing_time_ms=result.get("processing_time_ms"),
        created_at=result.get("created_at") or datetime.utcnow(),
        completed_at=result.get("completed_at"),
    )


def _persist_quarantine(record: QuarantineRecord) -> None:
    """Store quarantine record in Redis."""
    r = get_redis()
    r.setex(
        f"preauth:quarantine:{record.request_id}",
        86400 * 7,  # keep for 7 days
        json.dumps(record.model_dump(mode="json")),
    )
    log.warning(
        "quarantine_record_stored",
        request_id=record.request_id,
        error_count=len(record.validation_errors),
    )
