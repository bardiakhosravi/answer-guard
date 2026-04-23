from unittest.mock import MagicMock

import pytest

from src.adapters.exceptions import AdapterException
from src.application.commands.discover_schema_command import DiscoverSchemaCommand
from src.application.ports.primary.discover_schema_port import InvalidRowFilterError
from src.application.use_cases.discover_schema_use_case import DiscoverSchemaUseCase


def _cmd() -> DiscoverSchemaCommand:
    return DiscoverSchemaCommand(
        gcp_project_id="proj",
        dataset_id="ds",
        table_id="tbl",
    )


def test_returns_columns_from_bigquery():
    bq = MagicMock()
    bq.get_schema.return_value = [
        {"name": "user_question", "type": "STRING"},
        {"name": "agent_response", "type": "STRING"},
        {"name": "created_at", "type": "TIMESTAMP"},
    ]
    use_case = DiscoverSchemaUseCase(bq)

    result = use_case.execute(_cmd())

    assert len(result.columns) == 3
    assert result.columns[0].name == "user_question"
    assert result.columns[0].type == "STRING"
    assert result.columns[2].type == "TIMESTAMP"


def test_adapter_exception_propagates():
    bq = MagicMock()
    bq.get_schema.side_effect = AdapterException("table not found")
    use_case = DiscoverSchemaUseCase(bq)

    with pytest.raises(AdapterException, match="table not found"):
        use_case.execute(_cmd())


def test_invalid_row_filter_raises_domain_error():
    bq = MagicMock()
    bq.validate_row_filter.side_effect = AdapterException(
        "Invalid row filter: Syntax error: Expected end of input"
    )
    use_case = DiscoverSchemaUseCase(bq)

    with pytest.raises(InvalidRowFilterError, match="Syntax error"):
        use_case.execute(
            DiscoverSchemaCommand(
                gcp_project_id="proj",
                dataset_id="ds",
                table_id="tbl",
                row_filter="created_at > ",
            )
        )

    # Schema lookup should be skipped when the filter is invalid
    bq.get_schema.assert_not_called()


def test_empty_row_filter_skips_validation():
    bq = MagicMock()
    bq.get_schema.return_value = []
    use_case = DiscoverSchemaUseCase(bq)

    use_case.execute(
        DiscoverSchemaCommand(
            gcp_project_id="proj", dataset_id="ds", table_id="tbl", row_filter=""
        )
    )

    bq.validate_row_filter.assert_not_called()


def test_valid_row_filter_triggers_validation_then_schema():
    bq = MagicMock()
    bq.get_schema.return_value = []
    use_case = DiscoverSchemaUseCase(bq)

    use_case.execute(
        DiscoverSchemaCommand(
            gcp_project_id="proj",
            dataset_id="ds",
            table_id="tbl",
            row_filter="created_at > '2024-01-01'",
        )
    )

    bq.validate_row_filter.assert_called_once()
    bq.get_schema.assert_called_once()


def test_credentials_path_forwarded_to_connector():
    bq = MagicMock()
    bq.get_schema.return_value = []
    use_case = DiscoverSchemaUseCase(bq)

    use_case.execute(
        DiscoverSchemaCommand(
            gcp_project_id="proj",
            dataset_id="ds",
            table_id="tbl",
            credentials_path="/secrets/key.json",
        )
    )

    connector_arg = bq.get_schema.call_args[0][0]
    assert connector_arg.credentials_path == "/secrets/key.json"
    assert connector_arg.gcp_project_id == "proj"
