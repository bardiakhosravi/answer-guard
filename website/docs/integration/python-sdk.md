---
sidebar_position: 4
---

# Python SDK

Add runtime Q&A capture to your existing Python agent pipeline in under 5 lines of code.

## Installation

```bash
pip install -e ./sdk/python
```

:::note Publishing to PyPI
The package will be published to PyPI as `answerguard-sdk`. Until then, install from the source directory as shown above.
:::

## Minimal integration

```python
from answerguard import AnswerGuard

guard = AnswerGuard(endpoint="http://localhost:8080", source_system_id="my-agent")

# In your agent response handler:
guard.capture(question=user_question, answer=agent_response)
```

That's it. `capture()` is fire-and-forget — it returns immediately and never raises an exception.

## `capture()` vs `capture_sync()`

| Method | Behaviour | When to use |
|--------|-----------|-------------|
| `capture(question, answer, metadata)` | Fire-and-forget. Returns `None` immediately. Errors logged to stderr. | Production — adds &lt;1ms to your response path |
| `capture_sync(question, answer, metadata)` | Blocking. Returns `CaptureResult`. Raises on failure. | Debugging, testing, scripts |

## Passing metadata

```python
guard.capture(
    question=user_question,
    answer=agent_response,
    metadata={
        "topic": "billing",
        "session_id": session.id,
        "user_segment": "enterprise",
    }
)
```

Metadata values must be strings. Keys are arbitrary — use whatever is meaningful for your product.

## Constructor options

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `endpoint` | string | ✅ | — | AnswerGuard server URL (e.g. `"http://localhost:8080"`) |
| `source_system_id` | string | ✅ | — | Identifies this agent system in AnswerGuard |
| `timeout_ms` | integer | ❌ | `2000` | HTTP timeout in milliseconds for capture calls |

## Fail-open behaviour

If the AnswerGuard server is unreachable, `capture()` silently logs the error to `stderr` and returns without raising. Your agent pipeline is never blocked.

To surface errors during development, use `capture_sync()` instead — it raises `httpx.HTTPError` on failure.

## Full example

```python
import os
from answerguard import AnswerGuard

guard = AnswerGuard(
    endpoint=os.environ["ANSWERGUARD_ENDPOINT"],
    source_system_id="prod-agent-v2",
    timeout_ms=1000,
)

def handle_user_message(user_id: str, question: str) -> str:
    answer = your_agent.generate(question)

    guard.capture(
        question=question,
        answer=answer,
        metadata={"user_id": user_id},
    )

    return answer
```
