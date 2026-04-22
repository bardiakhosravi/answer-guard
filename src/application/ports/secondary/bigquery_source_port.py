from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Iterator

if TYPE_CHECKING:
    from src.application.values.source_connector import SourceConnector


class BigQuerySourcePort(ABC):
    @abstractmethod
    def read_rows(
        self, connector: "SourceConnector", start_index: int = 0
    ) -> Iterator[dict]:
        """Stream rows from the BigQuery source table as dicts, starting at start_index."""

    @abstractmethod
    def get_schema(self, connector: "SourceConnector") -> list[str]:
        """Return column names for the source table."""
