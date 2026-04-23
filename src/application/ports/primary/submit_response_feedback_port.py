from __future__ import annotations

from abc import ABC, abstractmethod

from src.application.commands.submit_response_feedback_command import (
    SubmitResponseFeedbackCommand,
)
from src.application.ports.primary._response_feedback_response import (
    ResponseFeedbackResponse,
)


class SubmitResponseFeedbackPort(ABC):
    @abstractmethod
    def execute(self, command: SubmitResponseFeedbackCommand) -> ResponseFeedbackResponse:
        """Store PM feedback about an agent answer as a ResponseFeedback record."""
