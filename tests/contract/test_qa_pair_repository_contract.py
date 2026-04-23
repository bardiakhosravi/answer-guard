"""Contract tests for QAPairRepository — run against any concrete implementation."""
import pytest

from src.adapters.secondary.sql.sql_qa_pair_repository import SqlQAPairRepository
from src.configuration.database_config import Base, DatabaseConfig
from src.domain.model.qa_pair.ingestion_method import IngestionMethod
from src.domain.model.qa_pair.qa_pair import QAPair
from src.domain.model.qa_pair.source_hash import SourceHash


@pytest.fixture()
def sqlite_session():
    config = DatabaseConfig("sqlite:///:memory:")
    Base.metadata.create_all(config.engine)
    session = config.get_session()
    yield session
    session.close()
    Base.metadata.drop_all(config.engine)


@pytest.fixture()
def repo(sqlite_session):
    return SqlQAPairRepository(sqlite_session)


def _pair(q="Q", a="A", source="sys-1", external_id=None, **kwargs) -> QAPair:
    return QAPair.create(q, a, source, IngestionMethod.HISTORICAL_IMPORT, external_id=external_id, **kwargs)


def test_save_and_find_by_hash(repo):
    pair = _pair(external_id="ext-1")
    repo.save(pair)
    found = repo.find_by_hash(pair.source_hash)
    assert found is not None
    assert found.question_text == "Q"
    assert found.answer_text == "A"


def test_save_and_find_by_id(repo):
    pair = _pair()
    repo.save(pair)
    found = repo.find_by_id(pair.id)
    assert found is not None
    assert found.id == pair.id


def test_find_by_hash_returns_none_when_absent(repo):
    assert repo.find_by_hash(SourceHash.for_external_id("sys-x", "ext-x")) is None


def test_find_by_id_returns_none_when_absent(repo):
    from src.domain.model.qa_pair.qa_pair_id import QAPairId
    assert repo.find_by_id(QAPairId.generate()) is None


def test_saving_same_source_row_twice_is_idempotent(repo):
    """A re-import of the same source row (same external_id) dedups."""
    a = _pair("Q1", "A1", "sys-1", external_id="ext-42")
    b = _pair("Q1", "A1", "sys-1", external_id="ext-42")  # same logical row, different create call
    repo.save(a)
    repo.save(b)
    assert repo.count_by_source("sys-1") == 1


def test_identical_content_without_external_id_stores_both(repo):
    """Without an external_id, repeats are treated as distinct interactions."""
    repo.save(_pair("Same question", "Same answer", "sys-1"))
    repo.save(_pair("Same question", "Same answer", "sys-1"))
    assert repo.count_by_source("sys-1") == 2


def test_different_external_ids_store_both_even_with_same_content(repo):
    """Two source rows with distinct IDs but identical content are distinct interactions."""
    repo.save(_pair("Q", "A", "sys-1", external_id="ext-1"))
    repo.save(_pair("Q", "A", "sys-1", external_id="ext-2"))
    assert repo.count_by_source("sys-1") == 2


def test_count_by_source(repo):
    repo.save(_pair("Q1", "A1", "sys-1", external_id="e1"))
    repo.save(_pair("Q2", "A2", "sys-1", external_id="e2"))
    repo.save(_pair("Q3", "A3", "sys-2", external_id="e3"))
    assert repo.count_by_source("sys-1") == 2
    assert repo.count_by_source("sys-2") == 1
    assert repo.count_by_source("sys-3") == 0


def test_count_by_source_since(repo):
    from datetime import datetime, timedelta, timezone
    pair = _pair(external_id="ext-now")
    repo.save(pair)
    past = datetime.now(timezone.utc) - timedelta(hours=1)
    future = datetime.now(timezone.utc) + timedelta(hours=1)
    assert repo.count_by_source_since("sys-1", past) == 1
    assert repo.count_by_source_since("sys-1", future) == 0


def test_metadata_round_trips(repo):
    pair = _pair(external_id="ext-m", metadata={"topic": "billing", "user": "u_123"})
    repo.save(pair)
    found = repo.find_by_hash(pair.source_hash)
    assert found.metadata == {"topic": "billing", "user": "u_123"}
