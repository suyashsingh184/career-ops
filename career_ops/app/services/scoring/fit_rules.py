from __future__ import annotations

from dataclasses import dataclass


@dataclass
class CandidateProfile:
    name: str
    target_locations: list[str]
    preferred_stacks: list[str]
    domains: list[str]
    seniority: str
    skills: list[str]
    impact_keywords: list[str]
    resume_bullets: list[str]


DEFAULT_CANDIDATE = CandidateProfile(
    name="Backend / Distributed Systems Engineer",
    target_locations=["remote", "san francisco", "new york", "seattle"],
    preferred_stacks=[
        "python",
        "backend",
        "fastapi",
        "postgresql",
        "postgres",
        "kafka",
        "aws",
        "docker",
        "sqlalchemy",
        "platform",
        "infrastructure",
        "reliability",
        "distributed systems",
    ],
    domains=[
        "fintech",
        "infra",
        "infrastructure",
        "developer platform",
        "platform engineering",
        "platform",
        "data",
        "ai",
        "backend",
        "distributed systems",
    ],
    seniority="senior",
    skills=[
        "python",
        "backend",
        "distributed systems",
        "platform engineering",
        "event streaming",
        "api design",
        "postgresql",
        "postgres",
        "kubernetes",
        "reliability",
    ],
    impact_keywords=[
        "latency",
        "throughput",
        "reliability",
        "scale",
        "migration",
        "automation",
        "performance",
        "platform",
        "infrastructure",
        "distributed systems",
        "backend",
    ],
    resume_bullets=[
        "Built Python services for high-throughput distributed systems with strong observability and SLO ownership.",
        "Led backend platform work across APIs, PostgreSQL, Kafka, and cloud infrastructure.",
        "Improved engineering velocity through automation, deployment workflows, and production incident reduction.",
    ],
)
