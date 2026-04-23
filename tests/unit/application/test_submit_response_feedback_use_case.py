from unittest.mock import MagicMock

import pytest

from src.application.commands.submit_response_feedback_command import (
    SubmitResponseFeedbackCommand,
)
from src.application.use_cases.submit_response_feedback_use_case import (
    SubmitResponseFeedbackUseCase,
)
from src.domain.exceptions import DomainException


def _make_use_case():
    repo = MagicMock()
    return SubmitResponseFeedbackUseCase(response_feedback_repository=repo), repo


def _make_command(**overrides) -> SubmitResponseFeedbackCommand:
    defaults = dict(
        source_qa_pair_id="qa-1",
        excerpt="agent reply",
        problem="too verbose",
        desired_behavior="be concise",
    )
    defaults.update(overrides)
    return SubmitResponseFeedbackCommand(**defaults)


def test_persists_feedback_and_returns_response():
    use_case, repo = _make_use_case()
    result = use_case.execute(_make_command())
    assert repo.save.call_count == 1
    assert len(result.id) == 36  # UUID length
    assert result.source_qa_pair_id == "qa-1"
    assert result.problem == "too verbose"


def test_with_span_persists_span():
    use_case, repo = _make_use_case()
    result = use_case.execute(_make_command(span_start=2, span_end=8))
    assert result.span_start == 2
    assert result.span_end == 8


def test_without_span_persists_nulls():
    use_case, _ = _make_use_case()
    result = use_case.execute(_make_command())
    assert result.span_start is None
    assert result.span_end is None


def test_empty_problem_raises():
    use_case, repo = _make_use_case()
    with pytest.raises(DomainException):
        use_case.execute(_make_command(problem=""))
    assert repo.save.call_count == 0


def test_partial_span_raises():
    use_case, _ = _make_use_case()
    with pytest.raises(DomainException):
        use_case.execute(_make_command(span_start=2))
