from __future__ import annotations

import pytest

from app.exceptions import StateTransitionError
from app.services.tracker.status_machine import enforce_transition


def test_illegal_job_transition_raises() -> None:
    with pytest.raises(StateTransitionError):
        enforce_transition("discovered", "applied", machine="job")


def test_illegal_outreach_transition_raises() -> None:
    with pytest.raises(StateTransitionError):
        enforce_transition("draft", "sent", machine="outreach")
