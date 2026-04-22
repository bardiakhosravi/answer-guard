from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from src.application.queries.get_ingestion_status_query import GetIngestionStatusQuery
from src.domain.exceptions import DomainException


class IngestionRunNotFoundError(DomainException):
    """Raised when an ingestion run ID is queried but does not exist."""


@dataclass
class IngestionRunSummary:
    run_id: str
    status: str
    started_at: str
    completed_at: str | None
    records_processed: int
    records_skipped: int
    last_checkpoint: int | None
    errors: list[dict] = field(default_factory=list)


@dataclass
class SourceSummary:
    source_system_id: str
    total_records: int
    last_ingested_at: str | None
    runtime_captures_last_24h: int
    last_import_run: IngestionRunSummary | None


@dataclass
class IngestionStatusResponse:
    total_qa_pairs: int
    sources: list[SourceSummary]


class GetIngestionStatusPort(ABC):
    @abstractmethod
    def execute(self, query: GetIngestionStatusQuery) -> IngestionStatusResponse:
        """Return ingestion status summary, optionally filtered by source or run ID."""
