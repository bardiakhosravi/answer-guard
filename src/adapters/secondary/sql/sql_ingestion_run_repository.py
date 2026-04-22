from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.adapters.secondary.sql.models.ingestion_run_model import IngestionRunModel
from src.domain.model.ingestion_run.ingestion_run import IngestionRun
from src.domain.model.ingestion_run.ingestion_run_id import IngestionRunId
from src.domain.model.ingestion_run.ingestion_status import IngestionStatus
from src.domain.ports.ingestion_run_repository import IngestionRunRepository


class SqlIngestionRunRepository(IngestionRunRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def save(self, run: IngestionRun) -> None:
        existing = self._session.get(IngestionRunModel, run.id.value)
        if existing:
            existing.status = run.status.value
            existing.completed_at = run.completed_at
            existing.records_processed = run.records_processed
            existing.records_skipped = run.records_skipped
            existing.last_checkpoint = run.last_checkpoint
            existing.error_log = run.error_log
        else:
            self._session.add(self._to_model(run))
        self._session.commit()

    def find_by_id(self, run_id: IngestionRunId) -> IngestionRun | None:
        model = self._session.get(IngestionRunModel, run_id.value)
        return self._to_domain(model) if model else None

    def find_active_for_source(self, source_system_id: str) -> IngestionRun | None:
        model = self._session.execute(
            select(IngestionRunModel)
            .where(
                IngestionRunModel.source_system_id == source_system_id,
                IngestionRunModel.status.in_(
                    [IngestionStatus.RUNNING.value, IngestionStatus.RESUMED.value]
                ),
            )
            .order_by(IngestionRunModel.started_at.desc())
            .limit(1)
        ).scalar_one_or_none()
        return self._to_domain(model) if model else None

    def find_latest_for_source(self, source_system_id: str) -> IngestionRun | None:
        model = self._session.execute(
            select(IngestionRunModel)
            .where(IngestionRunModel.source_system_id == source_system_id)
            .order_by(IngestionRunModel.started_at.desc())
            .limit(1)
        ).scalar_one_or_none()
        return self._to_domain(model) if model else None

    def find_latest_per_source(self) -> list[IngestionRun]:
        subq = (
            select(
                IngestionRunModel.source_system_id,
                IngestionRunModel.started_at.label("max_started"),
            )
            .group_by(IngestionRunModel.source_system_id)
            .subquery()
        )
        models = self._session.execute(
            select(IngestionRunModel).join(
                subq,
                (IngestionRunModel.source_system_id == subq.c.source_system_id)
                & (IngestionRunModel.started_at == subq.c.max_started),
            )
        ).scalars().all()
        return [self._to_domain(m) for m in models]

    def _to_model(self, run: IngestionRun) -> IngestionRunModel:
        return IngestionRunModel(
            id=run.id.value,
            source_system_id=run.source_system_id,
            started_at=run.started_at,
            completed_at=run.completed_at,
            status=run.status.value,
            records_processed=run.records_processed,
            records_skipped=run.records_skipped,
            last_checkpoint=run.last_checkpoint,
            error_log=run.error_log or None,
            config_snapshot=run.config_snapshot,
        )

    def _to_domain(self, model: IngestionRunModel) -> IngestionRun:
        return IngestionRun(
            id=IngestionRunId(model.id),
            source_system_id=model.source_system_id,
            status=IngestionStatus(model.status),
            started_at=model.started_at,
            config_snapshot=model.config_snapshot or {},
            completed_at=model.completed_at,
            records_processed=model.records_processed,
            records_skipped=model.records_skipped,
            last_checkpoint=model.last_checkpoint,
            error_log=model.error_log or [],
        )
