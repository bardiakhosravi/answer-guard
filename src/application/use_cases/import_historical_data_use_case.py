from __future__ import annotations

from src.application.commands.import_historical_data_command import ImportHistoricalDataCommand
from src.application.ports.primary.import_historical_data_port import (
    FieldMappingValidationError,
    ImportAlreadyRunningError,
    ImportHistoricalDataPort,
    ImportHistoricalDataResponse,
)
from src.application.ports.secondary.bigquery_source_port import BigQuerySourcePort
from src.application.values.source_connector import SourceConnector
from src.domain.model.ingestion_run.ingestion_run import IngestionRun
from src.domain.model.ingestion_run.ingestion_status import IngestionStatus
from src.domain.model.qa_pair.ingestion_method import IngestionMethod
from src.domain.model.qa_pair.qa_pair import QAPair
from src.domain.ports.ingestion_run_repository import IngestionRunRepository
from src.domain.ports.qa_pair_repository import QAPairRepository


class ImportHistoricalDataUseCase(ImportHistoricalDataPort):
    def __init__(
        self,
        bigquery_source: BigQuerySourcePort,
        qa_pair_repository: QAPairRepository,
        ingestion_run_repository: IngestionRunRepository,
    ) -> None:
        self._bq = bigquery_source
        self._qa_repo = qa_pair_repository
        self._run_repo = ingestion_run_repository

    def execute(self, command: ImportHistoricalDataCommand) -> ImportHistoricalDataResponse:
        connector = command.source_connector

        # 1. Validate field mapping against actual source schema
        available_columns = self._bq.get_schema(connector)
        fm = connector.field_mapping
        for col_name, col_value in [
            ("question_column", fm.question_column),
            ("answer_column", fm.answer_column),
        ]:
            if col_value not in available_columns:
                raise FieldMappingValidationError(
                    f"Column '{col_value}' ({col_name}) not found in source table. "
                    f"Available: {available_columns}"
                )
        if fm.timestamp_column and fm.timestamp_column not in available_columns:
            raise FieldMappingValidationError(
                f"Column '{fm.timestamp_column}' (timestamp_column) not found. "
                f"Available: {available_columns}"
            )

        # 2. Check for conflicting active runs; resume from FAILED if one exists
        active_run = self._run_repo.find_active_for_source(connector.source_system_id)
        if active_run and active_run.status == IngestionStatus.RUNNING:
            raise ImportAlreadyRunningError(
                f"Import already running for source '{connector.source_system_id}'. "
                f"Run ID: {active_run.id.value}"
            )

        failed_run = self._run_repo.find_latest_for_source(connector.source_system_id)
        if failed_run and failed_run.status == IngestionStatus.FAILED:
            run = failed_run
            run.resume()
            start_index = run.last_checkpoint or 0
        else:
            run = IngestionRun.start(
                source_system_id=connector.source_system_id,
                config_snapshot=connector.to_dict(),
            )
            start_index = 0

        self._run_repo.save(run)

        # 3. Stream and import rows page by page
        try:
            batch_processed = 0
            batch_skipped = 0

            for row_index, row in enumerate(
                self._bq.read_rows(connector, start_index=start_index), start=start_index
            ):
                try:
                    qa_pair = self._build_qa_pair(row, connector, run.id.value)
                    was_new = self._qa_repo.save(qa_pair)
                    if was_new:
                        batch_processed += 1
                    else:
                        batch_skipped += 1
                        run.log_error(row_index, "duplicate record")
                except Exception as exc:
                    batch_skipped += 1
                    run.log_error(row_index, str(exc))

                # Checkpoint every page_size rows
                if (row_index + 1) % connector.page_size == 0:
                    run.record_progress(batch_processed, batch_skipped, row_index + 1)
                    self._run_repo.save(run)
                    batch_processed = 0
                    batch_skipped = 0

            if batch_processed or batch_skipped:
                run.record_progress(
                    batch_processed,
                    batch_skipped,
                    start_index + run.records_processed + batch_processed + batch_skipped,
                )

            run.complete()
            self._run_repo.save(run)

        except Exception as exc:
            run.fail(str(exc))
            self._run_repo.save(run)
            raise

        return ImportHistoricalDataResponse(
            ingestion_run_id=run.id.value,
            status=run.status.value,
            message=(
                f"Import completed. Processed: {run.records_processed}, "
                f"Skipped: {run.records_skipped}"
            ),
        )

    def _build_qa_pair(self, row: dict, connector: SourceConnector, run_id: str) -> QAPair:
        fm = connector.field_mapping
        question = row.get(fm.question_column, "")
        answer = row.get(fm.answer_column, "")
        source_timestamp = row.get(fm.timestamp_column) if fm.timestamp_column else None
        external_id = row.get(fm.external_id_column) if fm.external_id_column else None
        metadata = {
            k: row.get(v)
            for k, v in fm.metadata_columns.items()
            if row.get(v) is not None
        }
        return QAPair.create(
            question_text=str(question),
            answer_text=str(answer),
            source_system_id=connector.source_system_id,
            ingestion_method=IngestionMethod.HISTORICAL_IMPORT,
            source_timestamp=source_timestamp,
            external_id=str(external_id) if external_id else None,
            ingestion_run_id=run_id,
            metadata=metadata,
        )
