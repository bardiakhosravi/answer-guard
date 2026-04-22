from enum import Enum


class IngestionStatus(str, Enum):
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    RESUMED = "RESUMED"
