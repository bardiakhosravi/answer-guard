from __future__ import annotations

from src.application.commands.delete_response_feedback_command import (
    DeleteResponseFeedbackCommand,
)
from src.application.ports.primary.delete_response_feedback_port import (
    DeleteResponseFeedbackPort,
)
from src.domain.model.response_feedback.response_feedback_id import ResponseFeedbackId
from src.domain.ports.response_feedback_repository import ResponseFeedbackRepository


class DeleteResponseFeedbackUseCase(DeleteResponseFeedbackPort):
    def __init__(self, response_feedback_repository: ResponseFeedbackRepository) -> None:
        self._repo = response_feedback_repository

    def execute(self, command: DeleteResponseFeedbackCommand) -> None:
        self._repo.delete(ResponseFeedbackId(command.feedback_id))
