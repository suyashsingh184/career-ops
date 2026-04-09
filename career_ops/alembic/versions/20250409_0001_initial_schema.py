"""initial schema

Revision ID: 20250409_0001
Revises:
Create Date: 2026-04-09 15:30:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20250409_0001"
down_revision = None
branch_labels = None
depends_on = None


def _json_type() -> sa.JSON:
    return sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql")


def upgrade() -> None:
    op.create_table(
        "companies",
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("careers_url", sa.String(length=500), nullable=True),
        sa.Column("linkedin_url", sa.String(length=500), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_companies")),
        sa.UniqueConstraint("name", name=op.f("uq_companies_name")),
    )
    op.create_index(op.f("ix_companies_name"), "companies", ["name"], unique=False)

    op.create_table(
        "audit_logs",
        sa.Column("entity_type", sa.String(length=64), nullable=False),
        sa.Column("entity_id", sa.String(length=64), nullable=False),
        sa.Column("action", sa.String(length=64), nullable=False),
        sa.Column("actor", sa.String(length=64), nullable=False),
        sa.Column("payload", _json_type(), nullable=False),
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_audit_logs")),
    )
    op.create_index(op.f("ix_audit_logs_action"), "audit_logs", ["action"], unique=False)
    op.create_index(op.f("ix_audit_logs_actor"), "audit_logs", ["actor"], unique=False)
    op.create_index(op.f("ix_audit_logs_entity_id"), "audit_logs", ["entity_id"], unique=False)
    op.create_index(op.f("ix_audit_logs_entity_type"), "audit_logs", ["entity_type"], unique=False)

    op.create_table(
        "jobs",
        sa.Column("source", sa.String(length=50), nullable=False),
        sa.Column("external_id", sa.String(length=255), nullable=False),
        sa.Column("company_id", sa.String(), nullable=True),
        sa.Column("company_name", sa.String(length=255), nullable=False),
        sa.Column("normalized_company_name", sa.String(length=255), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("location", sa.String(length=255), nullable=True),
        sa.Column("normalized_location", sa.String(length=255), nullable=False),
        sa.Column("employment_type", sa.String(length=100), nullable=True),
        sa.Column("department", sa.String(length=255), nullable=True),
        sa.Column("posted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("url", sa.String(length=500), nullable=False),
        sa.Column("raw_description", sa.Text(), nullable=False),
        sa.Column("normalized_description", sa.Text(), nullable=False),
        sa.Column("salary_min", sa.Integer(), nullable=True),
        sa.Column("salary_max", sa.Integer(), nullable=True),
        sa.Column("currency", sa.String(length=10), nullable=True),
        sa.Column("is_remote", sa.Boolean(), nullable=False),
        sa.Column("is_hybrid", sa.Boolean(), nullable=False),
        sa.Column("match_score", sa.Float(), nullable=True),
        sa.Column("archetype", sa.String(length=64), nullable=True),
        sa.Column("decision", sa.String(length=32), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("hash", sa.String(length=64), nullable=False),
        sa.Column("idempotency_key", sa.String(length=255), nullable=True),
        sa.Column("freshness_valid", sa.Boolean(), nullable=False),
        sa.Column("score_breakdown", _json_type(), nullable=False),
        sa.Column("canonical_job_id", sa.String(), nullable=True),
        sa.Column("duplicate_status", sa.String(length=20), nullable=False),
        sa.Column("duplicate_reason", sa.Text(), nullable=True),
        sa.Column("retry_count", sa.Integer(), nullable=False),
        sa.Column("last_failure_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["canonical_job_id"], ["jobs.id"], name=op.f("fk_jobs_canonical_job_id_jobs")),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], name=op.f("fk_jobs_company_id_companies")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_jobs")),
        sa.UniqueConstraint("source", "external_id", name="uq_jobs_source_external_id"),
    )
    for column in [
        "source",
        "external_id",
        "company_name",
        "normalized_company_name",
        "title",
        "normalized_location",
        "posted_at",
        "status",
        "hash",
        "duplicate_status",
    ]:
        op.create_index(op.f(f"ix_jobs_{column}"), "jobs", [column], unique=False)
    op.create_index(op.f("ix_jobs_idempotency_key"), "jobs", ["idempotency_key"], unique=False)

    op.create_table(
        "resumes",
        sa.Column("job_id", sa.String(), nullable=False),
        sa.Column("base_resume_name", sa.String(length=255), nullable=False),
        sa.Column("tailored_summary", sa.Text(), nullable=False),
        sa.Column("tailored_skills", sa.Text(), nullable=False),
        sa.Column("tailored_experience", _json_type(), nullable=False),
        sa.Column("docx_path", sa.String(length=500), nullable=False),
        sa.Column("pdf_path", sa.String(length=500), nullable=True),
        sa.Column("generation_key", sa.String(length=255), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("source_hash", sa.String(length=64), nullable=False),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"], name=op.f("fk_resumes_job_id_jobs")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_resumes")),
    )
    op.create_index(op.f("ix_resumes_generation_key"), "resumes", ["generation_key"], unique=False)
    op.create_index(op.f("ix_resumes_job_id"), "resumes", ["job_id"], unique=False)

    op.create_table(
        "applications",
        sa.Column("job_id", sa.String(), nullable=False),
        sa.Column("resume_id", sa.String(), nullable=True),
        sa.Column("method", sa.String(length=32), nullable=False),
        sa.Column("application_url", sa.String(length=500), nullable=True),
        sa.Column("applied_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("idempotency_key", sa.String(length=255), nullable=False),
        sa.Column("dry_run", sa.Boolean(), nullable=False),
        sa.Column("explicit_submit_approved", sa.Boolean(), nullable=False),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"], name=op.f("fk_applications_job_id_jobs")),
        sa.ForeignKeyConstraint(["resume_id"], ["resumes.id"], name=op.f("fk_applications_resume_id_resumes")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_applications")),
    )
    op.create_index(op.f("ix_applications_idempotency_key"), "applications", ["idempotency_key"], unique=False)
    op.create_index(op.f("ix_applications_job_id"), "applications", ["job_id"], unique=False)
    op.create_index(op.f("ix_applications_status"), "applications", ["status"], unique=False)

    op.create_table(
        "contacts",
        sa.Column("job_id", sa.String(), nullable=False),
        sa.Column("contact_type", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=True),
        sa.Column("company", sa.String(length=255), nullable=True),
        sa.Column("linkedin_url", sa.String(length=500), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("confidence_score", sa.Float(), nullable=False),
        sa.Column("search_hint", sa.Text(), nullable=True),
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"], name=op.f("fk_contacts_job_id_jobs")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_contacts")),
    )
    op.create_index(op.f("ix_contacts_job_id"), "contacts", ["job_id"], unique=False)

    op.create_table(
        "outreach_messages",
        sa.Column("contact_id", sa.String(), nullable=True),
        sa.Column("job_id", sa.String(), nullable=False),
        sa.Column("message_type", sa.String(length=32), nullable=False),
        sa.Column("subject", sa.String(length=255), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("generation_key", sa.String(length=255), nullable=False),
        sa.Column("template_version", sa.String(length=32), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["contact_id"], ["contacts.id"], name=op.f("fk_outreach_messages_contact_id_contacts")),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"], name=op.f("fk_outreach_messages_job_id_jobs")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_outreach_messages")),
    )
    op.create_index(op.f("ix_outreach_messages_generation_key"), "outreach_messages", ["generation_key"], unique=False)
    op.create_index(op.f("ix_outreach_messages_job_id"), "outreach_messages", ["job_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_outreach_messages_job_id"), table_name="outreach_messages")
    op.drop_index(op.f("ix_outreach_messages_generation_key"), table_name="outreach_messages")
    op.drop_table("outreach_messages")
    op.drop_index(op.f("ix_contacts_job_id"), table_name="contacts")
    op.drop_table("contacts")
    op.drop_index(op.f("ix_applications_idempotency_key"), table_name="applications")
    op.drop_index(op.f("ix_applications_status"), table_name="applications")
    op.drop_index(op.f("ix_applications_job_id"), table_name="applications")
    op.drop_table("applications")
    op.drop_index(op.f("ix_resumes_generation_key"), table_name="resumes")
    op.drop_index(op.f("ix_resumes_job_id"), table_name="resumes")
    op.drop_table("resumes")
    op.drop_index(op.f("ix_jobs_idempotency_key"), table_name="jobs")
    for column in ["duplicate_status", "hash", "status", "posted_at", "normalized_location", "title", "normalized_company_name", "company_name", "external_id", "source"]:
        op.drop_index(op.f(f"ix_jobs_{column}"), table_name="jobs")
    op.drop_table("jobs")
    op.drop_index(op.f("ix_audit_logs_actor"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_entity_type"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_entity_id"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_action"), table_name="audit_logs")
    op.drop_table("audit_logs")
    op.drop_index(op.f("ix_companies_name"), table_name="companies")
    op.drop_table("companies")
