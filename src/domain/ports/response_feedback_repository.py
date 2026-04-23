from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from src.domain.model.response_feedback.response_feedback import ResponseFeedback
    from src.domain.model.response_feedback.response_feedback_id import (
        ResponseFeedbackId,
    )


class ResponseFeedbackRepository(ABC):
    @abstractmethod
    def save(self, feedback: "ResponseFeedback") -> None:
        """Persist a new or updated ResponseFeedback record."""

    @abstractmethod
    def find_by_id(self, feedback_id: "ResponseFeedbackId") -> Optional["ResponseFeedback"]:
        """Return the ResponseFeedback with the given ID, or None if absent."""

    @abstractmethod
    def list_paginated(
        self,
        page: int,
        page_size: int,
        search: str | None = None,
    ) -> tuple[list["ResponseFeedback"], int]:
        """
        Return a page of ResponseFeedback records plus the total count.
        Ordered by created_at DESC. Search filters on excerpt, problem, or
        desired_behavior.
        """

    @abstractmethod
    def delete(self, feedback_id: "ResponseFeedbackId") -> bool:
        """Remove the record with the given ID. Returns True if a row was deleted."""
