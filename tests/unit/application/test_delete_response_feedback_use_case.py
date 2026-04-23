from unittest.mock import MagicMock

from src.application.commands.delete_response_feedback_command import (
    DeleteResponseFeedbackCommand,
)
from src.application.use_cases.delete_response_feedback_use_case import (
    DeleteResponseFeedbackUseCase,
)


def _make_use_case():
    repo = MagicMock()
    return DeleteResponseFeedbackUseCase(response_feedback_repository=repo), repo


def test_calls_repository_delete():
    use_case, repo = _make_use_case()
    use_case.execute(DeleteResponseFeedbackCommand(feedback_id="abc"))
    assert repo.delete.call_count == 1
    called_arg = repo.delete.call_args[0][0]
    assert called_arg.value == "abc"


def test_idempotent_when_repo_returns_false():
    use_case, repo = _make_use_case()
    repo.delete.return_value = False
    # Should not raise
    use_case.execute(DeleteResponseFeedbackCommand(feedback_id="missing"))


def test_returns_none():
    use_case, repo = _make_use_case()
    repo.delete.return_value = True
    result = use_case.execute(DeleteResponseFeedbackCommand(feedback_id="x"))
    assert result is None
