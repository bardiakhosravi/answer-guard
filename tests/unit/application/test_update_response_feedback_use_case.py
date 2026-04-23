from unittest.mock import MagicMock

import pytest

from src.application.commands.update_response_feedback_command import (
    UpdateResponseFeedbackCommand,
)
from src.application.ports.primary.get_response_feedback_port import (
    ResponseFeedbackNotFoundError,
)
from src.application.use_cases.update_response_feedback_use_case import (
    UpdateResponseFeedbackUseCase,
)
from src.domain.exceptions import DomainException
from src.domain.model.response_feedback.response_feedback import ResponseFeedback


def _make_feedback():
    return ResponseFeedback.create(
        source_qa_pair_id="qa-1",
        excerpt="excerpt",
        problem="original problem",
        desired_behavior="original behavior",
    )


def _make_use_case(stored=None):
    repo = MagicMock()
    repo.find_by_id.return_value = stored
    return UpdateResponseFeedbackUseCase(response_feedback_repository=repo), repo


def test_updates_both_fields():
    feedback = _make_feedback()
    use_case, repo = _make_use_case(stored=feedback)
    result = use_case.execute(
        UpdateResponseFeedbackCommand(
            feedback_id=feedback.id.value,
            problem="new problem",
            desired_behavior="new behavior",
        )
    )
    assert result.problem == "new problem"
    assert result.desired_behavior == "new behavior"
    assert repo.save.call_count == 1


def test_partial_update_preserves_other_field():
    feedback = _make_feedback()
    use_case, _ = _make_use_case(stored=feedback)
    result = use_case.execute(
        UpdateResponseFeedbackCommand(
            feedback_id=feedback.id.value,
            problem="new problem",
        )
    )
    assert result.problem == "new problem"
    assert result.desired_behavior == "original behavior"


def test_both_fields_none_raises():
    feedback = _make_feedback()
    use_case, _ = _make_use_case(stored=feedback)
    with pytest.raises(DomainException):
        use_case.execute(UpdateResponseFeedbackCommand(feedback_id=feedback.id.value))


def test_missing_id_raises_not_found():
    use_case, _ = _make_use_case(stored=None)
    with pytest.raises(ResponseFeedbackNotFoundError):
        use_case.execute(
            UpdateResponseFeedbackCommand(
                feedback_id="does-not-exist", problem="x", desired_behavior="y"
            )
        )


def test_empty_supplied_value_raises():
    feedback = _make_feedback()
    use_case, _ = _make_use_case(stored=feedback)
    with pytest.raises(DomainException):
        use_case.execute(
            UpdateResponseFeedbackCommand(feedback_id=feedback.id.value, problem="")
        )
