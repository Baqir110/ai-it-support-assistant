"""Thin wrapper around an OpenAI-compatible chat completions endpoint.

Kept deliberately small: one method, one job (produce grounded prose for an
already-classified issue). Category/severity/escalation policy live in
classifier.py and are never delegated to the model. This keeps the LLM's
blast radius limited to wording, which is what makes the rest of the
pipeline testable without live API calls.
"""

import json
import logging

from app.config.settings import get_settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an IT support assistant. You are given a user's issue, \
a pre-computed classification, and excerpts retrieved from internal IT documentation.

Write a concise, grounded explanation using ONLY the provided context and classification.
Do not invent facts, commands, or sources that are not present in the context.

Respond with strict JSON only, in this shape:
{"probable_cause": "...", "recommended_steps": ["...", "..."]}
"""


class LLMUnavailableError(RuntimeError):
    pass


def generate_grounded_analysis(
    issue_text: str,
    category: str,
    severity: str,
    retrieved_context: list[str],
) -> dict:
    """Calls the configured LLM to refine probable_cause/recommended_steps.

    Raises LLMUnavailableError if no provider is configured; callers should
    catch this and fall back to the deterministic rule-based text.
    """
    settings = get_settings()
    if not settings.llm_enabled:
        raise LLMUnavailableError(
            "No LLM provider configured (set LLM_PROVIDER=openai and OPENAI_API_KEY)."
        )

    from openai import OpenAI

    client = OpenAI(api_key=settings.openai_api_key, base_url=settings.openai_base_url)

    context_block = (
        "\n\n".join(f"[Doc {i+1}] {c}" for i, c in enumerate(retrieved_context))
        or "(no documentation retrieved)"
    )
    user_prompt = (
        f"User issue: {issue_text}\n"
        f"Classification: category={category}, severity={severity}\n\n"
        f"Retrieved documentation:\n{context_block}"
    )

    response = client.chat.completions.create(
        model=settings.llm_model,
        temperature=settings.llm_temperature,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
    )

    content = response.choices[0].message.content
    try:
        return json.loads(content)
    except (json.JSONDecodeError, TypeError) as exc:
        logger.warning("LLM returned non-JSON content, falling back: %s", exc)
        raise LLMUnavailableError("LLM response was not valid JSON.") from exc
