"""ChromaDB-backed vector store for the IT knowledge base."""

from functools import lru_cache

import chromadb

from app.config.settings import get_settings
from app.models.schemas import KnowledgeSearchResult
from app.rag.embeddings import get_embedding_function
from app.rag.loader import load_documents


class VectorStore:
    def __init__(self):
        settings = get_settings()
        settings.chroma_persist_dir.mkdir(parents=True, exist_ok=True)

        self._client = chromadb.PersistentClient(path=str(settings.chroma_persist_dir))
        self._embedding_fn = get_embedding_function()
        self._collection = self._client.get_or_create_collection(
            name=settings.chroma_collection_name,
            embedding_function=self._embedding_fn,
            metadata={"hnsw:space": "cosine"},
        )
        self._ensure_ingested()

    def _ensure_ingested(self) -> None:
        """Ingests the knowledge base on first run, or when it has changed."""
        chunks = load_documents()
        chunk_ids = [c.id for c in chunks]
        existing_ids = set(self._collection.get(ids=chunk_ids).get("ids", []))
        new_chunks = [c for c in chunks if c.id not in existing_ids]
        if not new_chunks:
            return

        self._collection.upsert(
            ids=[c.id for c in new_chunks],
            documents=[c.content for c in new_chunks],
            metadatas=[{"source": c.source} for c in new_chunks],
        )

    def reindex(self) -> int:
        """Force a full re-ingestion of the knowledge base. Returns chunk count."""
        settings = get_settings()
        self._client.delete_collection(settings.chroma_collection_name)
        self._collection = self._client.get_or_create_collection(
            name=settings.chroma_collection_name,
            embedding_function=self._embedding_fn,
            metadata={"hnsw:space": "cosine"},
        )
        chunks = load_documents()
        if chunks:
            self._collection.upsert(
                ids=[c.id for c in chunks],
                documents=[c.content for c in chunks],
                metadatas=[{"source": c.source} for c in chunks],
            )
        return len(chunks)

    def search(
        self, query: str, top_k: int | None = None
    ) -> list[KnowledgeSearchResult]:
        settings = get_settings()
        k = top_k or settings.retrieval_top_k
        if self._collection.count() == 0:
            return []

        results = self._collection.query(
            query_texts=[query], n_results=min(k, self._collection.count())
        )

        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        output = []
        for doc, meta, distance in zip(documents, metadatas, distances):
            # Cosine distance -> similarity score in [0, 1]
            similarity = max(0.0, 1 - distance / 2)
            output.append(
                KnowledgeSearchResult(
                    source=meta.get("source", "unknown"),
                    content=doc,
                    score=round(similarity, 4),
                )
            )
        return output


@lru_cache
def get_vector_store() -> VectorStore:
    return VectorStore()
