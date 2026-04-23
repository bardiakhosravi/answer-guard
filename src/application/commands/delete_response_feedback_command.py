from dataclasses import dataclass


@dataclass(frozen=True)
class DeleteResponseFeedbackCommand:
    feedback_id: str
