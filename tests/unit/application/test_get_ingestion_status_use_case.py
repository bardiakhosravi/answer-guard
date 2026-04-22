from unittest.mock import MagicMock

import pytest

from src.application.ports.primary.get_ingestion_status_port import IngestionRunNotFoundError
from src.application.queries.get_ingestion_status_query import GetIngestionStatusQuery
from src.application.use_cases.get_ingestion_status_use_case import GetIngestionStatusUseCase
from src.domain.model.ingestion_run.ingestion_run import IngestionRun
from src.domain.model.ingestion_run.ingestion_status import IngestionStatus


def _make_use_case(qa_repo=None, run_repo=None):
    qa_repo = qa_repo or MagicMock()
    run_repo = run_repo or MagicMock()
    return GetIngestionStatusUseCase(qa_repo, run_repo), qa_repo, run_repo


def _make_completed_run(source_system_id: str = "sys-1") -> IngestionRun:
    run = IngestionRun.start(source_system_id, {"source_system_id": source_system_id})
    run.record_progress(100, 3, 100)
    run.complete()
    return run


def test_summary_includes_correct_totals():
    use_case, qa_repo, run_repo = _make_use_case()
    run = _make_completed_run("sys-1")
    run_repo.find_latest_per_source.return_value = [run]
    qa_repo.count_by_source.return_value = 97
    qa_repo.count_by_source_since.return_value = 10

    result = use_case.execute(GetIngestionStatusQuery())

    assert result.total_qa_pairs == 97
    assert len(result.sources) == 1
    assert result.sources[0].source_system_id == "sys-1"
    assert result.sources[0].total_records == 97
    assert result.sources[0].runtime_captures_last_24h == 10


def test_summary_last_import_run_populated():
    use_case, qa_repo, run_repo = _make_use_case()
    run = _make_completed_run("sys-1")
    run_repo.find_latest_per_source.return_value = [run]
    qa_repo.count_by_source.return_value = 97
    qa_repo.count_by_source_since.return_value = 0

    result = use_case.execute(GetIngestionStatusQuery())

    last_run = result.sources[0].last_import_run
    assert last_run is not None
    assert last_run.status == IngestionStatus.COMPLETED.value
    assert last_run.records_processed == 100
    assert last_run.records_skipped == 3


def test_unknown_run_id_raises_not_found():
    use_case, qa_repo, run_repo = _make_use_case()
    run_repo.find_by_id.return_value = None

    with pytest.raises(IngestionRunNotFoundError):
        use_case.execute(GetIngestionStatusQuery(run_id="nonexistent-id"))


def test_single_run_query_returns_that_run():
    use_case, qa_repo, run_repo = _make_use_case()
    run = _make_completed_run("sys-1")
    run_repo.find_by_id.return_value = run
    qa_repo.count_by_source.return_value = 50

    result = use_case.execute(GetIngestionStatusQuery(run_id=run.id.value))

    assert result.sources[0].last_import_run.run_id == run.id.value
