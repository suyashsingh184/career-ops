from __future__ import annotations

from app.exceptions import StateTransitionError
from app.types import ApplicationStatus, JobStatus, OutreachStatus

JOB_TRANSITIONS = {
    JobStatus.DISCOVERED.value: {JobStatus.NORMALIZED.value, JobStatus.DUPLICATE.value, JobStatus.FAILED.value},
    JobStatus.NORMALIZED.value: {JobStatus.SCORED.value, JobStatus.SKIPPED.value, JobStatus.FAILED.value},
    JobStatus.SCORED.value: {JobStatus.TAILORED.value, JobStatus.READY_TO_APPLY.value, JobStatus.SKIPPED.value, JobStatus.FAILED.value},
    JobStatus.TAILORED.value: {JobStatus.READY_TO_APPLY.value, JobStatus.FAILED.value},
    JobStatus.READY_TO_APPLY.value: {JobStatus.APPLIED.value, JobStatus.FAILED.value},
    JobStatus.APPLIED.value: {JobStatus.CONTACTED.value, JobStatus.INTERVIEWING.value, JobStatus.REJECTED.value, JobStatus.OFFER.value},
    JobStatus.CONTACTED.value: {JobStatus.INTERVIEWING.value, JobStatus.REJECTED.value, JobStatus.OFFER.value},
    JobStatus.INTERVIEWING.value: {JobStatus.REJECTED.value, JobStatus.OFFER.value},
    JobStatus.DUPLICATE.value: set(),
    JobStatus.SKIPPED.value: set(),
    JobStatus.FAILED.value: {JobStatus.NORMALIZED.value, JobStatus.SCORED.value, JobStatus.TAILORED.value, JobStatus.READY_TO_APPLY.value},
    JobStatus.REJECTED.value: set(),
    JobStatus.OFFER.value: set(),
}

APPLICATION_TRANSITIONS = {
    ApplicationStatus.NOT_STARTED.value: {ApplicationStatus.QUEUED.value, ApplicationStatus.FAILED.value},
    ApplicationStatus.QUEUED.value: {ApplicationStatus.PREPARING.value, ApplicationStatus.FAILED.value},
    ApplicationStatus.PREPARING.value: {ApplicationStatus.READY_FOR_REVIEW.value, ApplicationStatus.FAILED.value},
    ApplicationStatus.READY_FOR_REVIEW.value: {ApplicationStatus.SUBMITTED.value, ApplicationStatus.FAILED.value, ApplicationStatus.WITHDRAWN.value},
    ApplicationStatus.SUBMITTED.value: {
        ApplicationStatus.CONTACTED.value,
        ApplicationStatus.REJECTED.value,
        ApplicationStatus.OFFER.value,
        ApplicationStatus.WITHDRAWN.value,
    },
    ApplicationStatus.CONTACTED.value: {ApplicationStatus.REJECTED.value, ApplicationStatus.OFFER.value},
    ApplicationStatus.FAILED.value: {ApplicationStatus.QUEUED.value, ApplicationStatus.PREPARING.value},
    ApplicationStatus.WITHDRAWN.value: set(),
    ApplicationStatus.REJECTED.value: set(),
    ApplicationStatus.OFFER.value: set(),
}

OUTREACH_TRANSITIONS = {
    OutreachStatus.DRAFT.value: {OutreachStatus.APPROVED.value, OutreachStatus.ARCHIVED.value, OutreachStatus.FAILED.value},
    OutreachStatus.APPROVED.value: {OutreachStatus.SENT.value, OutreachStatus.ARCHIVED.value, OutreachStatus.FAILED.value},
    OutreachStatus.SENT.value: {OutreachStatus.ARCHIVED.value},
    OutreachStatus.ARCHIVED.value: set(),
    OutreachStatus.FAILED.value: {OutreachStatus.DRAFT.value, OutreachStatus.ARCHIVED.value},
}


def can_transition(current: str, target: str, *, machine: str = "job") -> bool:
    transitions = {
        "job": JOB_TRANSITIONS,
        "application": APPLICATION_TRANSITIONS,
        "outreach": OUTREACH_TRANSITIONS,
    }[machine]
    return target in transitions.get(current, set())


def enforce_transition(current: str, target: str, *, machine: str = "job") -> None:
    if current == target:
        return
    if not can_transition(current, target, machine=machine):
        raise StateTransitionError(f"Illegal {machine} transition: {current} -> {target}")
