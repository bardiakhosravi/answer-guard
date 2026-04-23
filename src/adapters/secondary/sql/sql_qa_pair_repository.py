from __future__ import annotations

from datetime import datetime

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from src.adapters.secondary.sql.models.qa_pair_model import QAPairModel
from src.domain.model.qa_pair.ingestion_method import IngestionMethod
from src.domain.model.qa_pair.qa_pair import QAPair
from src.domain.model.qa_pair.qa_pair_id import QAPairId
from src.domain.model.qa_pair.source_hash import SourceHash
from src.domain.ports.qa_pair_repository import QAPairRepository


class SqlQAPairRepository(QAPairRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def save(self, qa_pair: QAPair) -> bool:
        """Insert if new. Returns True if inserted, False if duplicate (silently ignored)."""
        table = QAPairModel.__table__
        values = {
            "id": qa_pair.id.value,
            "question_text": qa_pair.question_text,
            "answer_text": qa_pair.answer_text,
            "captured_at": qa_pair.captured_at,
            "source_timestamp": qa_pair.source_timestamp,
            "source_system_id": qa_pair.source_system_id,
            "external_id": qa_pair.external_id,
            "source_hash": qa_pair.source_hash.value,
            "ingestion_method": qa_pair.ingestion_method.value,
            "ingestion_run_id": qa_pair.ingestion_run_id,
            "metadata": qa_pair.metadata or None,
        }
        dialect = self._session.bind.dialect.name  # type: ignore[union-attr]
        if dialect == "sqlite":
            from sqlalchemy.dialects.sqlite import insert as sqlite_insert
            stmt = sqlite_insert(table).values(**values).prefix_with("OR IGNORE")
            result = self._session.execute(stmt)
            was_new = result.rowcount > 0
        else:
            from sqlalchemy.dialects.postgresql import insert as pg_insert
            stmt = pg_insert(table).values(**values).on_conflict_do_nothing(  # type: ignore[assignment]
                index_elements=["source_hash"]
            )
            result = self._session.execute(stmt)
            was_new = result.rowcount > 0
        self._session.commit()
        return was_new

    def find_by_hash(self, source_hash: SourceHash) -> QAPair | None:
        model = self._session.execute(
            select(QAPairModel).where(QAPairModel.source_hash == source_hash.value)
        ).scalar_one_or_none()
        return self._to_domain(model) if model else None

    def find_by_id(self, qa_pair_id: QAPairId) -> QAPair | None:
        model = self._session.get(QAPairModel, qa_pair_id.value)
        return self._to_domain(model) if model else None

    def count_by_source(self, source_system_id: str) -> int:
        result = self._session.execute(
            select(func.count()).where(QAPairModel.source_system_id == source_system_id)
        ).scalar_one()
        return result or 0

    def count_by_source_since(self, source_system_id: str, since: datetime) -> int:
        result = self._session.execute(
            select(func.count()).where(
                QAPairModel.source_system_id == source_system_id,
                QAPairModel.captured_at >= since,
            )
        ).scalar_one()
        return result or 0

    def list_paginated(
        self,
        page: int,
        page_size: int,
        source_system_id: str | None = None,
        search: str | None = None,
    ) -> tuple[list[QAPair], int]:
        if page < 1:
            page = 1
        if page_size < 1:
            page_size = 50

        filters = []
        if source_system_id:
            filters.append(QAPairModel.source_system_id == source_system_id)
        if search:
            pattern = f"%{search}%"
            filters.append(
                or_(
                    QAPairModel.question_text.ilike(pattern),
                    QAPairModel.answer_text.ilike(pattern),
                )
            )

        total = self._session.execute(
            select(func.count()).select_from(QAPairModel).where(*filters)
        ).scalar_one() or 0

        models = (
            self._session.execute(
                select(QAPairModel)
                .where(*filters)
                .order_by(QAPairModel.captured_at.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
            .scalars()
            .all()
        )
        return [self._to_domain(m) for m in models], total

    def _to_domain(self, model: QAPairModel) -> QAPair:
        return QAPair(
            id=QAPairId(model.id),
            question_text=model.question_text,
            answer_text=model.answer_text,
            source_system_id=model.source_system_id,
            source_hash=SourceHash(model.source_hash),
            ingestion_method=IngestionMethod(model.ingestion_method),
            captured_at=model.captured_at,
            source_timestamp=model.source_timestamp,
            external_id=model.external_id,
            ingestion_run_id=model.ingestion_run_id,
            metadata=model.metadata_ or {},
        )
