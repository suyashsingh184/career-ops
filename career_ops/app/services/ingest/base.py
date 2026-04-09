from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class IngestedJob:
    source: str
    external_id: str
    company_name: str
    title: str
    location: Optional[str]
    employment_type: Optional[str]
    department: Optional[str]
    posted_at: Optional[datetime]
    url: str
    raw_description: str
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    currency: Optional[str] = None
    is_remote: bool = False
    is_hybrid: bool = False


class IngestionError(RuntimeError):
    """Raised when a source cannot be parsed."""
