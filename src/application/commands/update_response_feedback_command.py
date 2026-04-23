from dataclasses import dataclass


@dataclass(frozen=True)
class UpdateResponseFeedbackCommand:
    feedback_id: str
    problem: str | None = None
    desired_behavior: str | None = None
