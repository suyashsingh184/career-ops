from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

try:
    from apscheduler.schedulers.background import BackgroundScheduler
except ModuleNotFoundError:  # pragma: no cover - exercised only in lean environments
    class BackgroundScheduler:  # type: ignore[override]
        def __init__(self, timezone: str):
            self.running = False

        def add_job(self, *args, **kwargs) -> None:
            return None

        def start(self) -> None:
            self.running = True

        def shutdown(self, wait: bool = False) -> None:
            self.running = False

from app.api.routes.admin import router as admin_router
from app.api.routes.applications import router as applications_router
from app.api.routes.contacts import router as contacts_router
from app.api.routes.jobs import router as jobs_router
from app.api.routes.outreach import router as outreach_router
from app.api.routes.resumes import router as resumes_router
from app.config import get_settings
from app.db import ensure_runtime_dirs, init_db
from app.dependencies import get_db
from app.logging import configure_logging
from app.models.application import Application
from app.models.audit_log import AuditLog
from app.models.contact import Contact
from app.models.job import Job
from app.models.outreach import OutreachMessage
from app.models.resume import Resume
from app.services.ingest.normalize import build_resume_generation_key
from app.services.tracker.status_machine import enforce_transition
from app.types import JobStatus
from app.utils.audit import record_audit_log
from app.utils.retry import CIRCUIT_BREAKERS
from app.tasks.generate_outreach import run_generate_outreach_for_ready_jobs
from app.tasks.ingest_jobs import run_ingest_job_sources
from app.tasks.score_jobs import run_score_new_jobs

settings = get_settings()
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates" / "web"))
scheduler = BackgroundScheduler(timezone=settings.scheduler_timezone)


@asynccontextmanager
async def lifespan(_: FastAPI):
    configure_logging()
    init_db()
    if settings.enable_scheduler and not scheduler.running:
        scheduler.add_job(run_ingest_job_sources, "interval", hours=1, id="ingest-jobs", replace_existing=True)
        scheduler.add_job(run_score_new_jobs, "interval", hours=1, id="score-jobs", replace_existing=True)
        scheduler.add_job(run_generate_outreach_for_ready_jobs, "cron", hour=9, minute=0, id="daily-reminders", replace_existing=True)
        scheduler.start()
    yield
    if scheduler.running:
        scheduler.shutdown(wait=False)


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.include_router(jobs_router)
app.include_router(resumes_router)
app.include_router(outreach_router)
app.include_router(applications_router)
app.include_router(contacts_router)
app.include_router(admin_router)
ensure_runtime_dirs()
app.mount("/data", StaticFiles(directory=str(settings.data_dir), check_dir=False), name="data")


@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    jobs = list(db.scalars(select(Job).order_by(desc(Job.posted_at), desc(Job.created_at)).limit(50)))
    applications = list(db.scalars(select(Application).order_by(desc(Application.created_at)).limit(20)))
    outreach = list(db.scalars(select(OutreachMessage).order_by(desc(OutreachMessage.created_at)).limit(20)))
    audits = list(db.scalars(select(AuditLog).order_by(desc(AuditLog.created_at)).limit(20)))
    stats = {
        "total_jobs": len(jobs),
        "apply_now": sum(1 for job in jobs if job.decision == "apply_now"),
        "ready_to_apply": sum(1 for job in jobs if job.status == "ready_to_apply"),
        "applied": sum(1 for application in applications if application.status == "submitted"),
    }
    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {
            "request": request,
            "jobs": jobs,
            "applications": applications,
            "outreach_messages": outreach,
            "stats": stats,
            "audits": audits,
            "circuit_breakers": CIRCUIT_BREAKERS.snapshot(),
        },
    )


@app.get("/jobs-view", response_class=HTMLResponse)
def jobs_view(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    jobs = list(db.scalars(select(Job).order_by(desc(Job.posted_at), desc(Job.created_at))))
    return templates.TemplateResponse(request, "jobs.html", {"request": request, "jobs": jobs})


@app.get("/jobs-view/{job_id}", response_class=HTMLResponse)
def job_detail(request: Request, job_id: str, db: Session = Depends(get_db)) -> HTMLResponse:
    job = db.get(Job, job_id)
    if job is None:
        return HTMLResponse("Job not found", status_code=404)
    resumes = list(db.scalars(select(Resume).where(Resume.job_id == job.id).order_by(desc(Resume.created_at))))
    contacts = list(db.scalars(select(Contact).where(Contact.job_id == job.id).order_by(Contact.confidence_score.desc())))
    outreach = list(
        db.scalars(select(OutreachMessage).where(OutreachMessage.job_id == job.id).order_by(desc(OutreachMessage.created_at)))
    )
    applications = list(
        db.scalars(select(Application).where(Application.job_id == job.id).order_by(desc(Application.created_at)))
    )
    return templates.TemplateResponse(
        request,
        "job_detail.html",
        {
            "request": request,
            "job": job,
            "resumes": resumes,
            "contacts": contacts,
            "outreach_messages": outreach,
            "applications": applications,
            "canonical_group": list(
                db.scalars(
                    select(Job).where((Job.id == (job.canonical_job_id or job.id)) | (Job.canonical_job_id == (job.canonical_job_id or job.id)))
                )
            ),
        },
    )


@app.post("/web/jobs/{job_id}/score")
def web_score_job(job_id: str, db: Session = Depends(get_db)) -> RedirectResponse:
    job = db.get(Job, job_id)
    if job is not None:
        from app.services.scoring.career_ops import score_job

        result = score_job(job)
        job.match_score = result.final_score
        job.archetype = result.archetype
        job.decision = result.decision
        job.score_breakdown = result.to_dict()
        job.status = JobStatus.SCORED.value
        record_audit_log(db, entity_type="job", entity_id=job.id, action="score_generated", payload=result.to_dict())
        db.commit()
    return RedirectResponse(url=f"/jobs-view/{job_id}", status_code=303)


@app.post("/web/jobs/{job_id}/contacts")
def web_find_contacts(job_id: str, db: Session = Depends(get_db)) -> RedirectResponse:
    job = db.get(Job, job_id)
    if job is not None and not job.contacts:
        from app.services.people.finder import suggested_contacts

        for payload in suggested_contacts(job):
            db.add(Contact(job_id=job.id, **payload))
        db.commit()
    return RedirectResponse(url=f"/jobs-view/{job_id}", status_code=303)


@app.post("/web/jobs/{job_id}/tailor")
def web_tailor_resume(job_id: str, db: Session = Depends(get_db)) -> RedirectResponse:
    job = db.get(Job, job_id)
    if job is not None:
        from app.services.tailoring.resume_engine import build_tailored_resume

        generation_key = build_resume_generation_key(job, "backend_distributed_systems")
        existing = db.scalar(select(Resume).where(Resume.generation_key == generation_key).order_by(desc(Resume.version)))
        if existing is None or existing.source_hash != job.hash:
            payload = build_tailored_resume(job, version=(existing.version + 1) if existing else 1)
            db.add(Resume(job_id=job.id, **payload.__dict__))
            job.status = JobStatus.TAILORED.value
        db.commit()
    return RedirectResponse(url=f"/jobs-view/{job_id}", status_code=303)


@app.post("/web/jobs/{job_id}/outreach")
def web_generate_outreach(job_id: str, db: Session = Depends(get_db)) -> RedirectResponse:
    job = db.get(Job, job_id)
    if job is not None:
        contacts = list(db.scalars(select(Contact).where(Contact.job_id == job.id).order_by(Contact.confidence_score.desc())))
        if not contacts:
            from app.services.people.finder import suggested_contacts

            for payload in suggested_contacts(job):
                db.add(Contact(job_id=job.id, **payload))
            db.flush()
            contacts = list(
                db.scalars(select(Contact).where(Contact.job_id == job.id).order_by(Contact.confidence_score.desc()))
            )
        from app.services.outreach.generator import generate_outreach_messages

        for payload in generate_outreach_messages(job, contacts):
            existing = db.scalar(select(OutreachMessage).where(OutreachMessage.generation_key == payload["generation_key"]))
            if existing is None:
                db.add(OutreachMessage(job_id=job.id, **payload))
        db.commit()
    return RedirectResponse(url=f"/jobs-view/{job_id}", status_code=303)
