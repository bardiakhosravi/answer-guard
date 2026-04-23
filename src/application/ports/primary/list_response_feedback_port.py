from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from src.application.ports.primary._response_feedback_response import (
    ResponseFeedbackResponse,
)
from src.application.queries.list_response_feedback_query import (
    ListResponseFeedbackQuery,
)


@dataclass(frozen=True)
class ListResponseFeedbackResponse:
    total: int
    page: int
    page_size: int
    items: list[ResponseFeedbackResponse]


class ListResponseFeedbackPort(ABC):
    @abstractmethod
    def execute(self, query: ListResponseFeedbackQuery) -> ListResponseFeedbackResponse:
        """Return a paginated list of ResponseFeedback records."""
