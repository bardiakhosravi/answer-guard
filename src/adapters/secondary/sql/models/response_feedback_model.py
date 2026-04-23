from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.configuration.database_config import Base


class ResponseFeedbackModel(Base):
    __tablename__ = "response_feedback"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    source_qa_pair_id: Mapped[str] = mapped_column(String(36), nullable=False)
    excerpt: Mapped[str] = mapped_column(Text, nullable=False)
    span_start: Mapped[int | None] = mapped_column(Integer, nullable=True)
    span_end: Mapped[int | None] = mapped_column(Integer, nullable=True)
    problem: Mapped[str] = mapped_column(Text, nullable=False)
    desired_behavior: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        CheckConstraint(
            "(span_start IS NULL AND span_end IS NULL) OR "
            "(span_start >= 0 AND span_end > span_start)",
            name="ck_response_feedback_span_valid",
        ),
        Index("idx_response_feedback_source_qa_pair_id", "source_qa_pair_id"),
        Index("idx_response_feedback_created_at", "created_at"),
    )
