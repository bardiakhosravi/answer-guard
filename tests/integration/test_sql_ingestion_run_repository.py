"""Integration tests for SqlIngestionRunRepository against SQLite in-memory."""
import pytest

from src.adapters.secondary.sql.sql_ingestion_run_repository import SqlIngestionRunRepository
from src.configuration.database_config import Base, DatabaseConfig
from src.domain.model.ingestion_run.ingestion_run import IngestionRun
from src.domain.model.ingestion_run.ingestion_run_id import IngestionRunId
from src.domain.model.ingestion_run.ingestion_status import IngestionStatus


@pytest.fixture()
def repo():
    config = DatabaseConfig("sqlite:///:memory:")
    Base.metadata.create_all(config.engine)
    session = config.get_session()
    yield SqlIngestionRunRepository(session)
    session.close()
    Base.metadata.drop_all(config.engine)


def _start(source_id: str = "sys-1") -> IngestionRun:
    return IngestionRun.start(source_id, {"source_system_id": source_id})


def test_save_and_find_by_id(repo):
    run = _start()
    repo.save(run)
    found = repo.find_by_id(run.id)
    assert found is not None
    assert found.status == IngestionStatus.RUNNING
    assert found.source_system_id == "sys-1"


def test_find_by_id_missing_returns_none(repo):
    assert repo.find_by_id(IngestionRunId.generate()) is None


def test_save_updates_existing(repo):
    run = _start()
    repo.save(run)
    run.record_progress(50, 2, 50)
    run.complete()
    repo.save(run)

    found = repo.find_by_id(run.id)
    assert found.status == IngestionStatus.COMPLETED
    assert found.records_processed == 50


def test_find_active_for_source(repo):
    run = _start()
    repo.save(run)
    active = repo.find_active_for_source("sys-1")
    assert active is not None
    assert active.id == run.id


def test_find_active_returns_none_when_completed(repo):
    run = _start()
    run.complete()
    repo.save(run)
    assert repo.find_active_for_source("sys-1") is None


def test_find_latest_per_source(repo):
    run1 = _start("sys-1")
    run2 = _start("sys-2")
    repo.save(run1)
    repo.save(run2)

    latest = repo.find_latest_per_source()
    source_ids = {r.source_system_id for r in latest}
    assert source_ids == {"sys-1", "sys-2"}


def test_error_log_persists(repo):
    run = _start()
    run.log_error(42, "missing answer")
    repo.save(run)

    found = repo.find_by_id(run.id)
    assert len(found.error_log) == 1
    assert found.error_log[0]["index"] == 42
