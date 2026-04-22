import pytest

from src.domain.exceptions import DomainException
from src.domain.model.ingestion_run.ingestion_run import IngestionRun
from src.domain.model.ingestion_run.ingestion_status import IngestionStatus


def _start() -> IngestionRun:
    return IngestionRun.start(source_system_id="sys-1", config_snapshot={"source_system_id": "sys-1"})


def test_start_creates_running_run():
    run = _start()
    assert run.status == IngestionStatus.RUNNING
    assert run.records_processed == 0
    assert run.records_skipped == 0
    assert run.last_checkpoint is None


def test_config_snapshot_populated_on_start():
    run = IngestionRun.start("sys-1", {"source_system_id": "sys-1", "table_id": "tbl"})
    assert run.config_snapshot["source_system_id"] == "sys-1"
    assert run.config_snapshot["table_id"] == "tbl"


def test_complete_transitions_to_completed():
    run = _start()
    run.complete()
    assert run.status == IngestionStatus.COMPLETED
    assert run.completed_at is not None


def test_fail_transitions_to_failed():
    run = _start()
    run.fail("network error")
    assert run.status == IngestionStatus.FAILED
    assert run.completed_at is not None


def test_resume_from_failed():
    run = _start()
    run.fail("timeout")
    run.resume()
    assert run.status == IngestionStatus.RESUMED


def test_resume_from_running_raises():
    run = _start()
    with pytest.raises(DomainException):
        run.resume()


def test_complete_from_resumed():
    run = _start()
    run.fail("err")
    run.resume()
    run.complete()
    assert run.status == IngestionStatus.COMPLETED


def test_double_complete_raises():
    run = _start()
    run.complete()
    with pytest.raises(DomainException):
        run.complete()


def test_record_progress_accumulates():
    run = _start()
    run.record_progress(100, 5, 100)
    run.record_progress(200, 3, 300)
    assert run.records_processed == 300
    assert run.records_skipped == 8
    assert run.last_checkpoint == 300


def test_record_progress_on_completed_raises():
    run = _start()
    run.complete()
    with pytest.raises(DomainException):
        run.record_progress(1, 0, 1)


def test_log_error_appends():
    run = _start()
    run.log_error(42, "missing answer")
    run.log_error(99, "duplicate")
    assert len(run.error_log) == 2
    assert run.error_log[0] == {"index": 42, "reason": "missing answer"}
