from __future__ import annotations

from src.application.ports.primary.list_qa_pairs_port import (
    ListQAPairsPort,
    ListQAPairsResponse,
    QAPairSummary,
)
from src.application.queries.list_qa_pairs_query import ListQAPairsQuery
from src.domain.model.qa_pair.qa_pair import QAPair
from src.domain.ports.qa_pair_repository import QAPairRepository


class ListQAPairsUseCase(ListQAPairsPort):
    def __init__(self, qa_pair_repository: QAPairRepository) -> None:
        self._qa_repo = qa_pair_repository

    def execute(self, query: ListQAPairsQuery) -> ListQAPairsResponse:
        items, total = self._qa_repo.list_paginated(
            page=query.page,
            page_size=query.page_size,
            source_system_id=query.source_system_id,
            search=query.search,
        )
        return ListQAPairsResponse(
            total=total,
            page=query.page,
            page_size=query.page_size,
            items=[self._to_summary(p) for p in items],
        )

    @staticmethod
    def _to_summary(pair: QAPair) -> QAPairSummary:
        return QAPairSummary(
            id=pair.id.value,
            question_text=pair.question_text,
            answer_text=pair.answer_text,
            source_system_id=pair.source_system_id,
            captured_at=pair.captured_at.isoformat(),
            source_timestamp=pair.source_timestamp.isoformat() if pair.source_timestamp else None,
            ingestion_method=pair.ingestion_method.value,
            external_id=pair.external_id,
            metadata=dict(pair.metadata or {}),
        )
