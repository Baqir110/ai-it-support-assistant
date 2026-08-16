import logging

from fastapi import APIRouter, Query

from app.config.settings import get_settings
from app.db.models import AnalysisLog
from app.db.session import get_session
from app.models.schemas import KnowledgeSearchResult, SupportRequest, SupportResponse
from app.rag.vector_store import get_vector_store
from app.services.troubleshooter import analyze_issue

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/")
def root():
    return {"message": "AI IT Support Assistant API is running", "status": "online"}


@router.get("/health")
def health_check():
    settings = get_settings()
    return {
        "status": "healthy",
        "llm_enabled": settings.llm_enabled,
        "db_enabled": settings.db_enabled,
        "embedding_backend": settings.embedding_backend,
    }


@router.post("/support/analyze", response_model=SupportResponse)
def analyze_support_issue(request: SupportRequest):
    analysis = analyze_issue(request.issue)

    with get_session() as session:
        if session is not None:
            session.add(
                AnalysisLog(
                    issue=request.issue,
                    category=analysis.category,
                    severity=analysis.severity,
                    confidence=analysis.confidence,
                    escalation_required=analysis.escalation_required,
                    generated_by=analysis.generated_by,
                    source_count=len(analysis.sources),
                )
            )

    return SupportResponse(issue=request.issue, analysis=analysis)


@router.get("/knowledge-base/search", response_model=list[KnowledgeSearchResult])
def search_knowledge_base(q: str = Query(..., min_length=2)):
    return get_vector_store().search(q)


@router.post("/knowledge-base/reindex")
def reindex_knowledge_base():
    count = get_vector_store().reindex()
    return {"status": "reindexed", "chunks": count}
