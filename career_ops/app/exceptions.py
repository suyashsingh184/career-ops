from __future__ import annotations


class CareerOpsError(Exception):
    retryable: bool = False
    user_action_required: bool = False


class SourceFetchError(CareerOpsError):
    retryable = True


class NormalizationError(CareerOpsError):
    retryable = False


class DedupConflictError(CareerOpsError):
    retryable = False


class ScoringError(CareerOpsError):
    retryable = False


class ResumeGenerationError(CareerOpsError):
    retryable = True


class OutreachGenerationError(CareerOpsError):
    retryable = False


class ApplyPreparationError(CareerOpsError):
    retryable = True


class StateTransitionError(CareerOpsError):
    retryable = False
    user_action_required = True


class CircuitBreakerOpenError(SourceFetchError):
    retryable = True
