from __future__ import annotations

import sys
import threading
from concurrent.futures import ThreadPoolExecutor


class BackgroundCaptureDispatcher:
    def __init__(self, timeout_ms: int = 2000) -> None:
        self._timeout_s = timeout_ms / 1000
        self._executor = ThreadPoolExecutor(
            max_workers=2, thread_name_prefix="ag-capture"
        )
        # Make threads daemon so they don't block interpreter shutdown
        for t in threading.enumerate():
            if t.name.startswith("ag-capture"):
                t.daemon = True

    def dispatch(self, fn, *args, **kwargs) -> None:
        """Submit fn(*args, **kwargs) to background thread. Never raises."""
        try:
            self._executor.submit(self._run_safely, fn, *args, **kwargs)
        except Exception as exc:
            print(f"[AnswerGuard] Failed to dispatch capture: {exc}", file=sys.stderr)

    @staticmethod
    def _run_safely(fn, *args, **kwargs) -> None:
        try:
            fn(*args, **kwargs)
        except Exception as exc:
            print(f"[AnswerGuard] Capture failed: {exc}", file=sys.stderr)
