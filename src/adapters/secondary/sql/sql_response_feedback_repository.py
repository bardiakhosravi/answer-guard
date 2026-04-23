from __future__ import annotations

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from src.adapters.secondary.sql.models.response_feedback_model import ResponseFeedbackModel
from src.domain.model.response_feedback.response_feedback import ResponseFeedback
from src.domain.model.response_feedback.response_feedback_id import ResponseFeedbackId
from src.domain.model.response_feedback.text_span import TextSpan
from src.domain.ports.response_feedback_repository import ResponseFeedbackRepository


class SqlResponseFeedbackRepository(ResponseFeedbackRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def save(self, feedback: ResponseFeedback) -> None:
        model = self._session.get(ResponseFeedbackModel, feedback.id.value)
        if model is None:
            model = ResponseFeedbackModel(id=feedback.id.value)
            self._session.add(model)
        model.source_qa_pair_id = feedback.source_qa_pair_id
        model.excerpt = feedback.excerpt
        model.span_start = feedback.span.start if feedback.span else None
        model.span_end = feedback.span.end if feedback.span else None
        model.problem = feedback.problem
        model.desired_behavior = feedback.desired_behavior
        model.created_at = feedback.created_at
        model.updated_at = feedback.updated_at
        self._session.commit()

    def find_by_id(self, feedback_id: ResponseFeedbackId) -> ResponseFeedback | None:
        model = self._session.get(ResponseFeedbackModel, feedback_id.value)
        return self._to_domain(model) if model else None

    def list_paginated(
        self,
        page: int,
        page_size: int,
        search: str | None = None,
    ) -> tuple[list[ResponseFeedback], int]:
        if page < 1:
            page = 1
        if page_size < 1:
            page_size = 50

        filters = []
        if search:
            pattern = f"%{search}%"
            filters.append(
                or_(
                    ResponseFeedbackModel.excerpt.ilike(pattern),
                    ResponseFeedbackModel.problem.ilike(pattern),
                    ResponseFeedbackModel.desired_behavior.ilike(pattern),
                )
            )

        total = self._session.execute(
            select(func.count()).select_from(ResponseFeedbackModel).where(*filters)
        ).scalar_one() or 0

        models = (
            self._session.execute(
                select(ResponseFeedbackModel)
                .where(*filters)
                .order_by(ResponseFeedbackModel.created_at.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
            .scalars()
            .all()
        )
        return [self._to_domain(m) for m in models], total

    def delete(self, feedback_id: ResponseFeedbackId) -> bool:
        model = self._session.get(ResponseFeedbackModel, feedback_id.value)
        if model is None:
            return False
        self._session.delete(model)
        self._session.commit()
        return True

    def _to_domain(self, model: ResponseFeedbackModel) -> ResponseFeedback:
        span: TextSpan | None
        if model.span_start is not None and model.span_end is not None:
            span = TextSpan(start=model.span_start, end=model.span_end)
        else:
            span = None
        return ResponseFeedback(
            id=ResponseFeedbackId(model.id),
            source_qa_pair_id=model.source_qa_pair_id,
            excerpt=model.excerpt,
            span=span,
            problem=model.problem,
            desired_behavior=model.desired_behavior,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
