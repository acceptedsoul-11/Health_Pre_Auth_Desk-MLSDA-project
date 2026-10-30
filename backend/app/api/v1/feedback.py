"""
Feedback API Router (L6).
POST /api/v1/feedback — Submit feedback on a run
GET  /api/v1/feedback/{run_id} — Retrieve feedback for a run
"""
from __future__ import annotations

import json
from datetime import datetime, timezone

import redis
from fastapi import APIRouter, HTTPException, status

from app.core.config import get_settings
from app.core.logging import get_logger
from app.schemas.preauth import FeedbackRequest
from app.services.persistence import upsert_feedback

router = APIRouter()
settings = get_settings()
log = get_logger(__name__)


def get_redis() -> redis.Redis:
    return redis.Redis.from_url(settings.redis_url, decode_responses=True)


@router.post(
    "/feedback",
    status_code=status.HTTP_201_CREATED,
    summary="Submit feedback on a pre-authorization run",
)
async def submit_feedback(payload: FeedbackRequest) -> dict:
    r = get_redis()

    # Verify run exists
    result_exists = r.exists(f"preauth:result:{payload.run_id}")
    status_exists = r.exists(f"preauth:status:{payload.run_id}")
    if not result_exists and not status_exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "run_not_found", "run_id": payload.run_id},
        )

    submitted_at = datetime.now(timezone.utc)
    feedback_record = {
        "run_id": payload.run_id,
        "satisfactory": payload.satisfactory,
        "reason": payload.reason,
        "reviewer_id": payload.reviewer_id,
        "submitted_at": submitted_at.isoformat(),
    }
    r.setex(
        f"preauth:feedback:{payload.run_id}",
        86400 * 30,  # keep for 30 days
        json.dumps(feedback_record),
    )

    try:
        await upsert_feedback(
            run_id=payload.run_id,
            satisfactory=payload.satisfactory,
            reason=payload.reason,
            reviewer_id=payload.reviewer_id,
            submitted_at=submitted_at,
        )
    except Exception as exc:
        log.warning("feedback_database_persist_failed", run_id=payload.run_id, error=str(exc))

    log.info(
        "feedback_submitted",
        run_id=payload.run_id,
        satisfactory=payload.satisfactory,
    )
    return {"message": "Feedback recorded", "run_id": payload.run_id}


@router.get(
    "/feedback/{run_id}",
    summary="Get feedback for a run",
)
async def get_feedback(run_id: str) -> dict:
    r = get_redis()
    fb_raw = r.get(f"preauth:feedback:{run_id}")
    if not fb_raw:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "feedback_not_found", "run_id": run_id},
        )
    return json.loads(fb_raw)
