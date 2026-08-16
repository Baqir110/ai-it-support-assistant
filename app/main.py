from fastapi import FastAPI

from app.api.routes import router
from app.config.settings import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description="A RAG-backed system for analysing and troubleshooting IT issues.",
    version=settings.app_version,
)

app.include_router(router)
