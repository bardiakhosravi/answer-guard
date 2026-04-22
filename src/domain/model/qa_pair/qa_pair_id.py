from __future__ import annotations

import uuid
from dataclasses import dataclass


@dataclass(frozen=True)
class QAPairId:
    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("QAPairId cannot be empty")

    @classmethod
    def generate(cls) -> "QAPairId":
        return cls(value=str(uuid.uuid4()))
