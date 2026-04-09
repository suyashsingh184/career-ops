from __future__ import annotations

import pytest

from app.exceptions import CircuitBreakerOpenError, SourceFetchError
from app.utils.retry import CIRCUIT_BREAKERS, RetryPolicy, run_with_retry


def test_retry_succeeds_after_transient_failures(monkeypatch) -> None:
    attempts = {"count": 0}
    monkeypatch.setattr("time.sleep", lambda _: None)

    def flaky() -> str:
        attempts["count"] += 1
        if attempts["count"] < 3:
            raise SourceFetchError("temporary")
        return "ok"

    result = run_with_retry(flaky, retry_policy=RetryPolicy(max_attempts=3, backoff_base_seconds=0, jitter_seconds=0))
    assert result == "ok"
    assert attempts["count"] == 3


def test_circuit_breaker_opens_after_repeated_failures(monkeypatch) -> None:
    monkeypatch.setattr("time.sleep", lambda _: None)
    key = "unit-test-source"
    CIRCUIT_BREAKERS._states.pop(key, None)

    for _ in range(5):
        with pytest.raises(SourceFetchError):
            run_with_retry(
                lambda: (_ for _ in ()).throw(SourceFetchError("boom")),
                source_key=key,
                retry_policy=RetryPolicy(max_attempts=1, backoff_base_seconds=0, jitter_seconds=0),
            )

    with pytest.raises(CircuitBreakerOpenError):
        run_with_retry(lambda: "ok", source_key=key, retry_policy=RetryPolicy(max_attempts=1, backoff_base_seconds=0, jitter_seconds=0))
