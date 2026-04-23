"""Integration tests for SqlResponseFeedbackRepository against SQLite in-memory."""
import pytest

from src.adapters.secondary.sql.sql_response_feedback_repository import (
    SqlResponseFeedbackRepository,
)
from src.configuration.database_config import Base, DatabaseConfig
from src.domain.model.response_feedback.response_feedback import ResponseFeedback
from src.domain.model.response_feedback.response_feedback_id import ResponseFeedbackId


@pytest.fixture()
def repo():
    config = DatabaseConfig("sqlite:///:memory:")
    Base.metadata.create_all(config.engine)
    session = config.get_session()
    yield SqlResponseFeedbackRepository(session)
    session.close()
    Base.metadata.drop_all(config.engine)


def _make(**overrides):
    defaults = dict(
        source_qa_pair_id="qa-1",
        excerpt="the agent said this",
        problem="too verbose",
        desired_behavior="be concise",
    )
    defaults.update(overrides)
    return ResponseFeedback.create(**defaults)


def test_round_trip_with_span(repo):
    fb = _make(span_start=2, span_end=10)
    repo.save(fb)
    found = repo.find_by_id(fb.id)
    assert found is not None
    assert found.span is not None
    assert found.span.start == 2
    assert found.span.end == 10
    assert found.problem == "too verbose"


def test_round_trip_without_span(repo):
    fb = _make()
    repo.save(fb)
    found = repo.find_by_id(fb.id)
    assert found is not None
    assert found.span is None


def test_list_paginated_newest_first(repo):
    import time
    first = _make(problem="first")
    repo.save(first)
    time.sleep(0.01)
    second = _make(problem="second")
    repo.save(second)
    items, total = repo.list_paginated(page=1, page_size=50)
    assert total == 2
    assert items[0].problem == "second"
    assert items[1].problem == "first"


def test_list_paginated_pagination(repo):
    for i in range(25):
        repo.save(_make(problem=f"p{i}"))
    p1, total = repo.list_paginated(page=1, page_size=10)
    p2, _ = repo.list_paginated(page=2, page_size=10)
    p3, _ = repo.list_paginated(page=3, page_size=10)
    assert total == 25
    assert len(p1) == 10
    assert len(p2) == 10
    assert len(p3) == 5


def test_search_case_insensitive_across_fields(repo):
    repo.save(_make(problem="Contains REFUND word"))
    repo.save(_make(desired_behavior="say REFUND politely"))
    repo.save(_make(excerpt="refund mention in excerpt"))
    repo.save(_make(problem="unrelated"))

    items, total = repo.list_paginated(page=1, page_size=50, search="refund")
    assert total == 3


def test_delete_returns_true_when_deleted(repo):
    fb = _make()
    repo.save(fb)
    assert repo.delete(fb.id) is True
    assert repo.find_by_id(fb.id) is None


def test_delete_returns_false_when_absent(repo):
    assert repo.delete(ResponseFeedbackId("00000000-0000-0000-0000-000000000000")) is False


def test_update_roundtrips(repo):
    fb = _make()
    repo.save(fb)
    fb.update(problem="updated problem", desired_behavior="updated behavior")
    repo.save(fb)
    found = repo.find_by_id(fb.id)
    assert found is not None
    assert found.problem == "updated problem"
    assert found.desired_behavior == "updated behavior"


def test_feedback_independent_of_qa_pair(repo):
    """source_qa_pair_id is by identity — no FK, feedback survives QAPair deletion."""
    fb = _make(source_qa_pair_id="already-deleted-qa-pair")
    repo.save(fb)
    found = repo.find_by_id(fb.id)
    assert found is not None
    assert found.source_qa_pair_id == "already-deleted-qa-pair"
