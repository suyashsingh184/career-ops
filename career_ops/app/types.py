from __future__ import annotations

from enum import Enum


class SourceKind(str, Enum):
    GREENHOUSE = "greenhouse"
    LEVER = "lever"
    ASHBY = "ashby"
    SCRAPER = "scraper"
    SEED = "seed"


class JobDecision(str, Enum):
    APPLY_NOW = "apply_now"
    APPLY_IF_TIME = "apply_if_time"
    SKIP = "skip"
    PENDING_MANUAL_REVIEW = "pending_manual_review"


class JobStatus(str, Enum):
    DISCOVERED = "discovered"
    NORMALIZED = "normalized"
    SCORED = "scored"
    TAILORED = "tailored"
    READY_TO_APPLY = "ready_to_apply"
    APPLIED = "applied"
    DUPLICATE = "duplicate"
    FAILED = "failed"
    SKIPPED = "skipped"
    CONTACTED = "contacted"
    INTERVIEWING = "interviewing"
    REJECTED = "rejected"
    OFFER = "offer"


class ApplicationStatus(str, Enum):
    NOT_STARTED = "not_started"
    QUEUED = "queued"
    PREPARING = "preparing"
    READY_FOR_REVIEW = "ready_for_review"
    SUBMITTED = "submitted"
    CONTACTED = "contacted"
    FAILED = "failed"
    WITHDRAWN = "withdrawn"
    REJECTED = "rejected"
    OFFER = "offer"


class OutreachStatus(str, Enum):
    DRAFT = "draft"
    APPROVED = "approved"
    SENT = "sent"
    ARCHIVED = "archived"
    FAILED = "failed"


class DuplicateStatus(str, Enum):
    CANONICAL = "canonical"
    DUPLICATE = "duplicate"
    REVIEW = "review"


class ApplicationMethod(str, Enum):
    MANUAL = "manual"
    ASSISTED = "assisted"
    DIRECT_API = "direct_api"


class ContactType(str, Enum):
    RECRUITER = "recruiter"
    ENGINEERING_MANAGER = "engineering_manager"
    TEAM_ENGINEER = "team_engineer"
