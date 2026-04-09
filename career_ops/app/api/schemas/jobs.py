from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.types import JobDecision, SourceKind


class IngestSourceRequest(BaseModel):
    kind: SourceKind
    token: Optional[str] = None
    url: Optional[str] = None
    company_name: Optional[str] = None


class JobsIngestRequest(BaseModel):
    sources: list[IngestSourceRequest] = Field(default_factory=list)
    last_24_hours_only: bool = True
    include_seed: bool = False
    allow_stale: bool = False


class JobRead(BaseModel):
    id: str
    source: str
    external_id: str
    company_name: str
    title: str
    location: Optional[str]
    posted_at: Optional[datetime]
    url: str
    archetype: Optional[str]
    decision: Optional[str]
    match_score: Optional[float]
    status: str
    duplicate_status: str
    duplicate_reason: Optional[str]
    canonical_job_id: Optional[str]
    retry_count: int
    last_error: Optional[str]
    score_breakdown: dict

    model_config = {"from_attributes": True}


class JobDecisionRequest(BaseModel):
    decision: JobDecision
