from __future__ import annotations

from src.application.commands.update_response_feedback_command import (
    UpdateResponseFeedbackCommand,
)
from src.application.ports.primary._response_feedback_response import (
    ResponseFeedbackResponse,
)
from src.application.ports.primary.get_response_feedback_port import (
    ResponseFeedbackNotFoundError,
)
from src.application.ports.primary.update_response_feedback_port import (
    UpdateResponseFeedbackPort,
)
from src.domain.exceptions import DomainException
from src.domain.model.response_feedback.response_feedback_id import ResponseFeedbackId
from src.domain.ports.response_feedback_repository import ResponseFeedbackRepository


class UpdateResponseFeedbackUseCase(UpdateResponseFeedbackPort):
    def __init__(self, response_feedback_repository: ResponseFeedbackRepository) -> None:
        self._repo = response_feedback_repository

    def execute(self, command: UpdateResponseFeedbackCommand) -> ResponseFeedbackResponse:
        if command.problem is None and command.desired_behavior is None:
            raise DomainException(
                "UpdateResponseFeedback: at least one of problem or desired_behavior must be provided"
            )

        feedback = self._repo.find_by_id(ResponseFeedbackId(command.feedback_id))
        if feedback is None:
            raise ResponseFeedbackNotFoundError(
                f"ResponseFeedback {command.feedback_id} not found"
            )

        new_problem = command.problem if command.problem is not None else feedback.problem
        new_desired_behavior = (
            command.desired_behavior
            if command.desired_behavior is not None
            else feedback.desired_behavior
        )

        feedback.update(problem=new_problem, desired_behavior=new_desired_behavior)
        self._repo.save(feedback)
        return ResponseFeedbackResponse.from_domain(feedback)
