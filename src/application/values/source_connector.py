from dataclasses import dataclass, field

from src.domain.exceptions import DomainException
from src.application.values.field_mapping import FieldMapping


@dataclass(frozen=True)
class SourceConnector:
    source_system_id: str
    gcp_project_id: str
    dataset_id: str
    table_id: str
    field_mapping: FieldMapping
    credentials_path: str | None = None
    row_filter: str | None = None
    page_size: int = field(default=5000)

    def __post_init__(self) -> None:
        if not self.source_system_id.strip():
            raise DomainException("SourceConnector: source_system_id must not be empty")
        if not self.gcp_project_id.strip():
            raise DomainException("SourceConnector: gcp_project_id must not be empty")
        if not self.dataset_id.strip():
            raise DomainException("SourceConnector: dataset_id must not be empty")
        if not self.table_id.strip():
            raise DomainException("SourceConnector: table_id must not be empty")
        if self.page_size < 1:
            raise DomainException("SourceConnector: page_size must be at least 1")

    def to_dict(self) -> dict:
        return {
            "source_system_id": self.source_system_id,
            "gcp_project_id": self.gcp_project_id,
            "dataset_id": self.dataset_id,
            "table_id": self.table_id,
            "credentials_path": self.credentials_path,
            "row_filter": self.row_filter,
            "page_size": self.page_size,
            "field_mapping": {
                "question_column": self.field_mapping.question_column,
                "answer_column": self.field_mapping.answer_column,
                "timestamp_column": self.field_mapping.timestamp_column,
                "external_id_column": self.field_mapping.external_id_column,
                "metadata_columns": dict(self.field_mapping.metadata_columns),
            },
        }
