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


def _pair(q="Q", a="A", source="sys-1", **kwargs) -> QAPair:
    return QAPair.create(q, a, source, IngestionMethod.HISTORICAL_IMPORT, **kwargs)


def test_save_and_find_by_hash(repo):
    pair = _pair()
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
    assert repo.find_by_hash(SourceHash.compute("x", "y", "z")) is None


def test_find_by_id_returns_none_when_absent(repo):
    from src.domain.model.qa_pair.qa_pair_id import QAPairId
    assert repo.find_by_id(QAPairId.generate()) is None


def test_save_duplicate_is_idempotent(repo):
    pair = _pair()
    repo.save(pair)
    repo.save(pair)  # second save should be a no-op
    assert repo.count_by_source("sys-1") == 1


def test_count_by_source(repo):
    repo.save(_pair("Q1", "A1", "sys-1"))
    repo.save(_pair("Q2", "A2", "sys-1"))
    repo.save(_pair("Q3", "A3", "sys-2"))
    assert repo.count_by_source("sys-1") == 2
    assert repo.count_by_source("sys-2") == 1
    assert repo.count_by_source("sys-3") == 0


def test_count_by_source_since(repo):
    from datetime import datetime, timedelta, timezone
    pair = _pair()
    repo.save(pair)
    past = datetime.now(timezone.utc) - timedelta(hours=1)
    future = datetime.now(timezone.utc) + timedelta(hours=1)
    assert repo.count_by_source_since("sys-1", past) == 1
    assert repo.count_by_source_since("sys-1", future) == 0


def test_metadata_round_trips(repo):
    pair = _pair(metadata={"topic": "billing", "user": "u_123"})
    repo.save(pair)
    found = repo.find_by_hash(pair.source_hash)
    assert found.metadata == {"topic": "billing", "user": "u_123"}
