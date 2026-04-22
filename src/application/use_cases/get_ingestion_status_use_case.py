from __future__ import annotations

from datetime import datetime, timedelta, timezone

from src.application.ports.primary.get_ingestion_status_port import (
    GetIngestionStatusPort,
    IngestionRunNotFoundError,
    IngestionRunSummary,
    IngestionStatusResponse,
    SourceSummary,
)
from src.application.queries.get_ingestion_status_query import GetIngestionStatusQuery
from src.domain.model.ingestion_run.ingestion_run_id import IngestionRunId
from src.domain.ports.ingestion_run_repository import IngestionRunRepository
from src.domain.ports.qa_pair_repository import QAPairRepository

# Re-export so callers can import NotFoundError from this module for backwards compatibility
NotFoundError = IngestionRunNotFoundError


class GetIngestionStatusUseCase(GetIngestionStatusPort):
    def __init__(
        self,
        qa_pair_repository: QAPairRepository,
        ingestion_run_repository: IngestionRunRepository,
    ) -> None:
        self._qa_repo = qa_pair_repository
        self._run_repo = ingestion_run_repository

    def execute(self, query: GetIngestionStatusQuery) -> IngestionStatusResponse:
        if query.run_id:
            return self._single_run_response(query.run_id)
        return self._summary_response(query.source_system_id)

    def _single_run_response(self, run_id: str) -> IngestionStatusResponse:
        run = self._run_repo.find_by_id(IngestionRunId(run_id))
        if not run:
            raise NotFoundError(f"No ingestion run found with ID: {run_id}")
        summary = self._run_to_summary(run)
        total = self._qa_repo.count_by_source(run.source_system_id)
        return IngestionStatusResponse(
            total_qa_pairs=total,
            sources=[
                SourceSummary(
                    source_system_id=run.source_system_id,
                    total_records=total,
                    last_ingested_at=run.completed_at.isoformat() if run.completed_at else None,
                    runtime_captures_last_24h=0,
                    last_import_run=summary,
                )
            ],
        )

    def _summary_response(self, source_system_id: str | None) -> IngestionStatusResponse:
        since_24h = datetime.now(timezone.utc) - timedelta(hours=24)
        latest_runs = self._run_repo.find_latest_per_source()

        if source_system_id:
            latest_runs = [r for r in latest_runs if r.source_system_id == source_system_id]

        sources = []
        total_all = 0

        for run in latest_runs:
            total = self._qa_repo.count_by_source(run.source_system_id)
            captures_24h = self._qa_repo.count_by_source_since(run.source_system_id, since_24h)
            total_all += total
            sources.append(
                SourceSummary(
                    source_system_id=run.source_system_id,
                    total_records=total,
                    last_ingested_at=run.completed_at.isoformat() if run.completed_at else None,
                    runtime_captures_last_24h=captures_24h,
                    last_import_run=self._run_to_summary(run),
                )
            )

        if not sources and source_system_id:
            total = self._qa_repo.count_by_source(source_system_id)
            captures_24h = self._qa_repo.count_by_source_since(source_system_id, since_24h)
            total_all = total
            sources.append(
                SourceSummary(
                    source_system_id=source_system_id,
                    total_records=total,
                    last_ingested_at=None,
                    runtime_captures_last_24h=captures_24h,
                    last_import_run=None,
                )
            )

        return IngestionStatusResponse(total_qa_pairs=total_all, sources=sources)

    @staticmethod
    def _run_to_summary(run) -> IngestionRunSummary:
        return IngestionRunSummary(
            run_id=run.id.value,
            status=run.status.value,
            started_at=run.started_at.isoformat(),
            completed_at=run.completed_at.isoformat() if run.completed_at else None,
            records_processed=run.records_processed,
            records_skipped=run.records_skipped,
            last_checkpoint=run.last_checkpoint,
            errors=run.error_log,
        )
