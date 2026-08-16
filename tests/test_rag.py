import pytest
from app.rag.knowledge_base import search_knowledge_base


def test_knowledge_base_retrieval_structure():
    query = "printer paper jam error"
    results = search_knowledge_base(query, top_k=2)

    assert isinstance(results, list)
    if len(results) > 0:
        doc = results[0]
        assert "content" in doc
        assert "source" in doc
        assert "score" in doc
        assert isinstance(doc["content"], str)
        assert len(doc["source"]) > 0


def test_knowledge_base_empty_query():
    results = search_knowledge_base("", top_k=1)
    assert isinstance(results, list)
