"""Embedding backends for the RAG pipeline.

Two implementations are provided behind one interface so the retrieval
quality/cost trade-off is a config change, not a code change:

- HashingEmbeddingFunction: scikit-learn HashingVectorizer -> dense vector.
  Deterministic, stateless, no model download, no network call. Good enough
  for keyword-heavy IT documentation and lets the whole pipeline run in
  CI/offline environments.
- OpenAIEmbeddingFunction: calls an OpenAI-compatible /embeddings endpoint.
  Higher retrieval quality (real semantic similarity), used automatically
  once OPENAI_API_KEY + embedding_backend=openai are configured.
"""

import numpy as np
from chromadb import Documents, EmbeddingFunction, Embeddings
from sklearn.feature_extraction.text import HashingVectorizer

from app.config.settings import get_settings


class HashingEmbeddingFunction(EmbeddingFunction[Documents]):
    """Chroma-compatible embedding function backed by a hashing vectorizer."""

    def __init__(self, n_features: int = 384):
        self._vectorizer = HashingVectorizer(
            n_features=n_features,
            alternate_sign=False,
            norm="l2",
            ngram_range=(1, 2),
        )

    def __call__(self, input: Documents) -> Embeddings:  # noqa: A002 (chroma API)
        matrix = self._vectorizer.transform(list(input))
        return matrix.toarray().astype(np.float32).tolist()

    @staticmethod
    def name() -> str:
        return "hashing-vectorizer-v1"

    def get_config(self) -> dict:
        return {"n_features": self._vectorizer.n_features}

    @staticmethod
    def build_from_config(config: dict) -> "HashingEmbeddingFunction":
        return HashingEmbeddingFunction(n_features=config.get("n_features", 384))


class OpenAIEmbeddingFunction(EmbeddingFunction[Documents]):
    """Chroma-compatible embedding function using an OpenAI-compatible API."""

    def __init__(self, model: str = "text-embedding-3-small"):
        self._model = model

    def __call__(self, input: Documents) -> Embeddings:  # noqa: A002
        from openai import OpenAI

        settings = get_settings()
        client = OpenAI(
            api_key=settings.openai_api_key, base_url=settings.openai_base_url
        )
        response = client.embeddings.create(model=self._model, input=list(input))
        return [item.embedding for item in response.data]

    def name(self) -> str:  # instance method: name depends on configured model
        return f"openai-{self._model}"


def get_embedding_function():
    settings = get_settings()
    if settings.embedding_backend == "openai" and settings.openai_api_key:
        return OpenAIEmbeddingFunction()
    return HashingEmbeddingFunction(n_features=settings.embedding_dimensions)
