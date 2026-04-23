from __future__ import annotations

from src.application.ports.primary._response_feedback_response import (
    ResponseFeedbackResponse,
)
from src.application.ports.primary.list_response_feedback_port import (
    ListResponseFeedbackPort,
    ListResponseFeedbackResponse,
)
from src.application.queries.list_response_feedback_query import (
    ListResponseFeedbackQuery,
)
from src.domain.ports.response_feedback_repository import ResponseFeedbackRepository


class ListResponseFeedbackUseCase(ListResponseFeedbackPort):
    def __init__(self, response_feedback_repository: ResponseFeedbackRepository) -> None:
        self._repo = response_feedback_repository

    def execute(self, query: ListResponseFeedbackQuery) -> ListResponseFeedbackResponse:
        items, total = self._repo.list_paginated(
            page=query.page,
            page_size=query.page_size,
            search=query.search,
        )
        return ListResponseFeedbackResponse(
            total=total,
            page=query.page,
            page_size=query.page_size,
            items=[ResponseFeedbackResponse.from_domain(item) for item in items],
        )
