"""Durable PostgreSQL persistence for runs and reviewer feedback."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import select

from app.db.models import FeedbackRecord, RunRecord, get_session_factory
from app.core.logging import get_logger

log = get_logger(__name__)


async def create_run_record(
    *,
    run_id: str,
    request_id: str,
    correlation_id: str,
    admission_type: str,
    prompt_version: str,
    request_payload: dict[str, Any],
) -> None:
    """Create the durable pending row before a Celery task is enqueued."""
    session_factory = get_session_factory()
    async with session_factory() as session:
        session.add(
            RunRecord(
                id=run_id,
                request_id=request_id,
                correlation_id=correlation_id,
                status="pending",
                admission_type=admission_type,
                prompt_version=prompt_version,
                request_payload=request_payload,
            )
        )
        await session.commit()


async def update_run_record(run_id: str, **fields: Any) -> bool:
    """Update a run without making database availability break the live path."""
    session_factory = get_session_factory()
    async with session_factory() as session:
        run = await session.get(RunRecord, run_id)
        if run is None:
            log.warning("run_record_not_found", run_id=run_id)
            return False

        allowed = {
            "status",
            "outcome",
            "recommendation",
            "escalation_reason",
            "prompt_version",
            "processing_time_ms",
            "citations",
            "agent_steps",
            "token_usage",
            "completed_at",
        }
        for field, value in fields.items():
            if field in allowed:
                setattr(run, field, value)
        await session.commit()
        return True


async def get_run_record(run_id: str) -> dict[str, Any] | None:
    """Load a durable run so status polling can survive Redis expiry."""
    session_factory = get_session_factory()
    async with session_factory() as session:
        run = await session.get(RunRecord, run_id)
        if run is None:
            return None
        return {
            "run_id": run.id,
            "request_id": run.request_id,
            "status": run.status,
            "outcome": run.outcome,
            "recommendation": run.recommendation,
            "escalation_reason": run.escalation_reason,
            "admission_type_classified": run.admission_type,
            "prompt_version": run.prompt_version,
            "processing_time_ms": run.processing_time_ms,
            "citations": run.citations or [],
            "step_logs": run.agent_steps or [],
            "token_usage": run.token_usage or {},
            "correlation_id": run.correlation_id or "",
            "created_at": run.created_at,
            "completed_at": run.completed_at,
        }


async def upsert_feedback(
    *,
    run_id: str,
    satisfactory: bool,
    reason: str | None,
    reviewer_id: str | None,
    submitted_at: datetime,
) -> bool:
    """Persist feedback for a known run, updating an existing review if needed."""
    session_factory = get_session_factory()
    async with session_factory() as session:
        run = await session.get(RunRecord, run_id)
        if run is None:
            return False

        result = await session.execute(
            select(FeedbackRecord).where(FeedbackRecord.run_id == run_id)
        )
        feedback = result.scalar_one_or_none()
        if feedback is None:
            feedback = FeedbackRecord(run_id=run_id)
            session.add(feedback)

        feedback.satisfactory = satisfactory
        feedback.reason = reason
        feedback.reviewer_id = reviewer_id
        feedback.submitted_at = submitted_at
        await session.commit()
        return True
