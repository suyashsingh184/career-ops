from __future__ import annotations

import hashlib


def stable_hash(*parts: str) -> str:
    return hashlib.sha256("||".join(part.strip().lower() for part in parts if part).encode("utf-8")).hexdigest()
