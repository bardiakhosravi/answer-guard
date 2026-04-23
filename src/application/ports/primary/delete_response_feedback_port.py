from __future__ import annotations

from abc import ABC, abstractmethod

from src.application.commands.delete_response_feedback_command import (
    DeleteResponseFeedbackCommand,
)


class DeleteResponseFeedbackPort(ABC):
    @abstractmethod
    def execute(self, command: DeleteResponseFeedbackCommand) -> None:
        """Delete a feedback record. Idempotent: silently succeeds if the ID does not exist."""
