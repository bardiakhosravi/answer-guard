# AnswerGuard — Product Requirements Document (Draft v1)

**Response Feedback and Adherence Layer for Agent-Based Products**
**Status:** Draft
**Date:** 2026-04-09

---

## 1. Problem

Product managers overseeing agent-based conversational products have no practical way to improve response quality over time. They can read logs, but they cannot:

- Highlight a specific sentence in a response and say "this is wrong"
- Record structured feedback (banned phrases, tone issues, missing context, incorrect structure)
- Turn that feedback into enforceable guidelines
- Have those guidelines automatically applied to future responses

Today, the PM's only option is to log issues in a spreadsheet or Slack, then ask engineering to update prompts. This is slow, doesn't scale, and creates a bottleneck where every quality improvement requires an engineer's time. Existing tools address adjacent problems — observability platforms (Langfuse) trace LLM calls but don't turn PM feedback into enforceable rules, and runtime validation frameworks (Guardrails AI) enforce rules but require engineers to define them in code. None of them connect the full loop.

**The gap:** No tool lets a PM go from "this sentence is wrong" to "future responses follow this standard" without engineering involvement. The feedback-to-enforcement loop doesn't exist as a product.

---

## 2. Target User

**Primary:** Product managers responsible for the quality of agent-generated responses in customer-facing products.

**Secondary:** Content/editorial leads, QA reviewers, compliance officers — anyone who needs to enforce standards on AI-generated content without engineering involvement.

**Not the target user (v1):** Engineers tuning prompts, ML teams evaluating model performance, ops teams monitoring uptime.

---

## 3. Solution Overview

An open-source **external layer** that sits between the existing agent system and the end user. The existing system is treated as a black box that produces draft responses. AnswerGuard reviews, governs, and — when needed — rewrites those drafts before they reach the user.

```
User Question → Existing Agent System → Draft Response → AnswerGuard → Final Response → User
```

The tool has three components:
1. **Review UI** — where PMs inspect responses and create feedback
2. **Guideline Manager** — where feedback becomes structured, enforceable rules
3. **Adherence Engine** — the runtime that enforces guidelines on every response

---

## 4. V1 Capabilities

### 4A. Review & Annotation UI

A web interface designed for non-technical users. No knowledge of prompts, models, or routing required.

**Core interactions:**
- Browse historical question/answer pairs with search and filtering
- **Span-level selection:** highlight a specific passage (sentence, paragraph, phrase) within a response
- Attach structured feedback to the highlighted span:
  - **Issue type:** Tone, accuracy, structure, verbosity, banned content, missing content, style
  - **Severity:** Critical (must fix now), important (should fix), suggestion (nice to have)
  - **Explanation:** Free-text description of what's wrong
  - **Preferred rewrite:** What the PM thinks the passage should say instead
  - **Scope:** Does this apply to all responses, responses in a specific topic/category, or just this one case? *Note: We can detail this out further. Scope can be driven by metadata that we ingest from your question/answer database.*
- View feedback history per response and across responses
- See which guidelines were created from feedback

### 4B. Guideline Manager

Where PM feedback is organized into enforceable rules. PMs manually create and manage guidelines (automated synthesis is out of scope for v1).

**Guideline structure:**
- **Name:** Human-readable label (e.g., "No legal hedging language in billing answers")
- **Rule type:**
  - *Phrase ban:* Never use these exact words/phrases (e.g., "it depends", "I'm just an AI")
  - *Phrase requirement:* Always include this phrase/disclaimer when topic X is detected
  - *Style rule:* Tone, length, structure guidance (e.g., "Lead with the direct answer, keep under 100 words")
  - *Content rule:* What to include or exclude (e.g., "Always link to the pricing page when discussing costs")
  - *Response pattern:* Template or structure for a specific category of questions
- **Scope:** Global (all responses), topic-specific (e.g., billing, onboarding), or keyword-triggered
- **Priority:** When guidelines conflict, which wins
- **Status:** Draft, active, disabled
- **Linked feedback:** Which review annotations led to this guideline

**Key operations:**
- Create guidelines manually or from a specific piece of feedback ("turn this feedback into a guideline")
- Edit, disable, re-enable guidelines
- Preview guideline impact: run a guideline against a set of historical responses to see what would change before activating it
- Export guidelines as structured data (JSON/YAML) for use in other systems

### 4C. Adherence Engine (Runtime)

The operational core. Enforces active guidelines on every draft response before it reaches the user. Uses a tiered approach — simple rules (phrase bans, length limits) are checked instantly, while more nuanced style and content checks use an LLM only when needed. This keeps latency acceptable for chat applications while still enforcing quality.

**Key behaviors:**
- If the draft is fine, pass it through untouched — don't rewrite for the sake of rewriting
- If a rewrite happens, the PM can see exactly which guidelines triggered it and what changed
- If the engine errors or times out, serve the original draft — never block the user
- The PM controls how aggressively the engine intervenes via a confidence threshold

*See [ARCHITECTURE.md](./ARCHITECTURE.md) for technical details on the tiered architecture.*

---

## 5. Integration & Data Ingestion

AnswerGuard integrates with the existing agent system through lightweight SDKs (TypeScript and Python) or a REST API. The integration requires minimal code change — a few lines to route draft responses through the adherence engine before returning them to the user.

**Data ingestion** supports two scenarios:
- **Historical data:** A source connector reads Q&A data from the client's existing database and ingests it into AnswerGuard's own database. AnswerGuard never writes to the client's production Q&A system.
- **New data:** Responses flowing through the SDK/API at runtime are automatically captured.

**AnswerGuard's database** is provisioned and owned by the client (self-hosted). The client points AnswerGuard at their database via a connection string. All AnswerGuard data — ingested Q&A pairs, annotations, guidelines, enforcement logs — lives there. V1 supports PostgreSQL.

**LLM provider** is configurable. The client chooses their preferred provider (OpenAI, Anthropic, Gemini, self-hosted, etc.).

**Logging-only mode** is available for teams that want to start with the review UI and guideline management without enabling runtime enforcement. Guidelines can be built and tested against historical data before turning on live enforcement.

*Note: A hosted offering (answerguard.cloud) where we manage infrastructure on behalf of the client is under consideration for a future release.*

*See [ARCHITECTURE.md](./ARCHITECTURE.md) for SDK examples, API specs, data ingestion details, and adapter interfaces.*

---

## 6. What Is Explicitly Out of Scope for V1

- **Automated guideline synthesis** — no auto-detection of feedback patterns. PMs create guidelines manually.
- **Prompt modification** — the tool never touches the underlying agent's prompts.
- **Agent observability** — no trace visualization, no routing analysis, no prompt version tracking. Data model reserves fields for future integration.
- **Database support beyond PostgreSQL** — v1 supports Postgres only. Additional databases can be added later.
- **Hosted offering (answerguard.cloud)** — v1 is self-hosted only.
- **Role-based access control** — v1 assumes a small trusted team. RBAC comes later.
- **A/B testing of guidelines** — no ability to test guideline X vs guideline Y on live traffic. Use the historical preview feature instead.
- **Streaming support** — v1 works with complete responses, not token-by-token streams.

---

## 7. Success Metrics

| Metric | What it measures |
|--------|-----------------|
| **Guidelines created per week** | Is the PM actively using the tool? |
| **% of responses modified at runtime** | Is the adherence engine doing useful work? Should decrease over time as the underlying agent improves. |
| **Avg enforcement latency** | Is the tiered approach keeping latency acceptable? Target: < 500ms p95 for Tier 1+2, < 3s p95 for Tier 3. |
| **PM satisfaction (qualitative)** | Does the PM feel like response quality is improving? |
| **Rewrite acceptance rate** | When the PM reviews enforced rewrites, do they agree with the changes? |

---

## 8. Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Adherence engine rewrites introduce hallucinations or drop facts | Users get worse answers than the original draft | Fail-open by default. Store both versions. PM reviews enforcement logs. Confidence threshold controls aggression. |
| Latency exceeds acceptable chat thresholds | Poor user experience | Tiered architecture. Tier 1+2 handle most responses under 500ms. Configurable timeout with fail-open. |
| PM creates conflicting guidelines | Unpredictable enforcement behavior | Priority system on guidelines. Preview feature shows conflicts before activation. |
| LLM cost scales linearly with response volume | Expensive at 10K+ responses/day | Tier 1 (deterministic) handles simple rules at zero LLM cost. Tier 2 uses a fast/cheap model. Tier 3 only fires selectively. |
| Over-reliance on rewriting masks root-cause agent issues | Same bad drafts keep getting rewritten instead of fixed | Enforcement logs surface "top 10 most-triggered guidelines" so the team can see which agent behaviors need fixing at the source. |

---

## 9. Open Questions for Client Discussion

1. **Streaming:** Does the current agent system stream responses token-by-token, or return complete responses? If streaming, v1 may need to buffer the full response before enforcing — adding perceived latency.
2. **Topics/categories:** Does the agent system already classify questions by topic? If so, we can use those categories for guideline scoping. If not, do we need to build topic classification?
3. **Volume confirmation:** Roughly how many responses per day should we design for in the initial deployment?
4. **Hosting:** Does the client have a preferred deployment target? (AWS, GCP, on-prem Docker, etc.)
