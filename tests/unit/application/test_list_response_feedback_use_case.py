from unittest.mock import MagicMock

from src.application.queries.list_response_feedback_query import (
    ListResponseFeedbackQuery,
)
from src.application.use_cases.list_response_feedback_use_case import (
    ListResponseFeedbackUseCase,
)
from src.domain.model.response_feedback.response_feedback import ResponseFeedback


def _make_use_case():
    repo = MagicMock()
    return ListResponseFeedbackUseCase(response_feedback_repository=repo), repo


def test_forwards_pagination_and_search_to_repository():
    use_case, repo = _make_use_case()
    repo.list_paginated.return_value = ([], 0)
    use_case.execute(ListResponseFeedbackQuery(page=3, page_size=25, search="refund"))
    repo.list_paginated.assert_called_once_with(page=3, page_size=25, search="refund")


def test_maps_domain_objects_to_dtos():
    use_case, repo = _make_use_case()
    fb = ResponseFeedback.create(
        source_qa_pair_id="qa-1",
        excerpt="hi",
        problem="too long",
        desired_behavior="be concise",
    )
    repo.list_paginated.return_value = ([fb], 1)
    result = use_case.execute(ListResponseFeedbackQuery())
    assert result.total == 1
    assert len(result.items) == 1
    assert result.items[0].id == fb.id.value
    assert result.items[0].problem == "too long"


def test_empty_result():
    use_case, repo = _make_use_case()
    repo.list_paginated.return_value = ([], 0)
    result = use_case.execute(ListResponseFeedbackQuery())
    assert result.items == []
    assert result.total == 0
