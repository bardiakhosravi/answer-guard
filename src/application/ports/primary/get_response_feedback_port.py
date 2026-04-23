from __future__ import annotations

from abc import ABC, abstractmethod

from src.application.ports.primary._response_feedback_response import (
    ResponseFeedbackResponse,
)
from src.domain.exceptions import DomainException


class ResponseFeedbackNotFoundError(DomainException):
    """Raised when a ResponseFeedback record with the given ID does not exist."""


class GetResponseFeedbackPort(ABC):
    @abstractmethod
    def execute(self, feedback_id: str) -> ResponseFeedbackResponse:
        """Return the ResponseFeedback with the given ID, or raise ResponseFeedbackNotFoundError."""
