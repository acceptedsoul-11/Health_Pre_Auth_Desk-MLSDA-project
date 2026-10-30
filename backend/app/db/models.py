"""
SQLAlchemy database models for persistent storage.
Stores run results, feedback, and quarantine records.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean, Column, DateTime, Float, Integer,
    JSON, String, Text, ForeignKey
)
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, relationship

from app.core.config import get_settings


class Base(AsyncAttrs, DeclarativeBase):
    pass


class RunRecord(Base):
    __tablename__ = "preauth_runs"

    id = Column(String(64), primary_key=True, default=lambda: f"RUN-{uuid.uuid4().hex[:16].upper()}")
    request_id = Column(String(64), nullable=False, index=True)
    correlation_id = Column(String(64), nullable=True)
    status = Column(String(20), nullable=False, default="pending")
    outcome = Column(String(30), nullable=True)
    recommendation = Column(Text, nullable=True)
    escalation_reason = Column(Text, nullable=True)
    admission_type = Column(String(30), nullable=True)
    prompt_version = Column(String(10), nullable=False, default="v1")
    processing_time_ms = Column(Float, nullable=True)
    citations = Column(JSON, nullable=True, default=list)
    agent_steps = Column(JSON, nullable=True, default=list)
    token_usage = Column(JSON, nullable=True, default=dict)
    request_payload = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime(timezone=True), nullable=True)

    feedback = relationship("FeedbackRecord", back_populates="run", uselist=False)


class FeedbackRecord(Base):
    __tablename__ = "preauth_feedback"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(String(64), ForeignKey("preauth_runs.id"), nullable=False, index=True)
    satisfactory = Column(Boolean, nullable=False)
    reason = Column(Text, nullable=True)
    reviewer_id = Column(String(100), nullable=True)
    submitted_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    run = relationship("RunRecord", back_populates="feedback")


class QuarantineRecord(Base):
    __tablename__ = "preauth_quarantine"

    id = Column(Integer, primary_key=True, autoincrement=True)
    request_id = Column(String(64), nullable=False, index=True)
    correlation_id = Column(String(64), nullable=True)
    validation_errors = Column(JSON, nullable=False)
    raw_payload = Column(JSON, nullable=True)
    quarantined_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class EvalResult(Base):
    __tablename__ = "eval_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    scenario_id = Column(String(64), nullable=False, index=True)
    prompt_version = Column(String(10), nullable=False)
    expected_outcome = Column(String(30), nullable=False)
    actual_outcome = Column(String(30), nullable=True)
    passed = Column(Boolean, nullable=True)
    citation_match = Column(Boolean, nullable=True)
    groundedness = Column(Float, nullable=True)
    faithfulness = Column(Float, nullable=True)
    context_relevance = Column(Float, nullable=True)
    processing_time_ms = Column(Float, nullable=True)
    evaluated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


# ── Database engine factory ───────────────────────────────────────────────────

_engine = None
_session_factory = None


def get_engine():
    global _engine
    if _engine is None:
        settings = get_settings()
        _engine = create_async_engine(
            settings.database_url,
            echo=settings.app_env == "development",
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=10,
        )
    return _engine


def get_session_factory():
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(
            bind=get_engine(), expire_on_commit=False
        )
    return _session_factory


async def init_db() -> None:
    """Create all tables (idempotent)."""
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
