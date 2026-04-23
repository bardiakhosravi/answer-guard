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
    def get_schema(self, connector: "SourceConnector") -> list[dict]:
        """
        Return column metadata for the source table as a list of dicts:
        [{"name": "...", "type": "..."}, ...].
        """

    @abstractmethod
    def validate_row_filter(self, connector: "SourceConnector", row_filter: str) -> None:
        """
        Validate that the given row filter is a syntactically valid BigQuery
        WHERE clause for the given table. Raises AdapterException with the raw
        BigQuery error message on failure. Does not return any data.
        """
