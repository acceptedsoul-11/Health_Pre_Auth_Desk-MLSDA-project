"""
Redis cache service — shared caching for embeddings, retrieval results, and full runs.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any

import redis

from app.core.config import get_settings
from app.core.logging import get_logger

log = get_logger(__name__)
settings = get_settings()

_redis_client: redis.Redis | None = None


def get_redis() -> redis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.Redis.from_url(
            settings.redis_url,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
        )
    return _redis_client


def _cache_key(prefix: str, payload: str) -> str:
    h = hashlib.sha256(payload.encode()).hexdigest()[:24]
    return f"preauth:{prefix}:{h}"


def cache_get(prefix: str, payload: str) -> Any | None:
    try:
        r = get_redis()
        val = r.get(_cache_key(prefix, payload))
        if val:
            log.debug("cache_hit", prefix=prefix)
            return json.loads(val)
    except Exception as e:
        log.warning("cache_get_error", error=str(e))
    return None


def cache_set(prefix: str, payload: str, value: Any, ttl_s: int) -> None:
    try:
        r = get_redis()
        r.setex(_cache_key(prefix, payload), ttl_s, json.dumps(value, default=str))
        log.debug("cache_set", prefix=prefix, ttl_s=ttl_s)
    except Exception as e:
        log.warning("cache_set_error", error=str(e))


def get_run_result(run_id: str) -> dict | None:
    try:
        r = get_redis()
        raw = r.get(f"preauth:result:{run_id}")
        if raw:
            data = json.loads(raw)
            return data.get("result", data)
    except Exception as e:
        log.warning("get_run_result_error", error=str(e))
    return None


def set_run_status(run_id: str, status: str, extra: dict | None = None) -> None:
    try:
        r = get_redis()
        payload = {"run_id": run_id, "status": status, **(extra or {})}
        r.setex(f"preauth:status:{run_id}", 86400, json.dumps(payload, default=str))
    except Exception as e:
        log.warning("set_run_status_error", error=str(e))


def get_all_demo_runs() -> list[dict]:
    """Return all seeded DEMO-* runs for the dashboard."""
    try:
        r = get_redis()
        keys = r.keys("preauth:result:DEMO-*")
        results = []
        for key in sorted(keys):
            raw = r.get(key)
            if raw:
                data = json.loads(raw)
                result = data.get("result", data)
                results.append(result)
        return results
    except Exception as e:
        log.warning("get_all_demo_runs_error", error=str(e))
        return []
