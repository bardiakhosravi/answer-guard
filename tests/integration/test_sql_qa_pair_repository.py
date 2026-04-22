"""Integration tests for SqlQAPairRepository against SQLite in-memory."""
import pytest

from src.adapters.secondary.sql.sql_qa_pair_repository import SqlQAPairRepository
from src.configuration.database_config import Base, DatabaseConfig
from src.domain.model.qa_pair.ingestion_method import IngestionMethod
from src.domain.model.qa_pair.qa_pair import QAPair


@pytest.fixture()
def repo():
    config = DatabaseConfig("sqlite:///:memory:")
    Base.metadata.create_all(config.engine)
    session = config.get_session()
    yield SqlQAPairRepository(session)
    session.close()
    Base.metadata.drop_all(config.engine)


def test_full_round_trip(repo):
    pair = QAPair.create("What is X?", "X is Y.", "sys-1", IngestionMethod.RUNTIME_CAPTURE)
    repo.save(pair)
    by_hash = repo.find_by_hash(pair.source_hash)
    by_id = repo.find_by_id(pair.id)
    assert by_hash is not None
    assert by_id is not None
    assert by_hash.question_text == "What is X?"
    assert by_hash.ingestion_method == IngestionMethod.RUNTIME_CAPTURE


def test_duplicate_save_does_not_increase_count(repo):
    pair = QAPair.create("Q", "A", "sys-1", IngestionMethod.RUNTIME_CAPTURE)
    repo.save(pair)
    repo.save(pair)
    assert repo.count_by_source("sys-1") == 1


def test_external_id_stored(repo):
    pair = QAPair.create(
        "Q", "A", "sys-1", IngestionMethod.HISTORICAL_IMPORT, external_id="ext-123"
    )
    repo.save(pair)
    found = repo.find_by_id(pair.id)
    assert found.external_id == "ext-123"
