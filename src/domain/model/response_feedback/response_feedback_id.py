from __future__ import annotations

import uuid
from dataclasses import dataclass

from src.domain.exceptions import DomainException


@dataclass(frozen=True)
class ResponseFeedbackId:
    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise DomainException("ResponseFeedbackId cannot be empty")

    @classmethod
    def generate(cls) -> "ResponseFeedbackId":
        return cls(value=str(uuid.uuid4()))
