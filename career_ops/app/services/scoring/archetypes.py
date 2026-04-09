from __future__ import annotations

ARCHETYPE_RULES: dict[str, tuple[str, ...]] = {
    "backend_infra": ("backend", "distributed systems", "platform", "api", "postgresql", "microservices"),
    "platform_engineering": ("platform", "developer experience", "internal tools", "tooling", "infrastructure"),
    "data_streaming": ("kafka", "streaming", "data pipeline", "flink", "event-driven"),
    "ai_ml_systems": ("machine learning", "llm", "model serving", "ai", "inference", "vector"),
    "fullstack_product": ("react", "frontend", "full stack", "product engineering", "typescript"),
    "sre_devops": ("sre", "devops", "observability", "incident", "terraform", "kubernetes"),
    "fintech_backend": ("payments", "risk", "ledger", "fintech", "banking"),
}


def classify_archetype(text: str) -> str:
    lowered = text.lower()
    best_archetype = "backend_infra"
    best_score = 0
    for archetype, keywords in ARCHETYPE_RULES.items():
        score = sum(1 for keyword in keywords if keyword in lowered)
        if score > best_score:
            best_archetype = archetype
            best_score = score
    return best_archetype
