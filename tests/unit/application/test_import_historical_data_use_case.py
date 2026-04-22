from unittest.mock import MagicMock

import pytest

from src.application.commands.import_historical_data_command import ImportHistoricalDataCommand
from src.application.ports.primary.import_historical_data_port import (
    FieldMappingValidationError,
    ImportAlreadyRunningError,
)
from src.application.use_cases.import_historical_data_use_case import ImportHistoricalDataUseCase
from src.application.values.field_mapping import FieldMapping
from src.application.values.source_connector import SourceConnector
from src.domain.model.ingestion_run.ingestion_run import IngestionRun
from src.domain.model.ingestion_run.ingestion_status import IngestionStatus


def _make_connector(question_col="question", answer_col="answer") -> SourceConnector:
    return SourceConnector(
        source_system_id="sys-1",
        gcp_project_id="proj",
        dataset_id="ds",
        table_id="tbl",
        field_mapping=FieldMapping(question_column=question_col, answer_column=answer_col),
        page_size=2,
    )


def _make_use_case(bq=None, qa_repo=None, run_repo=None):
    bq = bq or MagicMock()
    qa_repo = qa_repo or MagicMock()
    run_repo = run_repo or MagicMock()
    run_repo.find_active_for_source.return_value = None
    run_repo.find_latest_for_source.return_value = None
    return ImportHistoricalDataUseCase(bq, qa_repo, run_repo), bq, qa_repo, run_repo


def test_invalid_field_mapping_raises_before_run_starts():
    use_case, bq, qa_repo, run_repo = _make_use_case()
    bq.get_schema.return_value = ["other_col"]

    with pytest.raises(FieldMappingValidationError):
        use_case.execute(ImportHistoricalDataCommand(_make_connector()))

    run_repo.save.assert_not_called()


def test_import_already_running_raises():
    use_case, bq, qa_repo, run_repo = _make_use_case()
    bq.get_schema.return_value = ["question", "answer"]
    running_run = IngestionRun.start("sys-1", {"source_system_id": "sys-1"})
    run_repo.find_active_for_source.return_value = running_run

    with pytest.raises(ImportAlreadyRunningError):
        use_case.execute(ImportHistoricalDataCommand(_make_connector()))


def test_successful_import_completes_run():
    use_case, bq, qa_repo, run_repo = _make_use_case()
    bq.get_schema.return_value = ["question", "answer"]
    bq.read_rows.return_value = iter([
        {"question": "Q1", "answer": "A1"},
        {"question": "Q2", "answer": "A2"},
    ])
    qa_repo.save.return_value = True  # new records

    result = use_case.execute(ImportHistoricalDataCommand(_make_connector()))

    assert result.status == IngestionStatus.COMPLETED.value
    assert qa_repo.save.call_count == 2


def test_duplicate_rows_counted_as_skipped():
    use_case, bq, qa_repo, run_repo = _make_use_case()
    bq.get_schema.return_value = ["question", "answer"]
    bq.read_rows.return_value = iter([
        {"question": "Q1", "answer": "A1"},
    ])
    qa_repo.save.return_value = False  # duplicate — not new

    result = use_case.execute(ImportHistoricalDataCommand(_make_connector()))

    assert result.status == IngestionStatus.COMPLETED.value


def test_mid_run_exception_fails_run():
    use_case, bq, qa_repo, run_repo = _make_use_case()
    bq.get_schema.return_value = ["question", "answer"]
    bq.read_rows.side_effect = RuntimeError("network down")

    with pytest.raises(RuntimeError):
        use_case.execute(ImportHistoricalDataCommand(_make_connector()))

    last_saved_run = run_repo.save.call_args_list[-1][0][0]
    assert last_saved_run.status == IngestionStatus.FAILED


def test_resume_from_failed_run():
    use_case, bq, qa_repo, run_repo = _make_use_case()
    bq.get_schema.return_value = ["question", "answer"]
    bq.read_rows.return_value = iter([])

    failed_run = IngestionRun.start("sys-1", {"source_system_id": "sys-1"})
    failed_run.fail("timeout")
    failed_run.last_checkpoint = 500
    run_repo.find_latest_for_source.return_value = failed_run

    use_case.execute(ImportHistoricalDataCommand(_make_connector()))

    # Verify read_rows called with start_index=500
    call_args = bq.read_rows.call_args
    start_index = call_args[1].get("start_index") or (call_args[0][1] if len(call_args[0]) > 1 else None)
    assert start_index == 500
