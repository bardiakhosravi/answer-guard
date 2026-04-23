# Tasks: Desktop App — Integration Setup

**Input**: Design documents from `specs/003-desktop-integration-setup/`
**Branch**: `003-desktop-integration-setup`
**Stack**: Tauri v2 + React 18 + TypeScript + Tailwind CSS · Python 3.11 / FastAPI / SQLAlchemy (backend additions)

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: Maps to user story (US1 = Source Setup, US2 = Import, US3 = Data View)
- Exact file paths included in every task

---

## Phase 1: Setup

**Purpose**: Scaffold the Tauri desktop app and prepare backend for new endpoints.

- [X] T001 Initialize Tauri v2 project: run `npm create tauri-app@latest desktop -- --template react-ts`; accept defaults; confirm `desktop/` directory created with `src-tauri/` (Rust) and `src/` (React/TS)
- [X] T002 [P] Install frontend dependencies in `desktop/`: `react-router-dom@6`, `@tanstack/react-query`, `react-hook-form`, `@tauri-apps/plugin-store`, `@tauri-apps/plugin-dialog`
- [X] T003 [P] Install and configure Tailwind CSS in `desktop/`: `npm install -D tailwindcss postcss autoprefixer`, run `npx tailwindcss init -p`, configure `tailwind.config.js` content paths for `src/**/*.{ts,tsx}`, add `@tailwind` directives to `src/index.css`
- [X] T004 [P] Configure Tauri app metadata in `desktop/src-tauri/tauri.conf.json`: set `productName: "AnswerGuard"`, `identifier: "com.answerguard.desktop"`, default window size `1200x800`, min size `900x600`
- [X] T005 [P] Register Tauri plugins in `desktop/src-tauri/src/main.rs` and `Cargo.toml`: add `tauri-plugin-store` and `tauri-plugin-dialog` plugins
- [X] T006 Add `desktop/node_modules/`, `desktop/dist/`, `desktop/src-tauri/target/`, `desktop/src-tauri/gen/` to `/.gitignore`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared frontend infrastructure (API client, config store, router shell, types) and backend repository extension. All three user stories depend on these.

**⚠️ CRITICAL**: No user story work can start until this phase is complete.

### Frontend foundations

- [X] T007 Create TypeScript type definitions in `desktop/src/types/index.ts`: interfaces for `ServerConfig`, `SourceConnectorConfig`, `FieldMapping`, `DiscoveredColumn`, `ImportJob`, `QAPairRecord` matching `specs/003-desktop-integration-setup/data-model.md` exactly
- [X] T008 [P] Create API client in `desktop/src/lib/api.ts`: `fetch`-based wrapper with functions `checkHealth(url)`, `discoverSchema(config)`, `triggerImport(config)`, `getImportStatus(runId)`, `getOverallStatus()`, `listQAPairs(params)`; all functions read the configured server URL from the store; throw typed errors for 4xx/5xx
- [X] T009 [P] Create store wrapper in `desktop/src/lib/store.ts`: functions `getServerConfig()`, `setServerConfig()`, `getSourceConnectorConfig()`, `setSourceConnectorConfig()`, `getLastImportRunId()`, `setLastImportRunId()`; uses `@tauri-apps/plugin-store` with file `config.json`
- [X] T010 Create `desktop/src/App.tsx`: React Router setup with routes matching `specs/003-desktop-integration-setup/contracts/ui-screens.md` navigation rules; wrap with `QueryClientProvider`; redirect to `/connect` on first load if no server config
- [X] T011 [P] Create `desktop/src/components/AppShell.tsx`: persistent layout with header (logo, connection status dot, configured URL), left sidebar (Source Setup, Import, Data — with enabled/disabled states per navigation rules), main content area via `<Outlet />`

### Backend foundations

- [X] T012 Extend `QAPairRepository` port in `src/domain/ports/qa_pair_repository.py`: add abstract method `list_paginated(page: int, page_size: int, source_system_id: str | None, search: str | None) -> tuple[list[QAPair], int]` returning `(items, total_count)`
- [X] T013 Implement `list_paginated()` in `src/adapters/secondary/sql/sql_qa_pair_repository.py`: SQL query with optional `source_system_id` filter and optional `ILIKE` (Postgres) / `LIKE` (SQLite) search on `question_text` OR `answer_text`; return `(items, total_count)` using separate count query; order by `captured_at DESC`

**Checkpoint**: Desktop app starts with routing, can call API (even stubbed), config persists across restarts. Backend has pagination support on the repository. All user story work can now begin.

---

## Phase 3: User Story 1 — Source Connector Setup (Priority: P1) 🎯 MVP

**Goal**: A developer can connect the desktop app to their AnswerGuard instance, configure BigQuery connection details, discover the table schema, and map source columns to AnswerGuard fields.

**Independent Test**: From a fresh install, open the app → enter server URL → configure BigQuery details → see discovered columns appear → select required mappings → save — all within 15 minutes, no docs required.

### Backend: Schema discovery endpoint

- [X] T014 [P] [US1] Create `DiscoverSchemaCommand` in `src/application/commands/discover_schema_command.py`: dataclass with `gcp_project_id: str`, `dataset_id: str`, `table_id: str`, `credentials_path: str | None`
- [X] T015 [P] [US1] Create `DiscoverSchemaPort` in `src/application/ports/primary/discover_schema_port.py`: abstract `execute(command) -> DiscoverSchemaResponse`; define `DiscoveredColumn` (name, type) and `DiscoverSchemaResponse` (columns: list) dataclasses
- [X] T016 [US1] Create `DiscoverSchemaUseCase` in `src/application/use_cases/discover_schema_use_case.py`: builds a minimal `SourceConnector` value object (with a placeholder `FieldMapping` to satisfy its invariants), calls `BigQuerySourcePort.get_schema()`, returns column names and types (schema from BigQuery includes type info — extend `BigQuerySourceAdapter.get_schema()` if needed to return tuples or typed objects instead of just names)
- [X] T017 [US1] Update `BigQuerySourceAdapter.get_schema()` in `src/adapters/secondary/bigquery/bigquery_source_adapter.py`: return `list[dict]` with `{name, type}` per field (was `list[str]`); update `BigQuerySourcePort` abstract method signature to match; update `ImportHistoricalDataUseCase` to extract `.name` from the dicts during field mapping validation
- [X] T018 [US1] Create `sources_router.py` in `src/adapters/primary/web/`: FastAPI `APIRouter` with `POST /v1/sources/discover-schema`; Pydantic request/response models; map `AdapterException` → 502, `DomainException` → 400; register in `main.py`
- [X] T019 [US1] Wire US1 in `src/configuration/di_container.py`: add `discover_schema_use_case()` factory method using `BigQuerySourceAdapter`

### Frontend: Source setup screens

- [X] T020 [P] [US1] Create `desktop/src/screens/ConnectScreen.tsx`: form with "Server URL" input + "Connect" button; on submit → `api.checkHealth(url)`; on 200 → persist via `store.setServerConfig()` and navigate to `/connector/details`; on failure → inline error
- [X] T021 [P] [US1] Create `desktop/src/screens/connector/DetailsScreen.tsx`: React Hook Form with Source System ID, GCP Project ID, Dataset ID, Table ID, Credentials file (with Browse button that calls `@tauri-apps/plugin-dialog` open dialog filtered to `.json`), Row filter, Page size; step indicator "Step 1 of 3"; on submit → store partial config, navigate to `/connector/schema`
- [X] T022 [US1] Create `desktop/src/screens/connector/SchemaScreen.tsx`: on mount → call `api.discoverSchema()` with stored details; show loading state; on success render `<FieldMappingForm>` passing discovered columns; step indicator "Step 2 of 3"; on error (502 from BQ) → show error card with "Back to Details" button
- [X] T023 [P] [US1] Create `desktop/src/components/FieldMappingForm.tsx`: two-column layout — left panel lists discovered columns with name + type badge; right panel has required dropdowns (Question column, Answer column) and optional dropdowns (Timestamp, External ID); repeatable metadata key-column pairs with "+ Add metadata field" button; "Review Mapping →" button disabled until both required dropdowns are selected; on submit → update stored config with field_mapping, navigate to `/connector/review`
- [X] T024 [P] [US1] Create `desktop/src/screens/connector/ReviewScreen.tsx`: read-only display of all configured values grouped by section (Connection, Field Mapping, Metadata); "Save Configuration" primary button → persists full config and navigates to `/import`; "Edit" links on each section to jump back
- [X] T025 [US1] Wire routes in `desktop/src/App.tsx`: `/connect`, `/connector/details`, `/connector/schema`, `/connector/review` with guards (redirect to `/connect` if no server config; redirect to `/connector/details` if trying to access `/schema` without stored details)

### Tests

- [X] T026 [P] [US1] Unit test `DiscoverSchemaUseCase` in `tests/unit/application/test_discover_schema_use_case.py`: mock `BigQuerySourcePort`; test successful schema return; test `AdapterException` propagates
- [X] T027 [P] [US1] Update affected tests for `get_schema()` return type change: `tests/unit/application/test_import_historical_data_use_case.py` — fix mock returns from `["col1"]` to `[{"name": "col1", "type": "STRING"}]`

**Checkpoint**: US1 complete. Developer can complete full source setup wizard end-to-end in the desktop app.

---

## Phase 4: User Story 2 — Import & Live Progress (Priority: P2)

**Goal**: A developer can trigger the historical import from the desktop app and watch live progress until completion.

**Independent Test**: With a saved source configuration, click "Start Import" → see progress updates every ~3 seconds → see completion summary with record counts — all in the app, no curl.

### Frontend: Import screen

- [X] T028 [US2] Create `desktop/src/components/ProgressCard.tsx`: displays status badge (RUNNING/COMPLETED/FAILED/RESUMED with appropriate colours), records processed (large number), records skipped, elapsed time (live ticker), last checkpoint; shows optional progress bar if total row count is known
- [X] T029 [US2] Create `desktop/src/screens/ImportScreen.tsx`: reads source config from store; State A (no active run) → shows source summary + "Start Import" button; on click → `api.triggerImport()`, store `runId`, transition to State B; State B (RUNNING/RESUMED) → renders `<ProgressCard>` with React Query `useQuery({ refetchInterval: 3000, enabled: isActive })`; State C (COMPLETED) → shows summary card with "View Ingested Data →" navigating to `/data`; State D (FAILED) → shows error card with "Resume Import" button calling `api.triggerImport()` with same config
- [X] T030 [US2] Wire `/import` route in `desktop/src/App.tsx` with guard (redirect to `/connector/details` if no source config saved); update `AppShell` sidebar to enable "Import" link once source config exists

### Tests

- [X] T031 [P] [US2] Unit test `ProgressCard` component in `desktop/src/components/__tests__/ProgressCard.test.tsx` (if test runner is configured): renders each status with correct badge colour; elapsed time updates on prop change

**Checkpoint**: US2 complete. Developer runs import and sees live progress through to completion without leaving the app.

---

## Phase 5: User Story 3 — Data View (Priority: P3)

**Goal**: A developer can browse all ingested Q&A pairs in a paginated, searchable list with a detail view for each record.

**Independent Test**: After an import, navigate to Data → see list of records → search filters in real time → select a record → detail panel shows full content.

### Backend: QA pairs list endpoint

- [X] T032 [P] [US3] Create `ListQAPairsQuery` in `src/application/queries/list_qa_pairs_query.py`: dataclass with `page: int = 1`, `page_size: int = 50`, `source_system_id: str | None = None`, `search: str | None = None`
- [X] T033 [P] [US3] Create `ListQAPairsPort` in `src/application/ports/primary/list_qa_pairs_port.py`: abstract `execute(query) -> ListQAPairsResponse`; define response with `total`, `page`, `page_size`, `items: list[QAPairSummary]`; define `QAPairSummary` dataclass (id, question_text, answer_text, source_system_id, captured_at, source_timestamp, ingestion_method, external_id, metadata)
- [X] T034 [US3] Create `ListQAPairsUseCase` in `src/application/use_cases/list_qa_pairs_use_case.py`: calls `QAPairRepository.list_paginated()`; maps domain `QAPair` objects to `QAPairSummary` DTOs; returns paginated response
- [X] T035 [US3] Create `qa_pairs_router.py` in `src/adapters/primary/web/`: FastAPI `APIRouter` with `GET /v1/qa-pairs?page=&page_size=&source_system_id=&search=`; Pydantic response model; register in `main.py`
- [X] T036 [US3] Wire US3 in `src/configuration/di_container.py`: add `list_qa_pairs_use_case()` factory method

### Frontend: Data view

- [X] T037 [P] [US3] Create `desktop/src/components/QAPairList.tsx`: paginated list using React Query `useQuery` with `keepPreviousData: true`; each row shows truncated question (max 2 lines), answer preview (1 line), timestamp, source badge; active row highlighted; pagination controls (prev/next/page number); accepts `onSelect(id)` prop
- [X] T038 [P] [US3] Create `desktop/src/components/QAPairDetail.tsx`: detail panel showing full question text, full answer text, source system ID, captured_at, ingestion_method badge, external_id (if present), metadata as key-value pairs; accepts `qaPairId` prop; fetches full record via `api.listQAPairs({ search: id })` or by filtering from the list
- [X] T039 [US3] Create `desktop/src/screens/DataScreen.tsx`: two-column layout — left is `<QAPairList>`, right is `<QAPairDetail>` (or empty state if none selected); top bar has stats (total records, runtime captures last 24h), search input (debounced 300ms, updates query), source filter dropdown; "Skipped Records" tab showing error log from most recent import via `api.getImportStatus(lastRunId)`
- [X] T040 [US3] Wire `/data` route in `desktop/src/App.tsx` with guard (redirect to `/import` if no `lastImportRunId` stored); update `AppShell` sidebar to enable "Data" link once at least one import has completed

### Tests

- [X] T041 [P] [US3] Unit test `ListQAPairsUseCase` in `tests/unit/application/test_list_qa_pairs_use_case.py`: mock `QAPairRepository.list_paginated()`; test pagination math (page 2 → offset calculation); test with/without filters
- [X] T042 [P] [US3] Integration test `list_paginated()` in `tests/integration/test_sql_qa_pair_repository.py`: seed 25 records, test page=1 size=10 returns 10 items total=25; test source filter; test search filter (case-insensitive)

**Checkpoint**: US3 complete. All three user stories deliver the full spec end-to-end.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [X] T043 Run full backend test suite: `cd /Users/bardiakhosravi/Projects/answer-gaurd && PYTHONPATH=. python -m pytest tests/ -v` — confirm all tests pass including updated import use case tests
- [X] T044 [P] Build desktop app for macOS: `cd desktop && npm run tauri build` — confirm `.dmg` produced in `src-tauri/target/release/bundle/dmg/`
- [ ] T045 [P] Build desktop app for Windows: on a Windows machine or via GitHub Actions, `npm run tauri build` — confirm `.msi` or `.exe` produced
- [X] T046 [P] Add GitHub Actions workflow in `/.github/workflows/desktop-build.yml`: trigger on push to `main` when `desktop/**` changes; matrix over `macos-latest` and `windows-latest`; builds artifacts and uploads as release assets
- [X] T047 [P] Update `website/docs/` with a new page `desktop/index.md`: brief overview of the desktop app, installation instructions (download from GitHub Releases), screenshots of the five screens; add to Docusaurus sidebar
- [X] T048 Manual end-to-end test: fresh install → server connection → source setup → import 100 test records → data view with search → confirm all 6 success criteria in spec.md pass

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Requires Phase 1 — blocks all user stories
- **US1 (Phase 3)**: Requires Phase 2 — largest phase
- **US2 (Phase 4)**: Requires Phase 2 + US1 source config saved
- **US3 (Phase 5)**: Requires Phase 2 + US2 completed import (for realistic data view testing)
- **Polish (Phase 6)**: Requires all stories complete

### Within Phase 3 (US1)

Backend (T014–T019) and frontend (T020–T025) are largely independent until they need to connect at T022 (SchemaScreen calls the discover-schema endpoint). Developers can split work:

```
Stream A (backend):  T014, T015 [P] → T017 → T016 → T018 → T019
Stream B (frontend): T020, T021, T023, T024 [P] → T022 (needs backend) → T025
```

### Parallel Opportunities

- **Phase 1**: T002, T003, T004, T005 all independent — run in parallel after T001
- **Phase 2**: T008, T009, T011 independent — run together after T007; T012, T013 backend in parallel stream
- **Phase 3 (US1)**: T014 + T015 parallel; T020 + T021 + T023 + T024 parallel; backend and frontend streams in parallel
- **Phase 5 (US3)**: T032 + T033 parallel; T037 + T038 parallel
- **Phase 6**: T044, T045, T046, T047 all independent

---

## Parallel Example: US1 Frontend Stream

```
T020 (ConnectScreen)       ─┐
T021 (DetailsScreen)        ├─[P]─ all in parallel
T023 (FieldMappingForm)     │
T024 (ReviewScreen)         ─┘
                             ↓
T022 (SchemaScreen — depends on backend T018 + component T023)
                             ↓
T025 (Wire routes — depends on all screens)
```

---

## Implementation Strategy

### MVP (User Story 1 only — P1)

1. Complete Phase 1: Setup (T001–T006)
2. Complete Phase 2: Foundational (T007–T013)
3. Complete Phase 3: US1 (T014–T027)
4. **STOP and VALIDATE**: A developer can configure the source connector end-to-end in the desktop app
5. Merge to main — the app has real value even without import/data screens (the config is saved and the existing curl-based import still works)

### Incremental Delivery

1. Setup + Foundational → runnable desktop app shell
2. US1 → full source setup wizard (the hardest part — schema discovery, field mapping) → **demo**
3. US2 → one-click import with live progress → **demo**
4. US3 → browsable data view → **demo**
5. Polish → signed builds for macOS + Windows, GitHub Actions CI, docs update

### Total Task Count

| Phase | Tasks | Parallel Opportunities |
|-------|-------|----------------------|
| Setup | 6 | 4 (T002, T003, T004, T005) |
| Foundational | 7 | 3 (T008, T009, T011) + 2 backend (T012, T013) |
| US1 — Source Setup | 14 | 6 (T014, T015, T020, T021, T023, T024) |
| US2 — Import | 4 | 1 (T031) |
| US3 — Data View | 11 | 4 (T032, T033, T037, T038, T041, T042) |
| Polish | 6 | 4 (T044, T045, T046, T047) |
| **Total** | **48** | **~24 parallel** |
