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
    pair = QAPair.create(
        "What is X?", "X is Y.", "sys-1", IngestionMethod.RUNTIME_CAPTURE, external_id="ext-1",
    )
    repo.save(pair)
    by_hash = repo.find_by_hash(pair.source_hash)
    by_id = repo.find_by_id(pair.id)
    assert by_hash is not None
    assert by_id is not None
    assert by_hash.question_text == "What is X?"


def test_same_external_id_save_twice_dedups(repo):
    a = QAPair.create("Q", "A", "sys-1", IngestionMethod.HISTORICAL_IMPORT, external_id="ext-1")
    b = QAPair.create("Q", "A", "sys-1", IngestionMethod.HISTORICAL_IMPORT, external_id="ext-1")
    repo.save(a)
    repo.save(b)
    assert repo.count_by_source("sys-1") == 1


def test_runtime_captures_never_dedup(repo):
    """Runtime captures have no external_id — every save stores a new row."""
    for _ in range(3):
        pair = QAPair.create("Q", "A", "sys-1", IngestionMethod.RUNTIME_CAPTURE)
        repo.save(pair)
    assert repo.count_by_source("sys-1") == 3


def test_external_id_stored(repo):
    pair = QAPair.create(
        "Q", "A", "sys-1", IngestionMethod.HISTORICAL_IMPORT, external_id="ext-123"
    )
    repo.save(pair)
    found = repo.find_by_id(pair.id)
    assert found.external_id == "ext-123"


def test_list_paginated_returns_page_and_total(repo):
    for i in range(25):
        repo.save(
            QAPair.create(
                f"Question {i}", f"Answer {i}", "sys-1",
                IngestionMethod.HISTORICAL_IMPORT, external_id=f"ext-{i}",
            )
        )
    items, total = repo.list_paginated(page=1, page_size=10)
    assert total == 25
    assert len(items) == 10


def test_list_paginated_second_page(repo):
    for i in range(25):
        repo.save(
            QAPair.create(
                f"Q{i}", f"A{i}", "sys-1",
                IngestionMethod.HISTORICAL_IMPORT, external_id=f"ext-{i}",
            )
        )

    items_p1, _ = repo.list_paginated(page=1, page_size=10)
    items_p2, _ = repo.list_paginated(page=2, page_size=10)
    items_p3, _ = repo.list_paginated(page=3, page_size=10)

    assert len(items_p1) == 10
    assert len(items_p2) == 10
    assert len(items_p3) == 5
    ids_p1 = {p.id.value for p in items_p1}
    ids_p2 = {p.id.value for p in items_p2}
    assert ids_p1.isdisjoint(ids_p2)


def test_list_paginated_filters_by_source(repo):
    repo.save(QAPair.create("Q1", "A1", "sys-a", IngestionMethod.HISTORICAL_IMPORT, external_id="e1"))
    repo.save(QAPair.create("Q2", "A2", "sys-a", IngestionMethod.HISTORICAL_IMPORT, external_id="e2"))
    repo.save(QAPair.create("Q3", "A3", "sys-b", IngestionMethod.HISTORICAL_IMPORT, external_id="e3"))

    items, total = repo.list_paginated(page=1, page_size=50, source_system_id="sys-a")

    assert total == 2
    assert {p.source_system_id for p in items} == {"sys-a"}


def test_list_paginated_search_is_case_insensitive(repo):
    repo.save(QAPair.create(
        "How to REFUND?", "Go to settings.", "sys-1",
        IngestionMethod.HISTORICAL_IMPORT, external_id="r1",
    ))
    repo.save(QAPair.create(
        "Cancel my plan", "Sure.", "sys-1",
        IngestionMethod.HISTORICAL_IMPORT, external_id="c1",
    ))
    repo.save(QAPair.create(
        "Billing question", "Yes, I can refund.", "sys-1",
        IngestionMethod.HISTORICAL_IMPORT, external_id="b1",
    ))

    items, total = repo.list_paginated(page=1, page_size=50, search="refund")

    # Case-insensitive match on either question_text or answer_text
    assert total == 2
    assert len(items) == 2


def test_list_paginated_returns_newest_first(repo):
    import time
    first = QAPair.create("First", "A1", "sys-1", IngestionMethod.HISTORICAL_IMPORT, external_id="f")
    repo.save(first)
    time.sleep(0.01)
    second = QAPair.create("Second", "A2", "sys-1", IngestionMethod.HISTORICAL_IMPORT, external_id="s")
    repo.save(second)

    items, _ = repo.list_paginated(page=1, page_size=50)

    assert items[0].question_text == "Second"
    assert items[1].question_text == "First"
