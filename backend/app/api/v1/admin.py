"""
Admin API Router — system metrics, corpus info, quarantine management.
"""
from __future__ import annotations

import json
from pathlib import Path

import redis
from fastapi import APIRouter, HTTPException, status

from app.core.config import get_settings
from app.core.logging import get_logger

router = APIRouter()
settings = get_settings()
log = get_logger(__name__)


def get_redis() -> redis.Redis:
    return redis.Redis.from_url(settings.redis_url, decode_responses=True)


@router.get("/corpus-metadata", summary="Get vector store build metadata")
async def get_corpus_metadata() -> dict:
    meta_path = Path(settings.vector_store_path) / "metadata.json"
    if not meta_path.exists():
        return {"status": "index_not_built", "message": "Run the ingestion CLI first"}
    with open(meta_path) as f:
        return json.load(f)


@router.get("/circuit-breaker-status", summary="Get circuit breaker states")
async def get_circuit_breaker_status() -> dict:
    from app.core.circuit_breaker import _breakers
    return {
        name: {
            "state": cb.state.value,
            "failures": cb._failures,
        }
        for name, cb in _breakers.items()
    }


@router.get("/quarantine", summary="List quarantined requests")
async def list_quarantine() -> dict:
    r = get_redis()
    keys = r.keys("preauth:quarantine:*")
    records = []
    for key in keys[:50]:  # limit to 50
        raw = r.get(key)
        if raw:
            records.append(json.loads(raw))
    return {"count": len(records), "records": records}


@router.delete("/circuit-breaker/{name}/reset", summary="Reset a circuit breaker")
async def reset_circuit_breaker(name: str) -> dict:
    from app.core.circuit_breaker import _breakers, CBState
    if name not in _breakers:
        raise HTTPException(status_code=404, detail=f"Breaker '{name}' not found")
    cb = _breakers[name]
    cb._state = CBState.CLOSED
    cb._failures = 0
    log.info("circuit_breaker_manual_reset", name=name)
    return {"message": f"Circuit breaker '{name}' reset to CLOSED"}
