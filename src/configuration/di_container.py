from __future__ import annotations

from sqlalchemy.orm import Session

from src.adapters.secondary.bigquery.bigquery_source_adapter import BigQuerySourceAdapter
from src.adapters.secondary.sql.sql_ingestion_run_repository import SqlIngestionRunRepository
from src.adapters.secondary.sql.sql_qa_pair_repository import SqlQAPairRepository
from src.application.use_cases.capture_runtime_response_use_case import CaptureRuntimeResponseUseCase
from src.application.use_cases.get_ingestion_status_use_case import GetIngestionStatusUseCase
from src.application.use_cases.import_historical_data_use_case import ImportHistoricalDataUseCase
from src.configuration.app_settings import AppSettings
from src.configuration.database_config import DatabaseConfig


class DIContainer:
    def __init__(self, settings: AppSettings) -> None:
        self._settings = settings
        self._db_config = DatabaseConfig(settings.database_url)

    @property
    def db_config(self) -> DatabaseConfig:
        return self._db_config

    def bigquery_source_adapter(self) -> BigQuerySourceAdapter:
        return BigQuerySourceAdapter(
            credentials_path=self._settings.google_application_credentials or None
        )

    def import_historical_data_use_case(self) -> ImportHistoricalDataUseCase:
        # Single shared session so both repositories participate in the same transaction
        session: Session = self._db_config.get_session()
        return ImportHistoricalDataUseCase(
            bigquery_source=self.bigquery_source_adapter(),
            qa_pair_repository=SqlQAPairRepository(session),
            ingestion_run_repository=SqlIngestionRunRepository(session),
        )

    def capture_runtime_response_use_case(self) -> CaptureRuntimeResponseUseCase:
        session: Session = self._db_config.get_session()
        return CaptureRuntimeResponseUseCase(
            qa_pair_repository=SqlQAPairRepository(session),
        )

    def get_ingestion_status_use_case(self) -> GetIngestionStatusUseCase:
        session: Session = self._db_config.get_session()
        return GetIngestionStatusUseCase(
            qa_pair_repository=SqlQAPairRepository(session),
            ingestion_run_repository=SqlIngestionRunRepository(session),
        )
