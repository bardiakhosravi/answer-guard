from __future__ import annotations

from src.application.ports.primary._response_feedback_response import (
    ResponseFeedbackResponse,
)
from src.application.ports.primary.get_response_feedback_port import (
    GetResponseFeedbackPort,
    ResponseFeedbackNotFoundError,
)
from src.domain.model.response_feedback.response_feedback_id import ResponseFeedbackId
from src.domain.ports.response_feedback_repository import ResponseFeedbackRepository


class GetResponseFeedbackUseCase(GetResponseFeedbackPort):
    def __init__(self, response_feedback_repository: ResponseFeedbackRepository) -> None:
        self._repo = response_feedback_repository

    def execute(self, feedback_id: str) -> ResponseFeedbackResponse:
        feedback = self._repo.find_by_id(ResponseFeedbackId(feedback_id))
        if feedback is None:
            raise ResponseFeedbackNotFoundError(
                f"ResponseFeedback {feedback_id} not found"
            )
        return ResponseFeedbackResponse.from_domain(feedback)
