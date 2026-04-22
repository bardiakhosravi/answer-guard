from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from src.application.commands.capture_response_command import CaptureResponseCommand


@dataclass(frozen=True)
class CaptureResponse:
    qa_pair_id: str
    captured_at: str


class CaptureRuntimeResponsePort(ABC):
    @abstractmethod
    def execute(self, command: CaptureResponseCommand) -> CaptureResponse:
        """Capture a single Q&A pair at runtime."""
