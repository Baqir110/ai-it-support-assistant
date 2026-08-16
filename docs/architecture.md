# Architecture

## Overview

```
User
  │
  ▼
Web / API Client
  │  POST /support/analyze { "issue": "..." }
  ▼
FastAPI Backend  (app/api)
  │
  ├──► Classifier (app/services/classifier.py)
  │      Deterministic rule engine: category, severity, base steps,
  │      commands, escalation policy. Pure Python, no external calls,
  │      100% unit-testable.
  │
  ├──► RAG Pipeline (app/rag)
  │      1. loader.py    - chunk markdown knowledge base on headings
  │      2. embeddings.py - pluggable embedding backend
  │      3. vector_store.py - ChromaDB, cosine similarity search
  │      Retrieves top-k relevant chunks + returns them as `sources`
  │      with a relevance score, regardless of LLM usage.
  │
  ├──► LLM Client (app/services/llm_client.py)   [optional]
  │      OpenAI-compatible chat completion, given the classification +
  │      retrieved context, asked to *only* rewrite probable_cause and
  │      recommended_steps in natural language grounded in that context.
  │      Never chooses category/severity/escalation - those stay
  │      deterministic and auditable.
  │
  └──► Persistence (app/db)   [optional]
         SQLAlchemy → PostgreSQL. Every analysis is logged (issue,
         classification, generated_by, source count) for evaluation
         and analytics. Skipped entirely if DATABASE_URL is unset.
  │
  ▼
IssueAnalysis JSON response
  { category, severity, confidence, probable_cause, recommended_steps,
    relevant_commands, escalation_required, escalation_reason, sources,
    generated_by }
```

## Technical decisions

### Why classification is rule-based, not LLM-based

Category, severity, and escalation policy are business rules a support
team needs to control and test precisely — an LLM silently reclassifying
a "system crash" as "low severity" because of phrasing drift is a real
production risk. The classifier is pure Python with unit tests per
category. The LLM's role is deliberately narrowed to *wording* the
already-decided answer, grounded in retrieved documentation, which keeps
its blast radius small and its output testable.

### Why the default embedding backend is a hashing vectorizer, not an API call

`scikit-learn`'s `HashingVectorizer` is stateless, deterministic, and
needs no model download or network access. That means:

- The project runs fully offline, with zero API keys, out of the box.
- CI and this exact test suite run without secrets or flaky network calls.
- Retrieval quality is "good enough" for keyword-dense IT documentation,
  where exact terminology (Wi-Fi, BSOD, `ipconfig`) matters more than
  deep semantic similarity.

`app/rag/embeddings.py` implements the same interface for OpenAI
embeddings (`text-embedding-3-small`). Setting `EMBEDDING_BACKEND=openai`
and `OPENAI_API_KEY` switches the whole pipeline to real semantic
embeddings with no other code changes — a one-line config decision, not
an architecture change.

### Why the LLM is optional at all

Two reasons: cost/latency during development and iteration, and so the
core RAG + classification pipeline stands on its own as a demonstrable,
gradeable component. `generated_by` in every response tells you which
path produced the text, so this is transparent rather than hidden.

### Why PostgreSQL logging is optional

The API is useful standalone; the database exists to support evaluation
(comparing rule-based vs LLM-augmented outputs, tracking escalation
rates over time) once there's traffic to analyze. `db_enabled` is
surfaced on `/health` so it's obvious whether logging is active.

## Data flow for a single request

1. `POST /support/analyze {"issue": "..."}"` hits `app/api/routes.py`.
2. `classify()` matches the issue against keyword rules → category,
   severity, base steps, commands, escalation flag.
3. `VectorStore.search()` embeds the issue text and retrieves the top-k
   most similar knowledge base chunks.
4. If an LLM is configured, `generate_grounded_analysis()` sends the
   classification + retrieved chunks to the model and asks for a strict
   JSON `{probable_cause, recommended_steps}`, which overrides the
   rule-based text. If the LLM is unavailable or returns malformed
   output, the pipeline **falls back to the rule-based text**, so the
   API never errors due to an LLM outage.
5. The final `IssueAnalysis` is (optionally) logged to Postgres and
   returned to the client.

## Evaluation approach

`tests/test_classifier.py` and `tests/test_troubleshooter.py` pin down
expected category/severity/escalation per issue type - the regression
suite for the rule engine. `tests/test_api.py` exercises the endpoints
end-to-end with retrieval enabled but the LLM disabled, so the "offline
mode" contract is what CI actually verifies. When the LLM path is
enabled in a real deployment, comparing `generated_by="llm"` vs
`"rule_based"` responses against the same issue set (logged via
Postgres) is the intended way to evaluate whether LLM augmentation is
actually improving answer quality over the deterministic baseline.
