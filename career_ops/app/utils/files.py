from __future__ import annotations

import os
from pathlib import Path
from tempfile import NamedTemporaryFile


def ensure_parent(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def safe_slug(value: str) -> str:
    return "".join(character.lower() if character.isalnum() else "_" for character in value).strip("_")


def atomic_write_bytes(path: Path, data: bytes) -> Path:
    ensure_parent(path)
    with NamedTemporaryFile(dir=path.parent, delete=False) as temp:
        temp.write(data)
        temp.flush()
        os.fsync(temp.fileno())
        temp_path = Path(temp.name)
    temp_path.replace(path)
    return path
