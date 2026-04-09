from __future__ import annotations

from pathlib import Path

from app.utils.files import atomic_write_bytes


def test_atomic_write_creates_nonempty_file(tmp_path: Path) -> None:
    destination = tmp_path / "sample.docx"
    atomic_write_bytes(destination, b"hello")
    assert destination.exists()
    assert destination.read_bytes() == b"hello"
