from __future__ import annotations

from src.adapters.exceptions import AdapterException
from src.application.commands.discover_schema_command import DiscoverSchemaCommand
from src.application.ports.primary.discover_schema_port import (
    DiscoveredColumn,
    DiscoverSchemaPort,
    DiscoverSchemaResponse,
    InvalidRowFilterError,
)
from src.application.ports.secondary.bigquery_source_port import BigQuerySourcePort
from src.application.values.field_mapping import FieldMapping
from src.application.values.source_connector import SourceConnector


class DiscoverSchemaUseCase(DiscoverSchemaPort):
    def __init__(self, bigquery_source: BigQuerySourcePort) -> None:
        self._bq = bigquery_source

    def execute(self, command: DiscoverSchemaCommand) -> DiscoverSchemaResponse:
        # Build a minimal SourceConnector. FieldMapping requires non-empty
        # question/answer columns, so we use placeholder values — they're never
        # read by get_schema() / validate_row_filter().
        connector = SourceConnector(
            source_system_id="__discover_schema__",
            gcp_project_id=command.gcp_project_id,
            dataset_id=command.dataset_id,
            table_id=command.table_id,
            credentials_path=command.credentials_path,
            field_mapping=FieldMapping(
                question_column="__placeholder__",
                answer_column="__placeholder__",
            ),
        )

        # Validate the row filter up front if provided — surfaces BigQuery
        # syntax errors before the user commits to the rest of the wizard.
        if command.row_filter and command.row_filter.strip():
            try:
                self._bq.validate_row_filter(connector, command.row_filter.strip())
            except AdapterException as exc:
                raise InvalidRowFilterError(str(exc)) from exc

        schema = self._bq.get_schema(connector)
        columns = [DiscoveredColumn(name=col["name"], type=col["type"]) for col in schema]
        return DiscoverSchemaResponse(columns=columns)
