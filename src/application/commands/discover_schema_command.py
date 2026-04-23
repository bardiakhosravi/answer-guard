from dataclasses import dataclass


@dataclass(frozen=True)
class DiscoverSchemaCommand:
    gcp_project_id: str
    dataset_id: str
    table_id: str
    credentials_path: str | None = None
    row_filter: str | None = None
