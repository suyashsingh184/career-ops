from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class ContactRead(BaseModel):
    id: str
    job_id: str
    contact_type: str
    name: Optional[str]
    title: Optional[str]
    company: Optional[str]
    linkedin_url: Optional[str]
    email: Optional[str]
    confidence_score: float
    search_hint: Optional[str]

    model_config = {"from_attributes": True}
