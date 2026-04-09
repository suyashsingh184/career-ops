from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}
