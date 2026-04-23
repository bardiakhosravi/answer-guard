from dataclasses import dataclass


@dataclass(frozen=True)
class SubmitResponseFeedbackCommand:
    source_qa_pair_id: str
    excerpt: str
    problem: str
    desired_behavior: str
    span_start: int | None = None
    span_end: int | None = None
