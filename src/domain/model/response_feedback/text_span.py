from __future__ import annotations

from dataclasses import dataclass

from src.domain.exceptions import DomainException


@dataclass(frozen=True)
class TextSpan:
    """Character range within the source answer text. Used when the PM
    selects only a portion of the answer to provide feedback on."""

    start: int
    end: int

    def __post_init__(self) -> None:
        if self.start < 0:
            raise DomainException("TextSpan: start must be >= 0")
        if self.end <= self.start:
            raise DomainException("TextSpan: end must be greater than start")

    def length(self) -> int:
        return self.end - self.start

    def covers(self, offset: int) -> bool:
        return self.start <= offset < self.end
