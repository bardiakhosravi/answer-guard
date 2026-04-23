from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from src.domain.model.qa_pair.qa_pair import QAPair
    from src.domain.model.qa_pair.qa_pair_id import QAPairId
    from src.domain.model.qa_pair.source_hash import SourceHash


class QAPairRepository(ABC):
    @abstractmethod
    def save(self, qa_pair: "QAPair") -> bool:
        """
        Persist a QAPair. Returns True if the record was newly inserted,
        False if it was a duplicate (same source_hash) and was silently ignored.
        """

    @abstractmethod
    def find_by_hash(self, source_hash: "SourceHash") -> Optional["QAPair"]:
        """Return QAPair matching the given source hash, or None."""

    @abstractmethod
    def find_by_id(self, qa_pair_id: "QAPairId") -> Optional["QAPair"]:
        """Return QAPair by internal ID, or None."""

    @abstractmethod
    def count_by_source(self, source_system_id: str) -> int:
        """Total Q&A pairs stored for a source system."""

    @abstractmethod
    def count_by_source_since(self, source_system_id: str, since: datetime) -> int:
        """Count Q&A pairs for a source system captured after the given timestamp."""

    @abstractmethod
    def list_paginated(
        self,
        page: int,
        page_size: int,
        source_system_id: str | None = None,
        search: str | None = None,
    ) -> tuple[list["QAPair"], int]:
        """
        Return a page of Q&A pairs plus the total count matching the filters.
        Ordered by captured_at DESC. Search filters on question_text OR answer_text.
        """
