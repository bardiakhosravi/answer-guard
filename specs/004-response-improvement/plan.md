# Implementation Plan: Response Improvement (Capture)

**Branch**: `004-response-improvement` | **Date**: 2026-04-23 | **Spec**: [spec.md](./spec.md)

---

## Summary

Add the `Guideline` aggregate and the UI flow for capturing guidelines by selecting text in an agent response. Extends the existing desktop app's Data view with text selection, an "Improve" action, an Improvement Form modal, inline guideline highlighting, and a per-record guidelines sidebar. Adds a new top-level "Guidelines" screen for browsing, editing, and deleting all captured guidelines. Adds 6 new REST endpoints to the AnswerGuard backend, all following the established hexagonal architecture.

This feature also consolidates the bounded-context model: everything in AnswerGuard is now explicitly one context, **Agent Governance**. Previously the codebase implied separate Ingestion and (forthcoming) Review/Adherence contexts. That was over-modeling — ingestion is a mechanism, not a domain. Renaming and cleanup work is included here so the new `Guideline` aggregate lands in the right place.

Enforcement (applying guidelines to future responses) is explicitly out of scope — see the spec's "Out of Scope" section and SC-004 which validates that captured data is sufficient for a future enforcement engine.

---

## Technical Context

**Backend**: Python 3.11, FastAPI, SQLAlchemy 2.0 (sync), Alembic — same stack as features 001/003
**Frontend**: Tauri v2, React 18 + TypeScript, React Router v6, React Query, Tailwind CSS — extends existing desktop app
**Storage**: new `guidelines` table in the shared AnswerGuard database (PostgreSQL in production, SQLite for local dev)
**Text selection**: browser native `Selection` API — works identically in Tauri's WebKit (macOS) and WebView2 (Windows)
**No new runtime dependencies**

---

## Constitution Check

| Principle | Status | Notes |
|---|---|---|
| Domain layer independence | PASS | `Guideline`, `GuidelineId`, `TextSpan` have zero external deps |
| Ports define external boundaries | PASS | `GuidelineRepository` in domain, 6 primary ports in application |
| Use cases contain no business logic | PASS | Each use case orchestrates only; business rules (invariants, span validation) live in `Guideline.create()` and `TextSpan` |
| Aggregates own their mutations | PASS | `Guideline.update()` is the only mutation path; repository only saves/deletes |
| Single bounded context (Governance) | PASS | `Guideline` is a new aggregate **within** the existing Governance context, alongside `QAPair` and `IngestionRun`. No new context created. See research.md Decision 1. |
| Cross-aggregate references by ID | PASS | `Guideline.qa_pair_id` is a plain UUID. No FK, no cascade — required by FR-013 |
| API must not leak persistence models | PASS | Pydantic DTOs in router; SQLAlchemy model stays in `adapters/secondary/sql/` |

---

## Project Structure

### Backend additions (`src/`)

```
src/
├── domain/
│   ├── model/
│   │   └── guideline/
│   │       ├── guideline.py               # Aggregate root
│   │       ├── guideline_id.py            # Value object
│   │       └── text_span.py               # Value object with invariants
│   └── ports/
│       └── guideline_repository.py        # Abstract port
├── application/
│   ├── ports/primary/
│   │   ├── create_guideline_port.py
│   │   ├── list_guidelines_port.py
│   │   ├── get_guideline_port.py          # Includes GuidelineNotFoundError
│   │   ├── get_guidelines_for_qa_pair_port.py
│   │   ├── update_guideline_port.py
│   │   └── delete_guideline_port.py
│   ├── commands/
│   │   ├── create_guideline_command.py
│   │   ├── update_guideline_command.py
│   │   └── delete_guideline_command.py
│   ├── queries/
│   │   └── list_guidelines_query.py
│   └── use_cases/
│       ├── create_guideline_use_case.py
│       ├── list_guidelines_use_case.py
│       ├── get_guideline_use_case.py
│       ├── get_guidelines_for_qa_pair_use_case.py
│       ├── update_guideline_use_case.py
│       └── delete_guideline_use_case.py
├── adapters/
│   ├── primary/
│   │   └── web/
│   │       └── guidelines_router.py       # All endpoints including the QA-pair-scoped list
│   └── secondary/
│       └── sql/
│           ├── models/
│           │   └── guideline_model.py
│           └── sql_guideline_repository.py
└── configuration/
    └── di_container.py                    # Wire 6 new use cases
```

Plus a new Alembic migration creating the `guidelines` table with indexes on `qa_pair_id` and `created_at`.

### Frontend additions (`desktop/src/`)

```
desktop/src/
├── types/index.ts                         # Add Guideline + related interfaces
├── lib/
│   └── api.ts                             # createGuideline, listGuidelines, getGuidelinesForQAPair, updateGuideline, deleteGuideline
├── components/
│   ├── QAPairDetail.tsx                   # EXTEND: selection, Improve button, highlight overlay, guidelines sidebar section
│   ├── ImprovementFormModal.tsx           # NEW: create + edit form
│   ├── HighlightedAnswer.tsx              # NEW: renders answer text with highlight overlays
│   └── GuidelineList.tsx                  # NEW: used by the Guidelines screen
├── screens/
│   └── GuidelinesScreen.tsx               # NEW: top-level screen
└── App.tsx                                # EXTEND: add /guidelines route
```

AppShell gains a new sidebar entry "Guidelines".

---

## Governance Context Cleanup (In Scope)

Before adding the `Guideline` aggregate, we straighten out the bounded-context framing in the existing codebase. The goal is to make it obvious — to any future reader — that AnswerGuard has one bounded context (Agent Governance), not two or three.

What gets updated, concretely:

| Target | Change |
|---|---|
| `CLAUDE.md` (project instructions) | Replace "Active Technologies / ingestion" language with an "Active bounded context: Agent Governance" note; list the aggregates inside it |
| `docs/ARCHITECTURE.md` | Remove any language framing Ingestion as a separate domain; restate the architecture as one context with several aggregates |
| `specs/001-qa-response-ingestion/data-model.md` | Add a note that the `QAPair` and `IngestionRun` aggregates documented there are part of the Governance context |
| Existing docstrings in `src/domain/` | Any comment or docstring that references an "ingestion context" or implies a separate domain → rephrase as "Governance context" |
| New aggregate directory | `src/domain/model/guideline/` is added as a peer of `qa_pair/` and `ingestion_run/` — aggregate-per-directory, same context |

What does **not** change:

- No class renames (e.g. `QAPair`, `IngestionRun`, `IngestionMethod`) — those are still correct names for the things they describe. `QAPair` is flagged as naming debt (storage-shaped rather than domain-shaped, e.g. `Conversation` or `Interaction` would read better) but renaming it is a large refactor touching ~60 files with no functional benefit; defer until there's another reason to touch that code
- No URL changes to `/v1/ingest/*` — these are external contracts; renaming would break SDKs and published docs
- No directory reorganization of existing aggregates

## Key Implementation Notes

### Creating a guideline from a selection
In `QAPairDetail`, after any `mouseup`/`keyup` in the answer text, read `window.getSelection()` to derive (a) the highlighted excerpt and (b) the character offsets within the raw `answerText`. Because the answer renders as multiple segments (for existing highlights), compute the offset by walking the rendered segments and summing the text-node lengths before the selection boundary. If no selection exists, the "Improve whole response" button supplies `start=0`, `end=answerText.length`.

### Rendering highlights over already-highlighted text
Compute a single flat list of `[start, end]` intervals by union-ing all guideline spans for the record, then merge overlapping intervals. Split the `answerText` into segments at every interval boundary, and wrap highlighted segments in a `<mark>` with a consistent Tailwind class. Clicking a highlighted region scrolls the sidebar to the list of guidelines that cover the clicked offset.

### `PATCH` endpoint partial update
The Pydantic model accepts `Optional[str]` for both fields, and the use case raises `DomainException` if both are omitted. If only one is supplied, the other is preserved from the stored record.

### DELETE idempotency
`DELETE /v1/guidelines/{id}` returns 204 even when the record doesn't exist. The repository's `delete()` returns a boolean indicating "did we actually delete something," but the HTTP layer discards it for the idempotent contract.

### Spec FR-013: guidelines survive QAPair deletion
Enforced by (a) the absence of a foreign key on `qa_pair_id` and (b) the frontend checking whether the source record still exists when rendering the "View source record" link on the Guidelines screen. The desktop app attempts to load the source record by ID on demand; if the request returns 404 or empty, the link becomes a disabled "Source record no longer available" label.

---

## Verification

1. **Backend unit tests**: `Guideline.create()` invariants, `TextSpan` validation, each of the 6 use cases with mocked repository
2. **Backend integration tests**: `SqlGuidelineRepository` round-trips on SQLite; list pagination + search; delete behaviour
3. **Manual end-to-end test**:
   - Open a record with a long answer in the desktop app
   - Select a sentence, click **Improve**, fill in problem + desired behaviour, save
   - Confirm the highlight appears, the sidebar lists the guideline, and the guideline appears on the Guidelines screen
   - Edit the guideline via the sidebar — confirm the change propagates to the Guidelines screen
   - Delete the guideline — confirm it disappears from both views and the highlight is removed
   - Reload the app — confirm everything persisted

### Success criteria mapping

| Criterion | Where it's verified |
|---|---|
| SC-001 (create in 30s) | Observed during manual test |
| SC-002 (find in 10s) | Tested on a seeded list of 100+ guidelines |
| SC-003 (persistence) | Reload test |
| SC-004 (enforcement-ready data) | Schema review — the stored fields cover excerpt + span + source ID + problem + desired behaviour, which is everything a critique pass would need |
| SC-005 (no silent failures) | Tested by killing the backend mid-save and observing the error surface in the modal |
