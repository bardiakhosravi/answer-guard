# AnswerGuard — High-Level Technical Architecture

**Status:** Draft
**Date:** 2026-04-09
**Related:** [PRD.md](./PRD.md)

---

## 1. System Components

Self-hosted. The tool runs as a Docker container (or set of containers) in the client's infrastructure.

- **Web UI** — React/Next.js app for the review interface and guideline management
- **API Server** — handles SDK/API requests, runs the adherence engine
- **Database** — pluggable via adapter interface
- **LLM Integration** — pluggable via adapter interface

---

## 2. Integration Model

### SDK Integration (Primary)

TypeScript and Python SDKs that wrap the existing response flow with minimal code change.

```typescript
// Before: direct response
const response = await agent.generateResponse(userQuestion);
return response;

// After: response goes through AnswerGuard
import { AnswerGuard } from '@answerguard/sdk';

const guard = new AnswerGuard({ endpoint: 'http://localhost:8080' });
const draft = await agent.generateResponse(userQuestion);
const final = await guard.enforce(draft, { topic: 'billing', userId });
return final.response;
```

### API Integration (Alternative)

REST API for teams that prefer direct HTTP integration or use languages without an SDK.

```
POST /v1/enforce
{
  "draft": "Here is the agent's draft response...",
  "metadata": {
    "topic": "billing",
    "user_id": "u_123",
    "question": "How do I get a refund?"
  }
}
```

---

## 3. Data Ingestion

There are two separate database concerns:

### Source Connector (inbound — read-only)

The client has an existing database of question/answer pairs. The source connector reads from this system and ingests the data into AnswerGuard's own database. AnswerGuard **never writes to the client's production Q&A system**.

Supported ingestion methods:
- **Batch import** — a CLI or API endpoint that accepts bulk Q&A data (CSV, JSON, or direct database pull) for one-time or recurring imports
- **Source database connector** — a read-only adapter that connects to the client's Q&A database and pulls data on a schedule or on-demand

*Note: The specific source connector will depend on the client's database and infrastructure. We'll detail this during technical discovery.*

### AnswerGuard's Database (our persistence layer)

All AnswerGuard data lives in a database that the client provisions and owns on their own infrastructure (self-hosted). The client provides a connection string and AnswerGuard manages the schema.

This database stores:
- Ingested Q&A pairs (copied from the source)
- Annotations and feedback from PM reviews
- Guidelines
- Enforcement logs (original draft, final output, which guidelines fired, latency)

**V1 supports PostgreSQL only.** Additional database support (MySQL, etc.) can be added later via adapter interfaces.

### New Data (going forward)

Responses flowing through the SDK or API at runtime are automatically written to AnswerGuard's database and available for review.

---

## 4. Adherence Engine — Tiered Architecture

The engine uses a tiered approach to balance quality enforcement with latency:

| Tier | What it does | Latency | When it fires |
|------|-------------|---------|---------------|
| **Tier 1: Deterministic rules** | Regex phrase bans, length checks, required phrase checks. No LLM. | < 50ms | Every response |
| **Tier 2: Fast classification** | Single LLM call — "does this draft violate any active style/content/pattern guidelines?" Returns pass/flag + confidence. | ~200-400ms | Every response that passes Tier 1 |
| **Tier 3: Targeted rewrite** | Full LLM rewrite of only the flagged sections, guided by the specific violated guidelines. | 1-3s | Only when Tier 2 flags a violation above confidence threshold |

**Design principles:**
- **Fail-open:** If the adherence engine errors or times out, serve the original draft. Never block the user from getting a response.
- **Preserve intent:** Rewrites fix the flagged issue only, not rephrase the entire response.
- **Transparency:** Store the original draft and final output. Log which guidelines triggered changes.
- **Configurable aggression:** PM sets the confidence threshold for Tier 3 rewrites.

---

## 5. Provider-Agnostic Design

The tool ships with adapter interfaces for both LLM and database integrations. Users configure their preferred providers.

### LLM Adapter

- Interface defines: `classify(draft, guidelines) → pass/flag` and `rewrite(draft, violations, guidelines) → revised`
- Ship with adapters for: OpenAI, Anthropic, Google Gemini, and a generic OpenAI-compatible adapter (covers most local/self-hosted models like Ollama, vLLM, etc.)
- Users configure via environment variable or config file: provider, model, API key, endpoint URL
- Community can contribute adapters for additional providers

### Database

- V1 supports PostgreSQL only. Client provides a connection string.
- AnswerGuard manages its own schema via migration tooling.
- Additional database support can be added later via an adapter interface.
