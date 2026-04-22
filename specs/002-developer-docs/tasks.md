# Tasks: Developer Documentation

**Input**: Design documents from `specs/002-developer-docs/`
**Branch**: `002-developer-docs`
**Stack**: Docusaurus v3 (TypeScript, classic preset) · GitHub Pages · GitHub Actions

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: Maps to user story (US1 = Getting Started, US2 = Integration, US3 = Reference)
- Exact file paths included in every task

---

## Phase 1: Setup

**Purpose**: Scaffold the Docusaurus project and CI/CD infrastructure.

- [X] T001 Initialize Docusaurus v3 in `website/`: run `npx create-docusaurus@latest website classic --typescript`, accept defaults
- [X] T002 Remove generated example content from `website/`: delete `website/docs/tutorial-basics/`, `website/docs/tutorial-extras/`, `website/blog/`, `website/docs/intro.md` (will be replaced), and the `blog` entry from `website/docusaurus.config.ts`
- [X] T003 Configure `website/docusaurus.config.ts`: set `title: 'AnswerGuard'`, `tagline: 'Response quality enforcement for AI agent products'`, `url: 'https://bardiakhosravi.github.io'`, `baseUrl: '/answer-guard/'`, `organizationName: 'bardiakhosravi'`, `projectName: 'answer-guard'`, `trailingSlash: false`; add GitHub link to navbar; configure `prism` code highlighting for Python, TypeScript, bash, JSON, yaml
- [X] T004 [P] Install local search plugin: `cd website && npm install @docusaurus/plugin-search-local`; add plugin config to `website/docusaurus.config.ts`
- [X] T005 [P] Create GitHub Actions workflow `/.github/workflows/docs.yml`: trigger on `push` to `main` (path filter `website/**`); steps: checkout → Node.js 20 → `npm ci` in `website/` → `npm run build` → `peaceiris/actions-gh-pages@v3` deploying `website/build/` to `gh-pages` branch
- [X] T006 [P] Create pull request template `/.github/pull_request_template.md`: include a checkbox `- [ ] If this PR changes any documented behaviour (API fields, config options, SDK methods, error messages), the relevant page in website/docs/ has been updated`
- [X] T007 Add `website/node_modules/` and `website/build/` to `/.gitignore`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core site structure that all user story content depends on.

**⚠️ CRITICAL**: Sidebar and nav must be configured before content pages are written.

- [X] T008 Configure `website/sidebars.ts`: define full sidebar matching the navigation contract in `specs/002-developer-docs/contracts/navigation.md` — all 11 doc pages listed in order, grouped under Overview, Quickstart, Integration Guide (6 sub-pages), Reference (2 sub-pages), Troubleshooting
- [X] T009 [P] Create custom landing page `website/src/pages/index.tsx`: hero section with AnswerGuard title, tagline, "Get Started →" CTA button linking to `/docs/quickstart`, "View on GitHub" button; use Docusaurus `Layout`, `Heading`, `Link` components; keep it simple — no custom CSS required beyond Docusaurus defaults
- [X] T010 [P] Create `website/static/img/` directory; add a simple ASCII-style or Mermaid-rendered data flow diagram as `website/static/img/answerguard-flow.png` (or create as SVG): `agent system → [AnswerGuard] → PM review interface`
- [X] T011 Verify Docusaurus builds without errors: `cd website && npm run build` — fix any broken links or config issues before proceeding to content

**Checkpoint**: `npm run start` shows a working site with correct nav, placeholder pages for all 11 docs, and the landing page. All subsequent content tasks can proceed in parallel.

---

## Phase 3: User Story 1 — Getting Started (Priority: P1) 🎯 MVP

**Goal**: A developer who has never seen AnswerGuard can read the overview, understand the tool, and have a local instance running with captured data within 30 minutes.

**Independent Test**: Follow the quickstart from a clean Python 3.11 environment; verify a running server and captured Q&A pair appear in the status endpoint within 30 minutes — using only the published documentation.

- [X] T012 [US1] Write `website/docs/intro.md`: what AnswerGuard is (1 paragraph), who it is for, the problem it solves, the data flow description (`agent system → AnswerGuard → PM review`), quick links to Quickstart and Integration Guide; set Docusaurus frontmatter `sidebar_position: 1`; must be readable in under 5 minutes
- [X] T013 [US1] Write `website/docs/quickstart.md`: title "Quickstart", time-estimate admonition ("⏱ Under 30 minutes"), prerequisites section (Python 3.11+, pip, git — explicitly state no Docker required), then numbered steps: (1) clone repo, (2) create venv + install deps `pip install -e .`, (3) copy `.env.example` to `.env` (SQLite DATABASE_URL is pre-set), (4) run migrations `DATABASE_URL=sqlite:///./answerguard.db PYTHONPATH=. alembic upgrade head`, (5) start server `DATABASE_URL=sqlite:///./answerguard.db uvicorn main:app --port 8080`, (6) health check `curl http://localhost:8080/health`, (7) test capture `curl -X POST http://localhost:8080/v1/capture -H 'Content-Type: application/json' -d '{"question":"What is AnswerGuard?","answer":"A response quality tool.","source_system_id":"quickstart-test"}'`, (8) verify `curl http://localhost:8080/v1/ingest/status`; end with "Next Steps" linking to integration guide

**Checkpoint**: US1 complete. A developer reading intro.md and quickstart.md has everything needed to evaluate AnswerGuard and get a local instance running.

---

## Phase 4: User Story 2 — Integration Guide (Priority: P2)

**Goal**: A developer with an existing agent system and BigQuery dataset can complete the full integration (historical import + runtime SDK capture + verification) using only the documentation.

**Independent Test**: An external developer with a BigQuery dataset integrates AnswerGuard — historical import + Python or TypeScript SDK capture — with zero support requests. Each sub-page can be validated independently.

- [X] T014 [P] [US2] Write `website/docs/integration/index.md`: integration overview explaining the two tasks (historical import + runtime capture), prerequisites (running agent system, BigQuery dataset), recommended order (import first, then SDK), links to all 5 sub-pages
- [X] T015 [P] [US2] Write `website/docs/integration/bigquery.md`: GCP prerequisites (project ID, BigQuery dataset + table, service account with `BigQuery Data Viewer` role), authentication options (service account JSON key file via `GOOGLE_APPLICATION_CREDENTIALS` env var vs Application Default Credentials for Google Cloud environments), full `SourceConnector` configuration table (all fields from `specs/001-qa-response-ingestion/contracts/api.md` import request body: `source_system_id`, `gcp_project_id`, `dataset_id`, `table_id`, `credentials_path`, `field_mapping`, `row_filter`, `page_size`), `FieldMapping` configuration table (`question_column`, `answer_column`, `timestamp_column`, `external_id_column`, `metadata_columns`) with required/optional and examples
- [X] T016 [P] [US2] Write `website/docs/integration/historical-import.md`: how to trigger via `POST /v1/ingest/import` (full request body example with all fields populated), how to monitor with `GET /v1/ingest/status/{run_id}`, explanation of `records_processed` vs `records_skipped`, how to resume a FAILED run (re-send same request — auto-detects FAILED run and resumes from `last_checkpoint`), skip-and-log behaviour explained, example response showing a completed run with errors array
- [X] T017 [P] [US2] Write `website/docs/integration/python-sdk.md`: installation (`pip install answerguard-sdk` — note: during development use `pip install -e ./sdk/python`), minimal working example in a code block (5 lines max): `from answerguard import AnswerGuard; guard = AnswerGuard(endpoint="http://localhost:8080", source_system_id="my-agent"); guard.capture(question, answer)`, `capture()` vs `capture_sync()` (when to use each, return types), `metadata` dict parameter with example, constructor parameters table (`endpoint`, `source_system_id`, `timeout_ms`), fail-open behaviour explained (never raises, logs to stderr)
- [X] T018 [P] [US2] Write `website/docs/integration/typescript-sdk.md`: installation (`npm install @answerguard/sdk`), minimal working example (5 lines max): `import { AnswerGuard } from '@answerguard/sdk'; const guard = new AnswerGuard({ endpoint: 'http://localhost:8080', sourceSystemId: 'my-agent' }); guard.capture(question, answer);`, `capture()` vs `captureAsync()` (when to use each), `metadata` parameter with example, constructor options table (`endpoint`, `sourceSystemId`, `timeoutMs`), fail-open behaviour explained (no await on `fetch`, errors to `console.error`)
- [X] T019 [US2] Write `website/docs/integration/verification.md`: how to use `GET /v1/ingest/status` (no run_id) to see overall stats, full example response with explanation of every field (`total_qa_pairs`, `sources[].runtime_captures_last_24h`, `sources[].last_import_run.status`), what a healthy integration looks like vs what needs attention (run stuck in RUNNING, zero captures in 24h)

**Checkpoint**: US2 complete. A developer with BigQuery access can complete the full integration using these 6 pages alone.

---

## Phase 5: User Story 3 — Reference Documentation (Priority: P3)

**Goal**: A developer can find the exact answer to any specific question (field type, default value, error code) within 60 seconds.

**Independent Test**: Give 5 developers a list of 10 questions about API fields and configuration options; all find answers in under 60 seconds using these two pages.

- [X] T020 [P] [US3] Write `website/docs/reference/api.md`: document every endpoint from `specs/001-qa-response-ingestion/contracts/api.md` — `POST /v1/ingest/import`, `GET /v1/ingest/status`, `GET /v1/ingest/status/{run_id}`, `POST /v1/capture`, `GET /health`; for each: method + path heading, description paragraph, request body table (field name | type | required | default | description), response body table, example request JSON in a code block, example response JSON in a code block, error responses table (HTTP status | error key | when it occurs); field names must exactly match the implemented API
- [X] T021 [P] [US3] Write `website/docs/reference/configuration.md`: four sections — Database (`DATABASE_URL`: type string, required, SQLite example `sqlite:///./answerguard.db`, PostgreSQL example `postgresql://user:pass@host:5432/db`), BigQuery (`GCP_PROJECT_ID`: required string; `GOOGLE_APPLICATION_CREDENTIALS`: optional string, path to service account JSON; `BIGQUERY_PAGE_SIZE`: optional integer, default 5000), Server (host and port via uvicorn CLI args), SDK config for Python (`endpoint`, `source_system_id`, `timeout_ms`) and TypeScript (`endpoint`, `sourceSystemId`, `timeoutMs`); each item: name | type | required | default | description | example
- [X] T022 [US3] Write `website/docs/troubleshooting.md`: five entries (each with "Symptom", "Cause", "Resolution" sub-sections): (1) `FileNotFoundError: [Errno 2] No such file or directory` when `GOOGLE_APPLICATION_CREDENTIALS` is set but path is wrong — check path, use absolute path; (2) `FieldMappingValidationError: Column 'X' not found` — list available columns from error message, fix `field_mapping` config; (3) `409 IMPORT_ALREADY_RUNNING` — check status endpoint for active run, wait for completion or investigate stuck run; (4) `sqlalchemy.exc.OperationalError: no such table: qa_pairs` — migrations not applied, run `alembic upgrade head`; (5) SDK captures not appearing in status — switch from `capture()` to `capture_sync()` to surface errors, check `endpoint` URL and `source_system_id` match server config

**Checkpoint**: US3 complete. All 11 docs pages exist and pass `npm run build` without broken links.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [X] T023 Run `cd website && npm run build` — fix all broken links and build warnings; confirm zero errors
- [X] T024 [P] Add `website/` to the `.gitignore` exclusion for `node_modules` and `build`; add `website/.docusaurus/` to `.gitignore`
- [X] T025 [P] Enable GitHub Pages in repository settings: Settings → Pages → Source: `gh-pages` branch (must be done manually after first deploy)
- [X] T026 Push to `main` and confirm GitHub Actions workflow `docs.yml` runs successfully; verify site is live at `https://bardiakhosravi.github.io/answer-guard/`
- [X] T027 Validate navigation contract: open the live site and confirm every page listed in `specs/002-developer-docs/contracts/navigation.md` is reachable from the sidebar
- [X] T028 [P] Validate reference accuracy: compare every field in `website/docs/reference/api.md` against `specs/001-qa-response-ingestion/contracts/api.md` — names, types, required/optional, and defaults must match exactly

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Requires Phase 1 (Docusaurus initialized) — blocks all content
- **US1 (Phase 3)**: Requires Phase 2 (sidebar configured, build verified)
- **US2 (Phase 4)**: Requires Phase 2 — can run in parallel with US1 after checkpoint
- **US3 (Phase 5)**: Requires Phase 2 — can run in parallel with US1 and US2
- **Polish (Phase 6)**: Requires all three user stories complete

### Parallel Opportunities Within Phases

**Phase 1**: T004, T005, T006 are all independent — run together after T001-T003
**Phase 2**: T009, T010 are independent — run together after T008
**Phase 4 (US2)**: T014, T015, T016, T017, T018 are all independent pages — run all together; T019 follows (requires understanding of what came before)
**Phase 5 (US3)**: T020, T021 are independent — run together; T022 follows

### Parallel Example: US2 Integration Guide

```
Stream A: T014 (integration/index.md)   → can merge immediately
Stream B: T015 (bigquery.md)            → can merge immediately
Stream C: T016 (historical-import.md)   → can merge immediately
Stream D: T017 (python-sdk.md)          → can merge immediately
Stream E: T018 (typescript-sdk.md)      → can merge immediately
                                         ↓ all five done
Stream F: T019 (verification.md)        → depends on reading A-E for accuracy
```

---

## Implementation Strategy

### MVP (User Story 1 Only — P1)

1. Complete Phase 1: Setup (T001–T007)
2. Complete Phase 2: Foundational (T008–T011)
3. Complete Phase 3: US1 — Overview + Quickstart (T012–T013)
4. **STOP and VALIDATE**: Follow the quickstart from a clean environment; confirm under 30 minutes
5. Push to `main` and verify GitHub Pages is live with just these 2 pages

### Incremental Delivery

1. Setup + Foundational → working Docusaurus site on GitHub Pages (empty content)
2. US1 (Overview + Quickstart) → developers can evaluate and try the tool → **demo**
3. US2 (Integration Guide, 6 pages) → developers can fully integrate → **demo**
4. US3 (Reference, 3 pages) → developers have a reference to return to → **demo**
5. Polish → validated navigation, confirmed GitHub Pages, reference accuracy check

### Total Task Count

| Phase | Tasks | Parallel Opportunities |
|-------|-------|----------------------|
| Setup | 7 | 3 (T004, T005, T006) |
| Foundational | 4 | 2 (T009, T010) |
| US1 — Getting Started | 2 | 0 (sequential) |
| US2 — Integration | 6 | 5 (T014–T018) |
| US3 — Reference | 3 | 2 (T020, T021) |
| Polish | 6 | 2 (T024, T025, T028) |
| **Total** | **28** | **14** |
