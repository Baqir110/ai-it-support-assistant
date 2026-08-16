import os
from typing import List, Dict, Any

# Replace legacy community imports
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

CHROMA_PATH = "data/chroma_db"

# Lazy-loaded embedding instance to save startup time
_embedding_function = None


def get_embedding_function():
    global _embedding_function
    if _embedding_function is None:
        _embedding_function = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    return _embedding_function


def search_knowledge_base(query: str, top_k: int = 3) -> List[Dict[str, Any]]:
    if not os.path.exists(CHROMA_PATH):
        return []

    vector_db = Chroma(
        persist_directory=CHROMA_PATH, embedding_function=get_embedding_function()
    )

    results = vector_db.similarity_search_with_score(query, k=top_k)

    retrieved_docs = []
    for doc, score in results:
        # Extract filename from path for clean source reporting
        source_path = doc.metadata.get("source", "general_knowledge")
        clean_source = os.path.basename(source_path)

        retrieved_docs.append(
            {"content": doc.page_content, "source": clean_source, "score": float(score)}
        )

    return retrieved_docs
