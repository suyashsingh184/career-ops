from __future__ import annotations

import random
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import timedelta
from threading import Lock
from typing import Callable, Deque, Generic, Optional, TypeVar

from app.config import get_settings
from app.exceptions import CareerOpsError, CircuitBreakerOpenError
from app.utils.dates import utcnow

T = TypeVar("T")


@dataclass
class RetryPolicy:
    max_attempts: int
    backoff_base_seconds: float
    jitter_seconds: float


@dataclass
class CircuitBreakerState:
    opened_until_epoch: float | None = None
    failures: Deque[float] | None = None

    def __post_init__(self) -> None:
        if self.failures is None:
            self.failures = deque()


class CircuitBreakerRegistry:
    def __init__(self) -> None:
        self._states: dict[str, CircuitBreakerState] = {}
        self._lock = Lock()

    def _state_for(self, key: str) -> CircuitBreakerState:
        with self._lock:
            return self._states.setdefault(key, CircuitBreakerState())

    def is_open(self, key: str) -> bool:
        state = self._state_for(key)
        return bool(state.opened_until_epoch and state.opened_until_epoch > time.time())

    def record_failure(self, key: str) -> bool:
        settings = get_settings()
        state = self._state_for(key)
        now = time.time()
        state.failures.append(now)
        window_start = now - timedelta(minutes=settings.circuit_breaker_window_minutes).total_seconds()
        while state.failures and state.failures[0] < window_start:
            state.failures.popleft()
        if len(state.failures) >= settings.circuit_breaker_threshold:
            state.opened_until_epoch = now + timedelta(minutes=settings.circuit_breaker_cooldown_minutes).total_seconds()
            return True
        return False

    def record_success(self, key: str) -> bool:
        state = self._state_for(key)
        was_open = self.is_open(key)
        state.failures.clear()
        state.opened_until_epoch = None
        return was_open

    def snapshot(self) -> dict[str, dict[str, object]]:
        result: dict[str, dict[str, object]] = {}
        for key, state in self._states.items():
            result[key] = {
                "open": self.is_open(key),
                "failure_count": len(state.failures or ()),
                "opened_until": state.opened_until_epoch,
            }
        return result


class SourceRateLimiter:
    def __init__(self) -> None:
        self._last_call_by_source: dict[str, float] = defaultdict(float)
        self._lock = Lock()

    def wait(self, source: str, per_second: float) -> None:
        if per_second <= 0:
            return
        min_interval = 1.0 / per_second
        with self._lock:
            elapsed = time.time() - self._last_call_by_source[source]
            if elapsed < min_interval:
                time.sleep(min_interval - elapsed)
            self._last_call_by_source[source] = time.time()


CIRCUIT_BREAKERS = CircuitBreakerRegistry()
RATE_LIMITER = SourceRateLimiter()


def default_retry_policy() -> RetryPolicy:
    settings = get_settings()
    return RetryPolicy(
        max_attempts=settings.retry_max_attempts,
        backoff_base_seconds=settings.retry_backoff_base,
        jitter_seconds=settings.retry_jitter,
    )


def classify_retryable_error(error: Exception) -> bool:
    if isinstance(error, CareerOpsError):
        return error.retryable
    return False


def run_with_retry(
    operation: Callable[[], T],
    *,
    source_key: Optional[str] = None,
    retry_policy: Optional[RetryPolicy] = None,
    retryable: Optional[Callable[[Exception], bool]] = None,
    on_retry: Optional[Callable[[int, Exception], None]] = None,
    on_exhausted: Optional[Callable[[Exception], None]] = None,
    on_circuit_open: Optional[Callable[[str], None]] = None,
    on_circuit_close: Optional[Callable[[str], None]] = None,
) -> T:
    policy = retry_policy or default_retry_policy()
    should_retry = retryable or classify_retryable_error
    if source_key and CIRCUIT_BREAKERS.is_open(source_key):
        if on_circuit_open:
            on_circuit_open(source_key)
        raise CircuitBreakerOpenError(f"Circuit breaker open for source '{source_key}'")

    attempt = 0
    while True:
        attempt += 1
        try:
            result = operation()
            if source_key:
                was_open = CIRCUIT_BREAKERS.record_success(source_key)
                if was_open and on_circuit_close:
                    on_circuit_close(source_key)
            return result
        except Exception as exc:
            if source_key:
                opened = CIRCUIT_BREAKERS.record_failure(source_key)
                if opened and on_circuit_open:
                    on_circuit_open(source_key)
            if attempt >= policy.max_attempts or not should_retry(exc):
                if on_exhausted:
                    on_exhausted(exc)
                raise
            if on_retry:
                on_retry(attempt, exc)
            sleep_for = policy.backoff_base_seconds * (2 ** (attempt - 1)) + random.uniform(0.0, policy.jitter_seconds)
            time.sleep(sleep_for)
