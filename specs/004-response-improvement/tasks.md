# Tasks: Response Improvement (Capture)

**Input**: Design documents from `specs/004-response-improvement/`
**Branch**: `004-response-improvement`
**Stack**: Python 3.11 / FastAPI / SQLAlchemy 2.0 / Alembic (backend) · Tauri v2 + React 18 + TypeScript + Tailwind (desktop)

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: Maps to user story (US1 = Capture, US2 = Review list, US3 = Edit/Delete)
- The captured entity is **ResponseFeedback** — PM feedback on an agent answer. It references the source `QAPair` by ID for provenance only; it is not owned by the QAPair.

---

## Phase 1: Setup — Governance-context framing

- [X] T001 Update `CLAUDE.md`: "Active bounded context" section naming **Agent Governance** with its aggregates; `ResponseFeedback` listed alongside `QAPair` / `IngestionRun`
- [X] T002 [P] Update `docs/ARCHITECTURE.md`: single bounded context (Governance) framing
- [X] T003 [P] Add bounded-context note to `specs/001-qa-response-ingestion/data-model.md`
- [X] T004 [P] Scrub stale "ingestion context" docstrings in `src/domain/`

---

## Phase 2: Foundational — ResponseFeedback aggregate + persistence + shared API surface

- [X] T005 [P] `ResponseFeedbackId` value object — `src/domain/model/response_feedback/response_feedback_id.py`
- [X] T006 [P] `TextSpan` value object — `src/domain/model/response_feedback/text_span.py`
- [X] T007 `ResponseFeedback` aggregate — `src/domain/model/response_feedback/response_feedback.py`. Factory accepts optional `span_start` / `span_end` (both-or-neither); stores `span: TextSpan | None`
- [X] T008 `ResponseFeedbackRepository` port — `src/domain/ports/response_feedback_repository.py` (save, find_by_id, list_paginated, delete — no per-QAPair list method)
- [X] T009 `ResponseFeedbackModel` ORM — `src/adapters/secondary/sql/models/response_feedback_model.py`. `span_start` / `span_end` nullable with a CHECK constraint: both null OR both valid
- [X] T010 Alembic migration — `alembic/versions/b2c3d4e5f6a7_create_response_feedback.py`, applied to dev SQLite
- [X] T011 `SqlResponseFeedbackRepository` — `src/adapters/secondary/sql/sql_response_feedback_repository.py`
- [X] T012 [P] Frontend types — `ResponseFeedback`, `ResponseFeedbackPage`, `SubmitResponseFeedbackInput` in `desktop/src/types/index.ts`
- [X] T013 [P] API client — `submitResponseFeedback` in `desktop/src/lib/api.ts` (list/get/update/delete added in later phases)

---

## Phase 3: User Story 1 — Capture Feedback (P1) 🎯 MVP

**Goal**: A PM can select text (or use the whole response) on the QA detail view, click **Improve**, enter problem + desired behavior, and save. The feedback is persisted as a standalone `ResponseFeedback` record with a reference back to the source QAPair.

**Independent Test**: From the Data screen, open a record, (optionally) select a passage, click an Improve button, fill both fields, save. Within 30 seconds the feedback exists in storage (verifiable via `POST /v1/response-feedback` round-trip / toast confirmation).

### Backend

- [X] T014 [P] [US1] `SubmitResponseFeedbackCommand` — `src/application/commands/submit_response_feedback_command.py`
- [X] T015 [P] [US1] `ResponseFeedbackResponse` DTO — `src/application/ports/primary/_response_feedback_response.py`
- [X] T016 [P] [US1] `SubmitResponseFeedbackPort` — `src/application/ports/primary/submit_response_feedback_port.py`
- [X] T017 [US1] `SubmitResponseFeedbackUseCase` — `src/application/use_cases/submit_response_feedback_use_case.py`
- [X] T018 [US1] `response_feedback_router.py` — `POST /v1/response-feedback` in `src/adapters/primary/web/`; registered in `main.py`
- [X] T019 [US1] DI wiring — `sql_response_feedback_repository()` + `submit_response_feedback_use_case()` in `di_container.py`; dependency override in `main.py`

### Frontend

- [X] T020 [P] [US1] `ImprovementFormModal` — `desktop/src/components/ImprovementFormModal.tsx`
- [X] T021 [US1] Extend `desktop/src/components/QAPairDetail.tsx`: selectable answer text, floating/fixed **Improve selected** button that opens the modal with the selection, **Improve whole response** button that opens the modal with `span_start/span_end = null` and the whole answer as excerpt. On save, submit to the backend via the API client and show a confirmation toast. No sidebar of feedback-for-this-QAPair (feedback is not owned by the QAPair)

**Checkpoint**: US1 complete. A PM can submit feedback on any agent answer.

---

## Phase 4: User Story 2 — Review All Response Feedback (P2)

**Goal**: A dedicated Response Feedback screen lists every captured feedback record across the product with pagination and full-text search. Each entry links back to its source QAPair for provenance.

**Independent Test**: With 100+ feedback records in the DB, a PM can open the screen and find a specific one via search in under 10 seconds.

### Backend

- [X] T022 [P] [US2] `ListResponseFeedbackQuery` — `src/application/queries/list_response_feedback_query.py`
- [X] T023 [P] [US2] `ListResponseFeedbackPort` — `src/application/ports/primary/list_response_feedback_port.py`; response type `ListResponseFeedbackResponse(total, page, page_size, items)`
- [X] T024 [US2] `ListResponseFeedbackUseCase` — `src/application/use_cases/list_response_feedback_use_case.py`
- [X] T025 [US2] Extend `response_feedback_router.py`: `GET /v1/response-feedback` (query params `page`, `page_size`, `search`); response body `ListResponseFeedbackResponseBody`
- [X] T026 [US2] DI wiring — `list_response_feedback_use_case()` factory + dependency override

### Frontend

- [X] T027 [P] [US2] `ResponseFeedbackList` component — `desktop/src/components/ResponseFeedbackList.tsx`
- [X] T028 [US2] `ResponseFeedbackScreen` — `desktop/src/screens/ResponseFeedbackScreen.tsx` (header + debounced search, two-column layout, source-record link via route state)
- [X] T029 [US2] `/response-feedback` route in `desktop/src/App.tsx`; sidebar entry in `AppShell.tsx`; `DataScreen` honors incoming `openQAPairId` route state
- [X] T030 [US2] `listResponseFeedback(params)` in `desktop/src/lib/api.ts` (get-by-id deferred to US3)

**Checkpoint**: US2 complete. All feedback records are browsable, searchable, and linkable to source.

---

## Phase 5: User Story 3 — Edit or Remove Feedback (P3)

**Goal**: A PM can edit the text of a feedback record or delete it entirely.

**Independent Test**: A PM finds a feedback record, edits the desired-behavior text, saves, and sees the update in the list detail view. Separately, deleting the record removes it from the list.

### Backend

- [X] T031 [P] [US3] `UpdateResponseFeedbackCommand` / `DeleteResponseFeedbackCommand`
- [X] T032 [P] [US3] `GetResponseFeedbackPort` (with `ResponseFeedbackNotFoundError`), `UpdateResponseFeedbackPort`, `DeleteResponseFeedbackPort`
- [X] T033 [US3] Get/Update/Delete use cases
- [X] T034 [US3] Router: `GET /{id}`, `PATCH /{id}`, `DELETE /{id}`
- [X] T035 [US3] DI wiring for the three use cases

### Frontend

- [X] T036 [US3] `ImprovementFormModal` already supports `mode: "edit"` from US1 (title + button swap)
- [X] T037 [US3] `getResponseFeedback`, `updateResponseFeedback`, `deleteResponseFeedback` in `desktop/src/lib/api.ts`
- [X] T038 [US3] Edit/Delete actions on `ResponseFeedbackScreen` detail view, with confirmation dialog for delete, React Query invalidation on success

---

## Phase 6: Polish & Cross-Cutting Concerns

### Backend tests

- [X] T039 [P] `tests/unit/domain/test_response_feedback.py`
- [X] T040 [P] `tests/unit/domain/test_text_span.py`
- [X] T041 [P] `tests/unit/application/test_submit_response_feedback_use_case.py`
- [X] T042 [P] `tests/unit/application/test_list_response_feedback_use_case.py`
- [X] T043 [P] `tests/unit/application/test_update_response_feedback_use_case.py`
- [X] T044 [P] `tests/unit/application/test_delete_response_feedback_use_case.py`
- [X] T045 [P] `tests/integration/test_sql_response_feedback_repository.py`

### Frontend tests

- [X] T046 [P] `desktop/src/components/__tests__/ImprovementFormModal.test.tsx`

### Verification & build

- [X] T047 `PYTHONPATH=. python -m pytest tests/ -q` passes (124 tests)
- [X] T048 `cd desktop && npm test` passes (14 tests)
- [X] T049 End-to-end API test against live Docker stack (POST/GET/PATCH/DELETE all pass; DELETE idempotent); desktop-UI E2E still to be run by the user manually
- [X] T050 `docker compose up -d --build api` — container healthy, `alembic current` reports `b2c3d4e5f6a7 (head)`

### User-facing documentation

- [X] T051 [P] Updated `website/docs/intro.md`
- [X] T052 [P] Created `website/docs/governance/response-feedback.md`
- [X] T053 [P] Updated `website/docs/reference/api.md`
- [X] T054 [US2] Updated `website/docs/desktop/index.md`
- [X] T055 [P] Updated `website/sidebars.ts`
- [X] T056 `cd website && npm run build` passes

---

## Dependencies

- Phase 1 → Phase 2 → each of US1/US2/US3 in parallel (frontend of US3 reuses `ImprovementFormModal` from US1, so US3 frontend waits on US1 frontend)
- Polish after all user stories ship

---

## Notes

- **Ownership model**: `ResponseFeedback` is an independent aggregate. It references `QAPair` by ID for provenance only. We deliberately do **not** expose a `GET /v1/qa-pairs/{id}/feedback` endpoint and do **not** render feedback-for-this-QAPair inside `QAPairDetail`. The QAPair is the *source*, not the *container*.
- **Future direction** (post-this-feature): what we do with `ResponseFeedback` — synthesize reusable guidelines, run enforcement, train retrieval, etc. — is explicitly out of scope. This feature captures the raw PM input.
- `QAPair` is **not** renamed in this feature. `/v1/ingest/*` URL paths are **not** renamed (external contract).
