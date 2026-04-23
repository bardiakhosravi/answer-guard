from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from src.domain.exceptions import DomainException
from src.domain.model.response_feedback.response_feedback_id import ResponseFeedbackId
from src.domain.model.response_feedback.text_span import TextSpan


@dataclass(eq=False)
class ResponseFeedback:
    """PM feedback captured against an agent's answer.

    Links back to the source QAPair by identity (`source_qa_pair_id`). The
    QAPair is provenance; ResponseFeedback is an independent aggregate and is
    not owned by the QAPair.
    """

    id: ResponseFeedbackId
    source_qa_pair_id: str
    excerpt: str
    span: TextSpan | None
    problem: str
    desired_behavior: str
    created_at: datetime
    updated_at: datetime

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ResponseFeedback):
            return NotImplemented
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)

    @classmethod
    def create(
        cls,
        source_qa_pair_id: str,
        excerpt: str,
        problem: str,
        desired_behavior: str,
        span_start: int | None = None,
        span_end: int | None = None,
    ) -> "ResponseFeedback":
        if not source_qa_pair_id or not source_qa_pair_id.strip():
            raise DomainException("ResponseFeedback: source_qa_pair_id must not be empty")
        if not excerpt:
            raise DomainException("ResponseFeedback: excerpt must not be empty")
        if not problem or not problem.strip():
            raise DomainException("ResponseFeedback: problem must not be empty")
        if not desired_behavior or not desired_behavior.strip():
            raise DomainException("ResponseFeedback: desired_behavior must not be empty")

        span: TextSpan | None
        if span_start is None and span_end is None:
            span = None
        elif span_start is not None and span_end is not None:
            span = TextSpan(start=span_start, end=span_end)
        else:
            raise DomainException(
                "ResponseFeedback: span_start and span_end must be provided together"
            )

        now = datetime.now(timezone.utc)
        return cls(
            id=ResponseFeedbackId.generate(),
            source_qa_pair_id=source_qa_pair_id,
            excerpt=excerpt,
            span=span,
            problem=problem.strip(),
            desired_behavior=desired_behavior.strip(),
            created_at=now,
            updated_at=now,
        )

    def update(self, problem: str, desired_behavior: str) -> None:
        if not problem or not problem.strip():
            raise DomainException("ResponseFeedback: problem must not be empty")
        if not desired_behavior or not desired_behavior.strip():
            raise DomainException("ResponseFeedback: desired_behavior must not be empty")
        self.problem = problem.strip()
        self.desired_behavior = desired_behavior.strip()
        self.updated_at = datetime.now(timezone.utc)
