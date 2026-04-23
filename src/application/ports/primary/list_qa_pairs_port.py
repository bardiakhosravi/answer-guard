from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from src.application.queries.list_qa_pairs_query import ListQAPairsQuery


@dataclass(frozen=True)
class QAPairSummary:
    id: str
    question_text: str
    answer_text: str
    source_system_id: str
    captured_at: str
    source_timestamp: str | None
    ingestion_method: str
    external_id: str | None
    metadata: dict = field(default_factory=dict)


@dataclass(frozen=True)
class ListQAPairsResponse:
    total: int
    page: int
    page_size: int
    items: list[QAPairSummary]


class ListQAPairsPort(ABC):
    @abstractmethod
    def execute(self, query: ListQAPairsQuery) -> ListQAPairsResponse:
        """Return a paginated list of stored Q&A pairs."""
