---
sidebar_position: 5
---

# TypeScript SDK

Add runtime Q&A capture to your existing TypeScript agent pipeline in under 5 lines of code.

## Installation

```bash
npm install ./sdk/typescript
```

:::note Publishing to npm
The package will be published to npm as `@answerguard/sdk`. Until then, install from the source directory as shown above.
:::

## Minimal integration

```typescript
import { AnswerGuard } from '@answerguard/sdk';

const guard = new AnswerGuard({ endpoint: 'http://localhost:8080', sourceSystemId: 'my-agent' });

// In your agent response handler:
guard.capture(userQuestion, agentResponse);
```

`capture()` is fire-and-forget — it does not `await` the network call and never throws.

## `capture()` vs `captureAsync()`

| Method | Behaviour | When to use |
|--------|-----------|-------------|
| `capture(question, answer, options?)` | Fire-and-forget. Returns `void` immediately. Errors logged to `console.error`. | Production — zero overhead on your response path |
| `captureAsync(question, answer, options?)` | Returns `Promise<{qa_pair_id, captured_at}>`. Throws on failure. | Debugging, testing, scripts |

## Passing metadata

```typescript
guard.capture(userQuestion, agentResponse, {
  metadata: {
    topic: 'billing',
    sessionId: session.id,
    userSegment: 'enterprise',
  },
});
```

Metadata values must be strings. Keys are arbitrary.

## Constructor options

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `endpoint` | string | ✅ | — | AnswerGuard server URL (e.g. `'http://localhost:8080'`) |
| `sourceSystemId` | string | ✅ | — | Identifies this agent system in AnswerGuard |
| `timeoutMs` | number | ❌ | `2000` | HTTP timeout in milliseconds |

## Fail-open behaviour

If the AnswerGuard server is unreachable, `capture()` logs the error to `console.error` and returns without throwing. Your agent pipeline is never blocked.

To surface errors during development, use `captureAsync()` — it throws on HTTP failures.

## Full example

```typescript
import { AnswerGuard } from '@answerguard/sdk';

const guard = new AnswerGuard({
  endpoint: process.env.ANSWERGUARD_ENDPOINT!,
  sourceSystemId: 'prod-agent-v2',
  timeoutMs: 1000,
});

async function handleUserMessage(userId: string, question: string): Promise<string> {
  const answer = await yourAgent.generate(question);

  guard.capture(question, answer, {
    metadata: { userId },
  });

  return answer;
}
```
