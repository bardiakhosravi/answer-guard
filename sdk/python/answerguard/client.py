from __future__ import annotations

import sys
from dataclasses import dataclass

from answerguard.capture import BackgroundCaptureDispatcher


@dataclass
class CaptureResult:
    qa_pair_id: str
    captured_at: str


class AnswerGuard:
    def __init__(
        self, endpoint: str, source_system_id: str, timeout_ms: int = 2000
    ) -> None:
        self._endpoint = endpoint.rstrip("/")
        self._source_system_id = source_system_id
        self._timeout_s = timeout_ms / 1000
        self._dispatcher = BackgroundCaptureDispatcher(timeout_ms=timeout_ms)

    def capture(
        self, question: str, answer: str, metadata: dict[str, str] | None = None
    ) -> None:
        """Fire-and-forget capture. Never raises. Returns immediately."""
        self._dispatcher.dispatch(self._do_capture, question, answer, metadata or {})

    def capture_sync(
        self, question: str, answer: str, metadata: dict[str, str] | None = None
    ) -> CaptureResult:
        """Blocking capture. Raises on failure."""
        return self._do_capture(question, answer, metadata or {})

    def _do_capture(
        self, question: str, answer: str, metadata: dict[str, str]
    ) -> CaptureResult:
        import httpx

        payload = {
            "question": question,
            "answer": answer,
            "source_system_id": self._source_system_id,
            "metadata": metadata,
        }
        response = httpx.post(
            f"{self._endpoint}/v1/capture",
            json=payload,
            timeout=self._timeout_s,
        )
        response.raise_for_status()
        data = response.json()
        return CaptureResult(
            qa_pair_id=data["qa_pair_id"],
            captured_at=data["captured_at"],
        )
