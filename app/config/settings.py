from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    """
    Central application configuration.

    Every external dependency (LLM provider, embedding backend, database)
    is controlled here and can be overridden with environment variables or
    a .env file, so the same codebase runs in three modes:

      1. Fully offline (default) — deterministic rule-based generation +
         local hashing embeddings. No API keys, no internet access needed.
      2. LLM-augmented — set LLM_PROVIDER=openai and OPENAI_API_KEY to route
         generation through any OpenAI-compatible chat completions endpoint
         (OpenAI, Azure OpenAI, together.ai, local vLLM/Ollama, etc via
         OPENAI_BASE_URL).
      3. Persisted — set DATABASE_URL to log every request/response to
         PostgreSQL for analytics/evaluation.
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "AI IT Support Assistant"
    app_version: str = "1.0.0"

    # --- LLM configuration -------------------------------------------------
    llm_provider: str = "none"  # "none" (rule-based fallback) | "openai"
    openai_api_key: str | None = None
    openai_base_url: str = "https://api.openai.com/v1"
    llm_model: str = "gpt-4o-mini"
    llm_temperature: float = 0.2

    # --- RAG / vector store configuration ----------------------------------
    knowledge_base_dir: Path = BASE_DIR / "data" / "knowledge_base"
    chroma_persist_dir: Path = BASE_DIR / "data" / "chroma"
    chroma_collection_name: str = "it_knowledge_base"
    embedding_backend: str = "hashing"  # "hashing" (offline) | "openai"
    embedding_dimensions: int = 384
    retrieval_top_k: int = 3

    # --- Persistence ---------------------------------------------------------
    database_url: str | None = None  # e.g. postgresql+psycopg2://user:pass@host/db

    @property
    def llm_enabled(self) -> bool:
        return self.llm_provider == "openai" and bool(self.openai_api_key)

    @property
    def db_enabled(self) -> bool:
        return bool(self.database_url)


@lru_cache
def get_settings() -> Settings:
    return Settings()
