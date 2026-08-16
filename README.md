# AI IT Support Assistant

A RAG-backed API that classifies IT support issues, retrieves grounded
context from an internal knowledge base, and returns a structured
troubleshooting recommendation — probable cause, steps, relevant commands,
severity, escalation guidance, and the sources it used.

Runs fully offline out of the box (no API keys required) and upgrades to
LLM-augmented generation and PostgreSQL-backed analytics with a couple of
environment variables. See [`docs/architecture.md`](docs/architecture.md)
for the full design rationale.

## Features

- FastAPI REST API with OpenAPI docs at `/docs`
- Deterministic classifier: category, severity, confidence, escalation policy
- RAG pipeline: ChromaDB vector store over a Markdown knowledge base,
  with a pluggable embedding backend (offline hashing vectorizer by
  default, OpenAI embeddings optional)
- Optional LLM-augmented generation via any OpenAI-compatible endpoint
  (OpenAI, Azure OpenAI, local vLLM/Ollama, etc.) — with automatic
  fallback to the deterministic generator if the LLM is unavailable
- Optional PostgreSQL logging of every analysis for evaluation
- Dockerized (API + Postgres) via `docker-compose`
- Automated tests with pytest (classifier, RAG grounding, API, LLM fallback)

## Example

### Request

```json
POST /support/analyze
{
  "issue": "My Windows laptop cannot connect to Wi-Fi."
}
```

### Response

```json
{
  "issue": "My Windows laptop cannot connect to Wi-Fi.",
  "analysis": {
    "category": "network",
    "severity": "medium",
    "confidence": 0.9,
    "probable_cause": "Network connectivity or configuration issue.",
    "recommended_steps": [
      "Check whether Airplane Mode is disabled.",
      "Restart the Wi-Fi adapter.",
      "Forget and reconnect to the Wi-Fi network.",
      "Run the Windows network troubleshooter.",
      "Restart the router if other devices are also affected."
    ],
    "relevant_commands": [
      "ipconfig /all",
      "ipconfig /release",
      "ipconfig /renew",
      "ipconfig /flushdns"
    ],
    "escalation_required": false,
    "escalation_reason": null,
    "sources": [
      {
        "source": "network_issues.md",
        "snippet": "## Initial Troubleshooting\n1. Check whether Airplane Mode is disabled...",
        "relevance_score": 0.61
      }
    ],
    "generated_by": "rule_based"
  }
}
```

## Architecture

```
User → Web/API Client → FastAPI → Classifier ─┐
                                    RAG (Chroma) ├─► LLM (optional) → Response
                                    Postgres (optional, logging)   ┘
```

Full diagram and technical decisions: [`docs/architecture.md`](docs/architecture.md).

## Project layout

```
app/
├── api/            # FastAPI routes
├── config/         # Environment-driven settings
├── rag/            # Loader, embeddings, ChromaDB vector store
├── services/       # Classifier, LLM client, orchestrator
├── models/         # Pydantic schemas
├── db/             # SQLAlchemy models + session (optional Postgres logging)
└── main.py

data/knowledge_base/  # Markdown IT documentation ingested into the vector store
docker/Dockerfile
docker-compose.yml
docs/architecture.md
tests/
```

## Installation

### Local (offline mode, no API keys needed)

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # optional, defaults already work
uvicorn app.main:app --reload
```

API docs: http://127.0.0.1:8000/docs

### With Docker (API + PostgreSQL)

```bash
docker compose up --build
```

### Enabling LLM-augmented generation

Set in `.env` or the environment:

```bash
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
LLM_MODEL=gpt-4o-mini          # or any OpenAI-compatible model
OPENAI_BASE_URL=https://api.openai.com/v1   # point elsewhere for local/self-hosted models
```

Check `GET /health` to confirm `llm_enabled: true`.

## Running tests

```bash
pytest
```

15 tests covering the classifier's rule set, RAG retrieval/grounding, the
LLM fallback path, and the API endpoints end-to-end.

## Reindexing the knowledge base

The vector store auto-ingests new/changed Markdown files in
`data/knowledge_base/` on startup. To force a full rebuild:

```bash
curl -X POST http://127.0.0.1:8000/knowledge-base/reindex
```
