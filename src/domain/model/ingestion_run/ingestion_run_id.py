from __future__ import annotations

import uuid
from dataclasses import dataclass


@dataclass(frozen=True)
class IngestionRunId:
    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("IngestionRunId cannot be empty")

    @classmethod
    def generate(cls) -> "IngestionRunId":
        return cls(value=str(uuid.uuid4()))
