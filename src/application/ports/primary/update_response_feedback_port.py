from __future__ import annotations

from abc import ABC, abstractmethod

from src.application.commands.update_response_feedback_command import (
    UpdateResponseFeedbackCommand,
)
from src.application.ports.primary._response_feedback_response import (
    ResponseFeedbackResponse,
)


class UpdateResponseFeedbackPort(ABC):
    @abstractmethod
    def execute(self, command: UpdateResponseFeedbackCommand) -> ResponseFeedbackResponse:
        """Update the problem and/or desired_behavior of an existing feedback record."""
