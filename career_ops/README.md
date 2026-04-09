# Career-Ops

Career-Ops is a production-minded MVP for job hunting operations. It ingests public job postings, normalizes and deduplicates them, scores them using a deterministic Career-Ops engine, produces truthful ATS-friendly tailored resumes, drafts outreach, queues assisted applications, and tracks pipeline state in a lightweight dashboard.

## What is included

- FastAPI app with JSON APIs and HTML dashboard pages
- SQLAlchemy 2.x models for jobs, resumes, applications, contacts, outreach messages, companies, and audit logs
- Alembic migration for the initial schema
- Public-source ingestion adapters for Greenhouse, Lever, Ashby, and a generic careers-page scraper fallback
- Deterministic role archetype classification and Career-Ops scoring
- Resume tailoring engine with DOCX export
- Outreach generation and people-finder hint ranking
- Assisted apply queue support that intentionally pauses before submit
- APScheduler jobs for ingestion, scoring, and reminder/outreach refresh workflows
- Unit and integration tests for core logic and the ingest -> score -> tailor flow

## Hardening notes

- Startup now creates runtime directories automatically and only calls `create_all()` for SQLite. For PostgreSQL, use Alembic migrations as the source of truth.
- Scheduler startup can be disabled with `CAREER_OPS_ENABLE_SCHEDULER=false`, which is useful for tests and one-off scripts.
- JSON columns use PostgreSQL `JSONB` when running against Postgres and generic `JSON` elsewhere.
- Dashboard pages now expose direct workflow actions for scoring, resume tailoring, contact discovery, and outreach generation.

## Live source validation

On April 9, 2026, the ingestion adapters were validated against real public boards:

- Greenhouse: `anthropic`
- Lever: `finch`

Observed live payload details during validation:

- Greenhouse `anthropic` returned 421 jobs, with the most recent posting timestamp at `2026-04-09T18:34:20-04:00`
- Lever `finch` returned 7 jobs, with the most recent posting timestamp at `2026-04-09T16:48:43.090000`

Parser fixtures derived from those real payload shapes live in:

- `tests/fixtures/greenhouse_anthropic_sample.json`
- `tests/fixtures/lever_finch_sample.json`

## Repository layout

The repository follows the requested structure under `app/`, `alembic/`, `tests/`, `data/`, and `scripts/`.

## Local setup

1. Create a virtual environment and install dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Copy `.env.example` to `.env` if you want to override defaults.

3. Optional: start PostgreSQL with Docker:

```bash
docker compose up -d db
```

By default the app also runs with SQLite for local smoke testing.

## Running migrations

```bash
alembic upgrade head
```

## Starting the API

```bash
uvicorn app.main:app --reload
```

Open the dashboard at [http://127.0.0.1:8000/](http://127.0.0.1:8000/).

## Running ingestion

Seed three sample jobs:

```bash
curl -X POST http://127.0.0.1:8000/jobs/ingest \
  -H "Content-Type: application/json" \
  -d '{"include_seed": true}'
```

Example public ATS ingestion request:

```bash
curl -X POST http://127.0.0.1:8000/jobs/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "sources": [
      {"kind": "greenhouse", "token": "your-board-token"},
      {"kind": "lever", "token": "your-lever-company"},
      {"kind": "ashby", "token": "your-ashby-company"}
    ]
  }'
```

The ingestion route filters to jobs posted within the last 24 hours unless you disable that behavior.

## Generating a tailored resume

1. Score a job:

```bash
curl -X POST http://127.0.0.1:8000/jobs/<job_id>/score
```

2. Tailor the resume:

```bash
curl -X POST http://127.0.0.1:8000/jobs/<job_id>/tailor-resume
```

The generated DOCX path is stored in the `resumes` table and returned by the API.

## Dashboard usage

- `/` shows recent jobs, application activity, and outreach drafts
- `/jobs-view` lists all jobs
- `/jobs-view/{job_id}` shows job detail and normalized description

Use the JSON APIs to move jobs through scoring, contact discovery, outreach generation, and apply queueing.

## Playwright setup

Install browser dependencies:

```bash
python3 -m playwright install chromium
```

The current MVP stores an assisted-apply plan and intentionally stops before final submission. This is by design to respect the requirement that automation must not finalize an application without explicit approval.

## Limitations of direct auto-apply

- `direct_api` is only appropriate when a public, documented apply flow exists
- Private ATS APIs are intentionally not reverse engineered
- Generic scraper fallback only discovers candidate links and does not fabricate structured metadata
- Contact generation uses ranked search hints when direct data is unavailable and never hallucinates email or LinkedIn identities
- PDF export is left as a manual extension point because local DOCX-to-PDF conversion depends on external office tooling

## How to extend job sources

1. Add a new adapter under `app/services/ingest/`
2. Return `IngestedJob` records from the adapter
3. Register the adapter in `POST /jobs/ingest`
4. Add parser fixtures and tests for the new source

## Running tests

```bash
pytest
```

## Seed data

Included fixtures cover:

- backend infra
- data streaming
- fullstack product

The scoring and tailoring logic are tuned around a backend/distributed-systems candidate profile in `app/services/scoring/fit_rules.py`.
