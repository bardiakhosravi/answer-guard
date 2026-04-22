from datetime import datetime

from sqlalchemy import DateTime, Index, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from src.configuration.database_config import Base


class QAPairModel(Base):
    __tablename__ = "qa_pairs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    answer_text: Mapped[str] = mapped_column(Text, nullable=False)
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    source_timestamp: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    source_system_id: Mapped[str] = mapped_column(String(255), nullable=False)
    external_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    ingestion_method: Mapped[str] = mapped_column(String(32), nullable=False)
    ingestion_run_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    metadata_: Mapped[dict | None] = mapped_column(
        "metadata",
        JSON().with_variant(JSONB(), "postgresql"),
        nullable=True,
    )

    __table_args__ = (
        UniqueConstraint("source_hash", name="uq_qa_pairs_source_hash"),
        Index("idx_qa_pairs_source_system", "source_system_id"),
        Index("idx_qa_pairs_external_id", "external_id"),
        Index("idx_qa_pairs_captured_at", "captured_at"),
    )
