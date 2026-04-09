from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.config import get_settings
from app.exceptions import ApplyPreparationError
from app.utils.dates import utcnow
from app.utils.files import ensure_parent


@dataclass
class AssistedApplyPlan:
    job_url: str
    paused_before_submit: bool
    notes: str
    dry_run: bool
    screenshot_dir: str
    html_snapshot_path: str | None = None


def build_assisted_apply_plan(job_url: str, *, explicit_submit_approval: bool = False, mapping_confidence: float = 1.0) -> AssistedApplyPlan:
    settings = get_settings()
    dry_run = settings.playwright_dry_run_default and not explicit_submit_approval
    screenshot_dir = settings.data_dir / "logs" / "playwright" / utcnow().strftime("%Y%m%d%H%M%S")
    ensure_parent(Path(screenshot_dir) / "placeholder.txt")
    if mapping_confidence < 0.7:
        raise ApplyPreparationError("Field mapping confidence too low; manual review required")
    return AssistedApplyPlan(
        job_url=job_url,
        paused_before_submit=not explicit_submit_approval,
        notes=(
            "Playwright automation is configured for assisted mode only. "
            "Capture screenshots and HTML on each major step, abort on CAPTCHA, and stop before final submit unless explicitly approved."
        ),
        dry_run=dry_run,
        screenshot_dir=str(screenshot_dir),
    )
