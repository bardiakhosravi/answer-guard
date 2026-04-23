from __future__ import annotations

from sqlalchemy.orm import Session

from src.adapters.secondary.bigquery.bigquery_source_adapter import BigQuerySourceAdapter
from src.adapters.secondary.sql.sql_ingestion_run_repository import SqlIngestionRunRepository
from src.adapters.secondary.sql.sql_qa_pair_repository import SqlQAPairRepository
from src.adapters.secondary.sql.sql_response_feedback_repository import (
    SqlResponseFeedbackRepository,
)
from src.application.use_cases.capture_runtime_response_use_case import CaptureRuntimeResponseUseCase
from src.application.use_cases.discover_schema_use_case import DiscoverSchemaUseCase
from src.application.use_cases.get_ingestion_status_use_case import GetIngestionStatusUseCase
from src.application.use_cases.import_historical_data_use_case import ImportHistoricalDataUseCase
from src.application.use_cases.list_qa_pairs_use_case import ListQAPairsUseCase
from src.application.use_cases.delete_response_feedback_use_case import (
    DeleteResponseFeedbackUseCase,
)
from src.application.use_cases.get_response_feedback_use_case import (
    GetResponseFeedbackUseCase,
)
from src.application.use_cases.list_response_feedback_use_case import (
    ListResponseFeedbackUseCase,
)
from src.application.use_cases.submit_response_feedback_use_case import (
    SubmitResponseFeedbackUseCase,
)
from src.application.use_cases.update_response_feedback_use_case import (
    UpdateResponseFeedbackUseCase,
)
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

    def discover_schema_use_case(self) -> DiscoverSchemaUseCase:
        return DiscoverSchemaUseCase(bigquery_source=self.bigquery_source_adapter())

    def list_qa_pairs_use_case(self) -> ListQAPairsUseCase:
        session: Session = self._db_config.get_session()
        return ListQAPairsUseCase(qa_pair_repository=SqlQAPairRepository(session))

    def sql_response_feedback_repository(self) -> SqlResponseFeedbackRepository:
        session: Session = self._db_config.get_session()
        return SqlResponseFeedbackRepository(session)

    def submit_response_feedback_use_case(self) -> SubmitResponseFeedbackUseCase:
        return SubmitResponseFeedbackUseCase(
            response_feedback_repository=self.sql_response_feedback_repository(),
        )

    def list_response_feedback_use_case(self) -> ListResponseFeedbackUseCase:
        return ListResponseFeedbackUseCase(
            response_feedback_repository=self.sql_response_feedback_repository(),
        )

    def get_response_feedback_use_case(self) -> GetResponseFeedbackUseCase:
        return GetResponseFeedbackUseCase(
            response_feedback_repository=self.sql_response_feedback_repository(),
        )

    def update_response_feedback_use_case(self) -> UpdateResponseFeedbackUseCase:
        return UpdateResponseFeedbackUseCase(
            response_feedback_repository=self.sql_response_feedback_repository(),
        )

    def delete_response_feedback_use_case(self) -> DeleteResponseFeedbackUseCase:
        return DeleteResponseFeedbackUseCase(
            response_feedback_repository=self.sql_response_feedback_repository(),
        )
