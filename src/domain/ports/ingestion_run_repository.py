from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from src.domain.model.ingestion_run.ingestion_run import IngestionRun
    from src.domain.model.ingestion_run.ingestion_run_id import IngestionRunId


class IngestionRunRepository(ABC):
    @abstractmethod
    def save(self, run: "IngestionRun") -> None:
        """Persist or update an IngestionRun."""

    @abstractmethod
    def find_by_id(self, run_id: "IngestionRunId") -> Optional["IngestionRun"]:
        """Return IngestionRun by ID, or None."""

    @abstractmethod
    def find_active_for_source(self, source_system_id: str) -> Optional["IngestionRun"]:
        """Return the currently RUNNING or RESUMED run for a source, or None."""

    @abstractmethod
    def find_latest_for_source(self, source_system_id: str) -> Optional["IngestionRun"]:
        """Return the most recently started run for a source, or None."""

    @abstractmethod
    def find_latest_per_source(self) -> list["IngestionRun"]:
        """Return the most recent run per distinct source_system_id."""
