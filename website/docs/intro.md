---
sidebar_position: 1
slug: /
---

# Overview

AnswerGuard is an open-source tool that lets product managers improve the quality of AI agent responses — without touching prompts or changing the underlying agent architecture.

## Who it's for

Software engineering teams that have built a user-facing conversational product powered by an agent system, and need a way for non-technical team members to systematically improve response quality over time.

## The problem it solves

Today, if a PM wants to fix a bad agent response — one that uses the wrong tone, buries the key information, or violates a company guideline — their only option is to file a ticket and wait for engineering to update prompts. This is slow, doesn't scale, and requires technical knowledge the PM doesn't have.

**AnswerGuard closes the loop**: a PM reviews agent responses, highlights what's wrong, creates a guideline, and that guideline is enforced on future responses — all without engineering involvement.

## How it works

```
Your agent system ──► AnswerGuard ──► PM Review Interface
                           │
                           ▼
                    Guideline Engine
                    (enforces quality on future responses)
```

1. **Ingest** — AnswerGuard captures Q&A pairs from your agent system, either by importing historical data from BigQuery or capturing new responses at runtime via SDK.
2. **Review** — PMs browse responses in the AnswerGuard interface.
3. **Capture feedback** — PMs highlight problem passages (or flag the whole response), describe what's wrong, and describe how the agent should behave instead. Each piece of feedback is stored as a standalone record that references the source Q&A for provenance. See [Response feedback →](/docs/governance/response-feedback).
4. **Enforce** — A future adherence engine will use captured feedback to improve responses before they reach users (not yet implemented).

## Next steps

- **[Quickstart →](/docs/quickstart)** — Get a local instance running in under 30 minutes (no Docker required).
- **[Integration Guide →](/docs/integration/)** — Connect AnswerGuard to your existing agent system and BigQuery dataset.
