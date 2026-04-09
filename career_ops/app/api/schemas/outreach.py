from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class OutreachMessageRead(BaseModel):
    id: str
    job_id: str
    contact_id: Optional[str]
    message_type: str
    subject: str
    body: str
    status: str
    generation_key: str
    template_version: str
    version: int
    last_error: Optional[str]

    model_config = {"from_attributes": True}
