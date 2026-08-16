from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class AnalysisLog(Base):
    """One row per /support/analyze call, for evaluation and analytics."""

    __tablename__ = "analysis_logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    issue: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(32), nullable=False)
    severity: Mapped[str] = mapped_column(String(16), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    escalation_required: Mapped[bool] = mapped_column(Boolean, nullable=False)
    generated_by: Mapped[str] = mapped_column(String(16), nullable=False)
    source_count: Mapped[int] = mapped_column(nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
