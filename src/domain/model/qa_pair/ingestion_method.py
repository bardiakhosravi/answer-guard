from enum import Enum


class IngestionMethod(str, Enum):
    HISTORICAL_IMPORT = "HISTORICAL_IMPORT"
    RUNTIME_CAPTURE = "RUNTIME_CAPTURE"
