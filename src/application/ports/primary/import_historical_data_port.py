from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from src.application.commands.import_historical_data_command import ImportHistoricalDataCommand
from src.domain.exceptions import DomainException


class FieldMappingValidationError(DomainException):
    """Raised when the configured field mapping references columns absent in the source table."""


class ImportAlreadyRunningError(DomainException):
    """Raised when an import is triggered while one is already RUNNING for the same source."""


@dataclass(frozen=True)
class ImportHistoricalDataResponse:
    ingestion_run_id: str
    status: str
    message: str


class ImportHistoricalDataPort(ABC):
    @abstractmethod
    def execute(self, command: ImportHistoricalDataCommand) -> ImportHistoricalDataResponse:
        """Trigger a historical bulk import from the configured BigQuery source."""
