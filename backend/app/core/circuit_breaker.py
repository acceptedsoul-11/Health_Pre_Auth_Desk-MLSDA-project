"""
Circuit Breaker implementation for the LLM provider.
States: CLOSED → OPEN → HALF-OPEN → CLOSED
"""
from __future__ import annotations

import asyncio
import time
from enum import Enum
from typing import Any, Callable, TypeVar

from app.core.config import get_settings
from app.core.logging import get_logger

log = get_logger(__name__)

F = TypeVar("F")


class CBState(str, Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreakerOpen(Exception):
    """Raised when a call is attempted while the circuit is OPEN."""


class CircuitBreaker:
    def __init__(
        self,
        name: str,
        failure_threshold: int | None = None,
        recovery_timeout_s: int | None = None,
        half_open_calls: int | None = None,
    ) -> None:
        s = get_settings()
        self.name = name
        self.failure_threshold = failure_threshold or s.cb_failure_threshold
        self.recovery_timeout_s = recovery_timeout_s or s.cb_recovery_timeout_s
        self.half_open_max = half_open_calls or s.cb_half_open_calls

        self._state = CBState.CLOSED
        self._failures = 0
        self._opened_at: float = 0.0
        self._half_open_successes = 0
        self._lock = asyncio.Lock()

    @property
    def state(self) -> CBState:
        return self._state

    async def _try_recover(self) -> None:
        async with self._lock:
            if self._state == CBState.OPEN:
                elapsed = time.monotonic() - self._opened_at
                if elapsed >= self.recovery_timeout_s:
                    self._state = CBState.HALF_OPEN
                    self._half_open_successes = 0
                    log.info("circuit_breaker_half_open", name=self.name)

    async def call(self, fn: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        await self._try_recover()

        async with self._lock:
            if self._state == CBState.OPEN:
                raise CircuitBreakerOpen(
                    f"Circuit breaker '{self.name}' is OPEN. "
                    f"Retry after {self.recovery_timeout_s}s."
                )

        try:
            result = await fn(*args, **kwargs)
            await self._on_success()
            return result
        except CircuitBreakerOpen:
            raise
        except Exception as exc:
            await self._on_failure(exc)
            raise

    async def _on_success(self) -> None:
        async with self._lock:
            if self._state == CBState.HALF_OPEN:
                self._half_open_successes += 1
                if self._half_open_successes >= self.half_open_max:
                    self._state = CBState.CLOSED
                    self._failures = 0
                    log.info("circuit_breaker_closed", name=self.name)

    async def _on_failure(self, exc: Exception) -> None:
        async with self._lock:
            self._failures += 1
            log.warning(
                "circuit_breaker_failure",
                name=self.name,
                failures=self._failures,
                error=str(exc),
            )
            if self._failures >= self.failure_threshold:
                self._state = CBState.OPEN
                self._opened_at = time.monotonic()
                log.error("circuit_breaker_open", name=self.name)


# ── Module-level singleton ───────────────────────────────────────────────────
_breakers: dict[str, CircuitBreaker] = {}


def get_circuit_breaker(name: str) -> CircuitBreaker:
    if name not in _breakers:
        _breakers[name] = CircuitBreaker(name)
    return _breakers[name]
