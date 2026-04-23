from __future__ import annotations

from src.application.commands.submit_response_feedback_command import (
    SubmitResponseFeedbackCommand,
)
from src.application.ports.primary._response_feedback_response import (
    ResponseFeedbackResponse,
)
from src.application.ports.primary.submit_response_feedback_port import (
    SubmitResponseFeedbackPort,
)
from src.domain.model.response_feedback.response_feedback import ResponseFeedback
from src.domain.ports.response_feedback_repository import ResponseFeedbackRepository


class SubmitResponseFeedbackUseCase(SubmitResponseFeedbackPort):
    def __init__(self, response_feedback_repository: ResponseFeedbackRepository) -> None:
        self._repo = response_feedback_repository

    def execute(self, command: SubmitResponseFeedbackCommand) -> ResponseFeedbackResponse:
        feedback = ResponseFeedback.create(
            source_qa_pair_id=command.source_qa_pair_id,
            excerpt=command.excerpt,
            problem=command.problem,
            desired_behavior=command.desired_behavior,
            span_start=command.span_start,
            span_end=command.span_end,
        )
        self._repo.save(feedback)
        return ResponseFeedbackResponse.from_domain(feedback)
