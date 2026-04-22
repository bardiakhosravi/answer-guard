from dataclasses import dataclass

from src.application.values.source_connector import SourceConnector


@dataclass(frozen=True)
class ImportHistoricalDataCommand:
    source_connector: SourceConnector
