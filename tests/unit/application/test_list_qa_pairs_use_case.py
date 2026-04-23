from datetime import datetime, timezone
from unittest.mock import MagicMock

from src.application.queries.list_qa_pairs_query import ListQAPairsQuery
from src.application.use_cases.list_qa_pairs_use_case import ListQAPairsUseCase
from src.domain.model.qa_pair.ingestion_method import IngestionMethod
from src.domain.model.qa_pair.qa_pair import QAPair


def _make_use_case(list_result=None, total=0):
    repo = MagicMock()
    repo.list_paginated.return_value = (list_result or [], total)
    return ListQAPairsUseCase(repo), repo


def _sample_pair(question="Q", answer="A", source="sys-1") -> QAPair:
    return QAPair.create(question, answer, source, IngestionMethod.HISTORICAL_IMPORT, external_id="ext-1")


def test_returns_empty_when_no_records():
    use_case, repo = _make_use_case()
    result = use_case.execute(ListQAPairsQuery())
    assert result.total == 0
    assert result.items == []
    assert result.page == 1
    assert result.page_size == 50


def test_maps_domain_objects_to_summary_dtos():
    pair = _sample_pair("What is X?", "X is Y.")
    use_case, repo = _make_use_case(list_result=[pair], total=1)

    result = use_case.execute(ListQAPairsQuery(page=1, page_size=10))

    assert result.total == 1
    assert len(result.items) == 1
    summary = result.items[0]
    assert summary.id == pair.id.value
    assert summary.question_text == "What is X?"
    assert summary.answer_text == "X is Y."
    assert summary.ingestion_method == IngestionMethod.HISTORICAL_IMPORT.value
    assert summary.external_id == "ext-1"
    # captured_at is serialised to ISO string
    assert isinstance(summary.captured_at, str)
    assert "T" in summary.captured_at


def test_pagination_and_filter_forwarded_to_repository():
    use_case, repo = _make_use_case()

    use_case.execute(
        ListQAPairsQuery(page=3, page_size=25, source_system_id="sys-42", search="refund")
    )

    repo.list_paginated.assert_called_once_with(
        page=3, page_size=25, source_system_id="sys-42", search="refund"
    )


def test_source_timestamp_serialised_when_present():
    pair = _sample_pair()
    object.__setattr__(pair, "source_timestamp", datetime(2025, 1, 2, 3, 4, 5, tzinfo=timezone.utc))
    use_case, repo = _make_use_case(list_result=[pair], total=1)

    result = use_case.execute(ListQAPairsQuery())

    assert result.items[0].source_timestamp is not None
    assert result.items[0].source_timestamp.startswith("2025-01-02")


def test_source_timestamp_none_preserved():
    pair = _sample_pair()
    use_case, repo = _make_use_case(list_result=[pair], total=1)

    result = use_case.execute(ListQAPairsQuery())

    assert result.items[0].source_timestamp is None
