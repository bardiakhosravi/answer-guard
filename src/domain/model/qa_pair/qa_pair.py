from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from src.domain.exceptions import DomainException
from src.domain.model.qa_pair.ingestion_method import IngestionMethod
from src.domain.model.qa_pair.qa_pair_id import QAPairId
from src.domain.model.qa_pair.source_hash import SourceHash


@dataclass(eq=False)
class QAPair:
    id: QAPairId
    question_text: str
    answer_text: str
    source_system_id: str
    source_hash: SourceHash
    ingestion_method: IngestionMethod
    captured_at: datetime
    source_timestamp: datetime | None = None
    external_id: str | None = None
    ingestion_run_id: str | None = None
    metadata: dict = field(default_factory=dict)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, QAPair):
            return NotImplemented
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)

    @classmethod
    def create(
        cls,
        question_text: str,
        answer_text: str,
        source_system_id: str,
        ingestion_method: IngestionMethod,
        source_timestamp: datetime | None = None,
        external_id: str | None = None,
        ingestion_run_id: str | None = None,
        metadata: dict | None = None,
    ) -> "QAPair":
        if not question_text or not question_text.strip():
            raise DomainException("QAPair: question_text must not be empty")
        if not answer_text or not answer_text.strip():
            raise DomainException("QAPair: answer_text must not be empty")
        if not source_system_id or not source_system_id.strip():
            raise DomainException("QAPair: source_system_id must not be empty")

        return cls(
            id=QAPairId.generate(),
            question_text=question_text,
            answer_text=answer_text,
            source_system_id=source_system_id,
            source_hash=SourceHash.compute(question_text, answer_text, source_system_id),
            ingestion_method=ingestion_method,
            captured_at=datetime.now(timezone.utc),
            source_timestamp=source_timestamp,
            external_id=external_id,
            ingestion_run_id=ingestion_run_id,
            metadata=metadata or {},
        )
