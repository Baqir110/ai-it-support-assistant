import logging
from contextlib import contextmanager
from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config.settings import get_settings
from app.db.models import Base

logger = logging.getLogger(__name__)


@lru_cache
def get_engine():
    settings = get_settings()
    if not settings.db_enabled:
        return None
    engine = create_engine(settings.database_url, pool_pre_ping=True)
    Base.metadata.create_all(engine)
    return engine


@contextmanager
def get_session():
    """Yields a DB session, or None if persistence isn't configured.

    Callers must handle the None case - logging is best-effort and should
    never block or fail the API response.
    """
    engine = get_engine()
    if engine is None:
        yield None
        return

    SessionLocal = sessionmaker(bind=engine, class_=Session)
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        logger.exception("DB session error during analysis logging.")
    finally:
        session.close()
