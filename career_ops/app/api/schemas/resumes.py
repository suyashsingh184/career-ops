from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class ResumeRead(BaseModel):
    id: str
    job_id: str
    base_resume_name: str
    tailored_summary: str
    tailored_skills: str
    tailored_experience: list[dict[str, str]]
    docx_path: str
    pdf_path: Optional[str]
    generation_key: str
    version: int
    status: str
    source_hash: str
    last_error: Optional[str]

    model_config = {"from_attributes": True}
