# Research: Response Improvement (Capture)

**Feature**: 004-response-improvement
**Date**: 2026-04-23

---

## Decision 1: One bounded context — **Agent Governance**

**Decision**: The entire AnswerGuard domain is a single bounded context called **Agent Governance** (or **Governance** for short). Every aggregate that exists today (`QAPair`, `IngestionRun`, `SourceConnector`) and every aggregate this feature adds (`Guideline`) lives inside it.

Previously the codebase and spec language treated "Ingestion" as a bounded context in its own right. That was wrong: ingestion is a *mechanism* (bringing conversations into the system), not a *domain*. It exists only because Governance needs conversations to reason about. Similarly, the feature's earlier framing of "Guideline as a new bounded context" was also wrong — guidelines are one more aggregate in the Governance context, not a sphere of their own.

The purpose of this single context is to **guard against bad agent responses reaching users** — capturing them, reviewing them, writing rules about them, and (in feature 005) enforcing those rules.

**Aggregates in the Governance context:**

| Aggregate | Role |
|---|---|
| `QAPair` | An observed agent↔user exchange being governed |
| `IngestionRun` | Bookkeeping of an import operation — supporting entity, not central |
| `SourceConnector`, `FieldMapping` | Configuration value objects for external data sources |
| `Guideline` (this feature) | A rule the PM wants the agent to follow |
| (future) `GuidelineViolation`, `EnforcementAction` | Records of applying guidelines at runtime |

**Aggregate-to-aggregate reference rules (unchanged):** `Guideline` references `QAPair` by ID only, no FK, no cascade. This is standard aggregate-boundary discipline *within* a single context, not a cross-context reference. Deleting a `QAPair` leaves its guidelines intact (FR-013).

**Cleanup work this decision creates** (tracked explicitly in this feature's task list):
1. Update `CLAUDE.md` project instructions to name "Agent Governance" as the sole bounded context
2. Update `docs/ARCHITECTURE.md` similarly
3. Scrub docstrings and comments across `src/` that describe an "ingestion context" or "qa_pair context" — reword as "Governance context"
4. **No directory reorganization.** `src/domain/model/qa_pair/`, `src/domain/model/ingestion_run/`, and the new `src/domain/model/guideline/` are all aggregate-level subdirectories *within the same context*. Aggregate-per-directory is valid; context-per-directory would only be justified if there were more than one context
5. **No URL rename.** The `/v1/ingest/*` paths are external contracts — "ingest" is a verb describing the operation, not a context label. Changing these would break every SDK and doc already shipped

**Alternatives rejected**: Multiple bounded contexts (Ingestion / Review / Adherence) — rejected because the product solves one cohesive problem (governing agent behavior) and splitting it at today's scale would be over-modeling. If AnswerGuard later grows features that genuinely belong to a different language (e.g. billing, or a separate team-collaboration domain), we can split then. Today we have one product, one domain.

---

## Decision 2: Span storage as character offsets

**Decision**: Store `span_start: int` and `span_end: int` as character offsets into the `answer_text` of the source Q&A pair at the time of capture. Also store the `excerpt: str` (the literal highlighted text) so guidelines remain readable even if the underlying response text ever changes.

**Rationale**:
- Character offsets are the simplest, least ambiguous representation
- Storing the excerpt decouples the guideline from the live state of the source text — if the source is later deleted or edited, the guideline is still self-contained and displayable
- Works for the "select nothing = whole response" case: `span_start=0`, `span_end=len(answer_text)`, `excerpt=answer_text`

**Alternatives rejected**: Storing structured anchors (e.g. "3rd sentence"), XPath-style selectors — overkill for plain-text content.

---

## Decision 3: Overlapping highlight rendering

**Decision**: When rendering the record detail view, compute a single flat set of "highlighted character ranges" by union-ing all guideline spans for that Q&A pair. Every highlighted character gets the same visual treatment (background colour). Clicking anywhere inside a highlighted region scrolls the guidelines sidebar to the guidelines that cover that range.

**Rationale**:
- Simple to implement and reason about
- Avoids the visual complexity of overlapping coloured regions
- The sidebar list is the source of truth for "which guidelines apply to which text" — the highlight is a visual cue, not a per-guideline marker

**Alternatives considered**: Stacked coloured highlights per guideline (rejected as visually noisy), numbered pin markers (rejected as too busy for long responses).

---

## Decision 4: Free-text fields, no structured taxonomy

**Decision**: Store `problem` and `desired_behavior` as free-text strings. No enum of issue types, no severity level.

**Rationale**: The spec's "Out of Scope" section explicitly defers structured taxonomy. Two unconstrained text fields give PMs maximum expressiveness with zero training overhead. If we need structure later (e.g. for enforcement engine routing), we can derive it via LLM classification of the captured text rather than asking PMs to self-categorise.

---

## Decision 5: Persistence — shared database, new table

**Decision**: `guidelines` is a new table in the same AnswerGuard database that holds `qa_pairs`. Alembic migration adds the table. Same SQLite/PostgreSQL dual support via SQLAlchemy as existing features.

**Rationale**:
- Transactional consistency with related reads (e.g. loading a Q&A pair and its guidelines in one request)
- No new infrastructure
- Matches the architecture of features 001 and 003

---

## Decision 6: Desktop app integration point

**Decision**: Extend the existing Data view's detail panel (`QAPairDetail.tsx`) to support text selection, the **Improve** action, and inline guideline highlighting. Add a new top-level `GuidelinesScreen` with its own sidebar entry.

**Rationale**: The Data view is where PMs already browse records — the feature's natural home. A separate Guidelines screen mirrors the structure we already have (Source Setup, Import, Data → add Guidelines).

---

## Decision 7: Text selection and highlight rendering approach

**Decision**: Use the browser's native `Selection` API (`window.getSelection()`) in the `QAPairDetail` component to detect user selections on the answer text. Render highlights by splitting the answer text into an array of segments at every highlight boundary and wrapping highlighted segments in a styled `<mark>` element.

**Rationale**:
- `Selection` API is standard and works natively in Tauri's WebKit/WebView2
- Splitting-and-wrapping is the simplest rendering approach; performs fine for responses well over 10KB
- No external libraries required

---

## Decision 8: "Improve" button UX

**Decision**: When the user selects text within the answer, a floating **Improve** button appears near the selection. When no selection is active, a persistent "Improve this response" button is shown above or below the answer text, which creates a guideline scoped to the whole response. Either path opens the same modal form.

**Rationale**: Matches the two user paths described in the spec (FR-002, FR-003). The modal form keeps the data view readable behind it.
