"""Orchestrates the analyze pipeline: classify -> retrieve -> generate."""

import logging

from app.models.schemas import IssueAnalysis, SourceReference
from app.rag.vector_store import get_vector_store
from app.services.classifier import classify
from app.services.llm_client import LLMUnavailableError, generate_grounded_analysis

logger = logging.getLogger(__name__)


def analyze_issue(issue_text: str) -> IssueAnalysis:
    rule = classify(issue_text)

    # Retrieval: ground the answer in the knowledge base regardless of
    # whether the LLM is enabled, so `sources` is always populated when
    # relevant documentation exists.
    try:
        search_results = get_vector_store().search(issue_text)
    except (
        Exception
    ):  # pragma: no cover - defensive, vector store issues shouldn't 500 the API
        logger.exception(
            "Vector store search failed; continuing without retrieved context."
        )
        search_results = []

    sources = [
        SourceReference(
            source=r.source, snippet=r.content[:280], relevance_score=r.score
        )
        for r in search_results
    ]

    probable_cause = rule.probable_cause
    recommended_steps = list(rule.recommended_steps)
    generated_by = "rule_based"

    try:
        llm_output = generate_grounded_analysis(
            issue_text=issue_text,
            category=rule.category,
            severity=rule.severity,
            retrieved_context=[r.content for r in search_results],
        )
        if llm_output.get("probable_cause"):
            probable_cause = llm_output["probable_cause"]
        if llm_output.get("recommended_steps"):
            recommended_steps = llm_output["recommended_steps"]
        generated_by = "llm"
    except LLMUnavailableError as exc:
        logger.info("Using rule-based generation: %s", exc)

    return IssueAnalysis(
        category=rule.category,
        severity=rule.severity,
        confidence=rule.confidence,
        probable_cause=probable_cause,
        recommended_steps=recommended_steps,
        relevant_commands=rule.relevant_commands,
        escalation_required=rule.escalation_required,
        escalation_reason=rule.escalation_reason,
        sources=sources,
        generated_by=generated_by,
    )
