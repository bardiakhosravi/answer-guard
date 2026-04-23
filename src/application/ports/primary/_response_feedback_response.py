from __future__ import annotations

from dataclasses import dataclass

from src.domain.model.response_feedback.response_feedback import ResponseFeedback


@dataclass(frozen=True)
class ResponseFeedbackResponse:
    id: str
    source_qa_pair_id: str
    excerpt: str
    span_start: int | None
    span_end: int | None
    problem: str
    desired_behavior: str
    created_at: str
    updated_at: str

    @classmethod
    def from_domain(cls, feedback: ResponseFeedback) -> "ResponseFeedbackResponse":
        return cls(
            id=feedback.id.value,
            source_qa_pair_id=feedback.source_qa_pair_id,
            excerpt=feedback.excerpt,
            span_start=feedback.span.start if feedback.span else None,
            span_end=feedback.span.end if feedback.span else None,
            problem=feedback.problem,
            desired_behavior=feedback.desired_behavior,
            created_at=feedback.created_at.isoformat(),
            updated_at=feedback.updated_at.isoformat(),
        )
