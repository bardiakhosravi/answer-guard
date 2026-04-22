from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from src.domain.exceptions import DomainException
from src.domain.model.ingestion_run.ingestion_run_id import IngestionRunId
from src.domain.model.ingestion_run.ingestion_status import IngestionStatus


@dataclass(eq=False)
class IngestionRun:
    id: IngestionRunId
    source_system_id: str
    status: IngestionStatus
    started_at: datetime
    config_snapshot: dict
    completed_at: datetime | None = None
    records_processed: int = 0
    records_skipped: int = 0
    last_checkpoint: int | None = None
    error_log: list[dict] = field(default_factory=list)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, IngestionRun):
            return NotImplemented
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)

    @classmethod
    def start(cls, source_system_id: str, config_snapshot: dict) -> "IngestionRun":
        """Create a new RUNNING ingestion run. config_snapshot is the serialised source config."""
        return cls(
            id=IngestionRunId.generate(),
            source_system_id=source_system_id,
            status=IngestionStatus.RUNNING,
            started_at=datetime.now(timezone.utc),
            config_snapshot=config_snapshot,
        )

    def resume(self) -> None:
        if self.status != IngestionStatus.FAILED:
            raise DomainException(
                f"IngestionRun can only be resumed from FAILED state, current: {self.status}"
            )
        self.status = IngestionStatus.RESUMED

    def record_progress(self, processed: int, skipped: int, checkpoint: int) -> None:
        if self.status not in (IngestionStatus.RUNNING, IngestionStatus.RESUMED):
            raise DomainException(
                f"Cannot record progress on run with status: {self.status}"
            )
        self.records_processed += processed
        self.records_skipped += skipped
        self.last_checkpoint = checkpoint

    def log_error(self, index: int, reason: str) -> None:
        self.error_log.append({"index": index, "reason": reason})

    def complete(self) -> None:
        if self.status not in (IngestionStatus.RUNNING, IngestionStatus.RESUMED):
            raise DomainException(
                f"Cannot complete run with status: {self.status}"
            )
        self.status = IngestionStatus.COMPLETED
        self.completed_at = datetime.now(timezone.utc)

    def fail(self, reason: str) -> None:
        if self.status not in (IngestionStatus.RUNNING, IngestionStatus.RESUMED):
            raise DomainException(
                f"Cannot fail run with status: {self.status}"
            )
        self.status = IngestionStatus.FAILED
        self.completed_at = datetime.now(timezone.utc)
        self.error_log.append({"index": -1, "reason": reason})
