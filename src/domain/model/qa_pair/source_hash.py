from __future__ import annotations

import hashlib
from dataclasses import dataclass


@dataclass(frozen=True)
class SourceHash:
    value: str

    @classmethod
    def compute(cls, question_text: str, answer_text: str, source_system_id: str) -> "SourceHash":
        raw = f"{question_text}{answer_text}{source_system_id}"
        return cls(value=hashlib.sha256(raw.encode("utf-8")).hexdigest())
