# Tasks: Q&A Response Ingestion & Storage

**Input**: Design documents from `specs/001-qa-response-ingestion/`
**Branch**: `001-qa-response-ingestion`
**Stack**: Python 3.11+ / FastAPI / SQLAlchemy 2.0 / Alembic / google-cloud-bigquery / TypeScript 5.x

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files, no shared dependencies)
- **[Story]**: Maps to user story (US1, US2, US3)
- Exact file paths included in every task

---

## Phase 1: Setup

**Purpose**: Project structure and tooling initialization.

- [X] T001 Create directory structure: `src/domain/`, `src/application/`, `src/adapters/`, `src/configuration/`, `sdk/python/`, `sdk/typescript/`, `tests/unit/`, `tests/integration/`, `tests/contract/` with `__init__.py` files (no `src/domain/events/` — domain events are deferred until a real consumer exists)
- [X] T002 Initialize Python project: create `pyproject.toml` with dependencies (`fastapi`, `uvicorn`, `sqlalchemy>=2.0`, `alembic`, `google-cloud-bigquery`, `pydantic-settings`, `pytest`, `httpx`)
- [X] T003 [P] Initialize TypeScript SDK project: create `sdk/typescript/package.json` with `typescript`, `vitest` dependencies and `tsconfig.json`
- [X] T004 [P] Configure Python linting: add `ruff` config to `pyproject.toml`, create `.ruff.toml`
- [X] T005 [P] Create `Dockerfile` and `docker-compose.yml` for local development (API + PostgreSQL + SQLite fallback)
- [X] T006 Create `.env.example` with all required environment variables: `DATABASE_URL`, `GCP_PROJECT_ID`, `GOOGLE_APPLICATION_CREDENTIALS`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before any user story work begins.

**⚠️ CRITICAL**: No user story work can start until this phase is complete.

- [X] T007 Create exception hierarchy: `DomainException` and `AdapterException` base classes in `src/domain/exceptions.py`
- [X] T009 Create `app_settings.py` in `src/configuration/` using `pydantic-settings`: load `DATABASE_URL`, `GCP_PROJECT_ID`, `GOOGLE_APPLICATION_CREDENTIALS`, `BIGQUERY_PAGE_SIZE` from environment
- [X] T010 Create `database_config.py` in `src/configuration/`: detect SQLite vs PostgreSQL from `DATABASE_URL` prefix, create SQLAlchemy engine and `SessionLocal` factory, configure `render_as_batch=True` for Alembic
- [X] T011 Initialize Alembic: run `alembic init alembic/`, configure `env.py` to use `database_config.DatabaseConfig`, set `render_as_batch = True`
- [X] T012 Create `main.py` at repo root: initialize FastAPI app, register routers (placeholders), add startup/shutdown lifespan hooks for DB session
- [X] T013 Create `di_container.py` skeleton in `src/configuration/` with stubs for all use case factory methods (return `None` until wired in later phases)
- [X] T014b [P] Create `QAPairRepository` abstract port in `src/domain/ports/qa_pair_repository.py`: methods `save(qa_pair: QAPair) -> None`, `find_by_hash(source_hash: SourceHash) -> Optional[QAPair]`, `find_by_id(qa_pair_id: QAPairId) -> Optional[QAPair]`, `count_by_source(source_system_id: str) -> int`, `count_by_source_since(source_system_id: str, since: datetime) -> int`

**Checkpoint**: Project runs (`uvicorn main:app`), Alembic can generate migrations, FastAPI app starts. All user story work can now begin.

---

## Phase 3: User Story 1 — Historical Data Import from BigQuery (Priority: P1) 🎯 MVP

**Goal**: Developer configures BigQuery source, triggers import, all historical Q&A pairs land in AnswerGuard's database. PM can immediately see data in storage.

**Independent Test**: Configure BigQuery connector with 100-row test table → `POST /v1/ingest/import` → poll `GET /v1/ingest/status/{run_id}` → verify 100 records in DB, 0 duplicates on second run.

### Domain Layer

- [X] T015 [P] [US1] Create `QAPairId` value object in `src/domain/model/qa_pair/qa_pair_id.py`: wraps UUID string, `generate()` class method
- [X] T016 [P] [US1] Create `IngestionMethod` enum in `src/domain/model/qa_pair/ingestion_method.py`: `HISTORICAL_IMPORT`, `RUNTIME_CAPTURE`
- [X] T017 [P] [US1] Create `SourceHash` value object in `src/domain/model/qa_pair/source_hash.py`: computes `sha256(question + answer + source_system_id)`, exposes `.value: str`
- [X] T018 [P] [US1] Create `IngestionRunId` value object in `src/domain/model/ingestion_run/ingestion_run_id.py`: wraps UUID string, `generate()` class method
- [X] T019 [P] [US1] Create `IngestionStatus` enum in `src/domain/model/ingestion_run/ingestion_status.py`: `RUNNING`, `COMPLETED`, `FAILED`, `RESUMED`
- [X] T020 [P] [US1] Create `FieldMapping` value object in `src/domain/model/ingestion_run/field_mapping.py`: fields `question_column`, `answer_column`, `timestamp_column` (optional), `external_id_column` (optional), `metadata_columns: dict[str, str]`; validate non-empty required columns in `__post_init__`
- [X] T021 [P] [US1] Create `SourceConnector` value object in `src/domain/model/ingestion_run/source_connector.py`: fields `source_system_id`, `gcp_project_id`, `dataset_id`, `table_id`, `credentials_path` (optional), `field_mapping: FieldMapping`, `row_filter` (optional), `page_size: int = 5000`
- [X] T022 [US1] Create `QAPair` aggregate root in `src/domain/model/qa_pair/qa_pair.py`: `@dataclass(eq=False)`, factory method `QAPair.create(question, answer, source_system_id, ingestion_method, ...)` computes `SourceHash`, raises `DomainException` on empty question/answer; implement `__eq__` and `__hash__` on `id`
- [X] T023 [US1] Create `IngestionRun` entity in `src/domain/model/ingestion_run/ingestion_run.py`: `@dataclass(eq=False)`, factory `IngestionRun.start(source_connector)`, methods: `complete()`, `fail(reason)`, `resume()`, `record_progress(processed, skipped, checkpoint)`, `log_error(index, reason)`; enforce state machine transitions, raise `DomainException` on invalid transition; include `config_snapshot: dict` field populated in `IngestionRun.start()` from `SourceConnector` (serialised as dict for storage in `IngestionRunModel`)
### Domain Ports

- [X] T026 [P] [US1] Create `IngestionRunRepository` abstract port in `src/domain/ports/ingestion_run_repository.py`: methods `save(run: IngestionRun) -> None`, `find_by_id(run_id: IngestionRunId) -> Optional[IngestionRun]`, `find_active_for_source(source_system_id: str) -> Optional[IngestionRun]`, `find_latest_for_source(source_system_id: str) -> Optional[IngestionRun]`, `find_latest_per_source() -> list[IngestionRun]` (returns the most recent run per distinct `source_system_id` — used by the overall status summary endpoint)
- [X] T027 [P] [US1] Create `BigQuerySourcePort` abstract port in `src/application/ports/secondary/bigquery_source_port.py`: methods `read_rows(connector: SourceConnector, start_index: int = 0) -> Iterator[dict]`, `get_schema(connector: SourceConnector) -> list[str]`

### Application Layer

- [X] T028 [P] [US1] Create `ImportHistoricalDataCommand` in `src/application/commands/import_historical_data_command.py`: dataclass with `source_connector: SourceConnector`
- [X] T029 [P] [US1] Create `ImportHistoricalDataPort` in `src/application/ports/primary/import_historical_data_port.py`: abstract `execute(command: ImportHistoricalDataCommand) -> ImportHistoricalDataResponse`; define `ImportHistoricalDataResponse` dataclass with `ingestion_run_id: str`, `status: str`, `message: str`
- [X] T030 [US1] Create `ImportHistoricalDataUseCase` in `src/application/use_cases/import_historical_data_use_case.py`: (1) validate field mapping via `BigQuerySourcePort.get_schema()` — raise `FieldMappingValidationError` if column missing; (2) if existing `FAILED` run found for same `source_system_id`, resume it from `last_checkpoint`; if `RUNNING`, raise `ImportAlreadyRunningError`; (3) start or resume `IngestionRun`, persist; (4) stream rows in pages, create `QAPair` for each, save (skip duplicates via `find_by_hash`), update checkpoint every batch; (5) complete or fail run on finish

### Secondary Adapters

- [X] T031 [P] [US1] Create `QAPairModel` SQLAlchemy ORM model in `src/adapters/secondary/sql/models/qa_pair_model.py`: maps all fields from data-model.md, use `JSON().with_variant(JSONB(), "postgresql")` for metadata, use `String(36)` for UUID fields on SQLite
- [X] T032 [P] [US1] Create `IngestionRunModel` SQLAlchemy ORM model in `src/adapters/secondary/sql/models/ingestion_run_model.py`: maps all fields from data-model.md, use `JSON` for `error_log` and `config_snapshot`
- [X] T033 [US1] Generate and apply Alembic migration: `alembic revision --autogenerate -m "create_qa_pairs_and_ingestion_runs"`, review generated migration, apply with `alembic upgrade head`
- [X] T034 [US1] Create `SqlQAPairRepository` in `src/adapters/secondary/sql/sql_qa_pair_repository.py`: implements `QAPairRepository`; `save()` uses `INSERT ... ON CONFLICT (source_hash) DO NOTHING` for PostgreSQL / `INSERT OR IGNORE` for SQLite; map domain ↔ ORM model in `_to_domain()` and `_to_model()` private methods
- [X] T035 [US1] Create `SqlIngestionRunRepository` in `src/adapters/secondary/sql/sql_ingestion_run_repository.py`: implements `IngestionRunRepository`; map domain ↔ ORM model in private methods
- [X] T036 [US1] Create `BigQuerySourceAdapter` in `src/adapters/secondary/bigquery/bigquery_source_adapter.py`: implements `BigQuerySourcePort`; initialize `bigquery.Client` from service account JSON or ADC; `read_rows()` uses `client.list_rows(table_id, start_index=start_index, page_size=connector.page_size)` and yields dicts page by page; `get_schema()` returns column names; wrap all BigQuery exceptions in `AdapterException`

### Primary Adapter

- [X] T037 [US1] Create `ingestion_router.py` in `src/adapters/primary/web/`: FastAPI `APIRouter`; define Pydantic request/response models for `POST /v1/ingest/import` and `GET /v1/ingest/status/{run_id}`; translate domain exceptions to 400/409 HTTP responses, `AdapterException` to 502; register router in `main.py`

### Wiring

- [X] T038 [US1] Wire US1 in `src/configuration/di_container.py`: implement `bigquery_source_adapter()`, `sql_qa_pair_repository()`, `sql_ingestion_run_repository()`, `import_historical_data_use_case()` factory methods using `SessionLocal` from `database_config`

### Tests

- [X] T039 [P] [US1] Unit test `QAPair` in `tests/unit/domain/test_qa_pair.py`: test factory method creates correct hash, empty question raises `DomainException`, empty answer raises `DomainException`, two identical pairs have same `source_hash`
- [X] T040 [P] [US1] Unit test `IngestionRun` in `tests/unit/domain/test_ingestion_run.py`: test all valid state transitions, invalid transitions raise `DomainException`, `record_progress()` updates counts, `log_error()` appends to error log
- [X] T041 [US1] Unit test `ImportHistoricalDataUseCase` in `tests/unit/application/test_import_historical_data_use_case.py`: mock `BigQuerySourcePort`, `QAPairRepository`, `IngestionRunRepository`; test field mapping validation failure → no run started; duplicate rows → counted as skipped; successful import → run completed; mid-run exception → run failed with checkpoint

**Checkpoint**: US1 complete. POST /v1/ingest/import triggers BigQuery read → DB write. PM sees imported data.

---

## Phase 4: User Story 2 — Runtime Response Capture via SDK (Priority: P2)

**Goal**: Developer adds 2 lines to their agent pipeline. Every new agent response is automatically captured in AnswerGuard storage. SDK adds <50ms overhead.

**Independent Test**: Call `guard.capture("q", "a")` from Python SDK → verify record in DB within 5 seconds. Call `POST /v1/capture` directly → verify 201 response and DB record.

### Application Layer

- [X] T042 [P] [US2] Create `CaptureResponseCommand` in `src/application/commands/capture_response_command.py`: dataclass with `question: str`, `answer: str`, `source_system_id: str`, `metadata: dict[str, str]`
- [X] T043 [P] [US2] Create `CaptureRuntimeResponsePort` in `src/application/ports/primary/capture_runtime_response_port.py`: abstract `execute(command: CaptureResponseCommand) -> CaptureResponse`; define `CaptureResponse` with `qa_pair_id: str`, `captured_at: str`
- [X] T044 [US2] Create `CaptureRuntimeResponseUseCase` in `src/application/use_cases/capture_runtime_response_use_case.py`: create `QAPair` with `ingestion_method=RUNTIME_CAPTURE`, call `find_by_hash` to check duplicate (return existing ID if dupe), save

### Primary Adapter

- [X] T045 [US2] Create `capture_router.py` in `src/adapters/primary/web/`: FastAPI `APIRouter`; define Pydantic request/response models for `POST /v1/capture`; map 409 for duplicates, 400 for validation errors; register router in `main.py`

### Python SDK

- [X] T046 [US2] Create `capture.py` in `sdk/python/answerguard/`: implement `BackgroundCaptureDispatcher` using `concurrent.futures.ThreadPoolExecutor(max_workers=2, thread_name_prefix="ag-capture")`; daemon threads; catches all exceptions and logs to `stderr`; honours configurable `timeout_ms`
- [X] T047 [US2] Create `client.py` in `sdk/python/answerguard/`: implement `AnswerGuard` class; `__init__(endpoint, source_system_id, timeout_ms=2000)`; `capture(question, answer, metadata=None) -> None` — fire-and-forget via `BackgroundCaptureDispatcher`; `capture_sync(question, answer, metadata=None) -> CaptureResult` — blocking HTTP POST to `/v1/capture`
- [X] T048 [P] [US2] Create `sdk/python/answerguard/__init__.py`: export `AnswerGuard`, `CaptureResult`; create `sdk/python/pyproject.toml` with package metadata and `httpx` dependency

### TypeScript SDK

- [X] T049 [US2] Create `client.ts` in `sdk/typescript/src/`: implement `AnswerGuard` class; `constructor(config: { endpoint: string; sourceSystemId: string; timeoutMs?: number })`; `capture(question, answer, options?) -> void` — calls `fetch()` without `await`, logs errors to `console.error`; `captureAsync(question, answer, options?) -> Promise<{ qa_pair_id: string }>` — awaited version
- [X] T050 [P] [US2] Create `sdk/typescript/src/index.ts`: export `AnswerGuard`, `AnswerGuardConfig`, `CaptureOptions`

### Wiring & Tests

- [X] T051 [US2] Wire US2 in `src/configuration/di_container.py`: add `capture_runtime_response_use_case()` factory method
- [X] T052 [US2] Unit test `CaptureRuntimeResponseUseCase` in `tests/unit/application/test_capture_runtime_response_use_case.py`: mock repositories; test successful capture stores record with `RUNTIME_CAPTURE` method; duplicate returns existing ID without creating new record

**Checkpoint**: US2 complete. SDK `capture()` and `POST /v1/capture` both store Q&A pairs. Overhead <50ms.

---

## Phase 5: User Story 3 — Ingestion Health & Verification (Priority: P3)

**Goal**: Developer can verify integration worked: total counts, skipped records, last ingested timestamp, error details — all from one status endpoint.

**Independent Test**: After US1 import of 100 records (3 intentionally invalid), `GET /v1/ingest/status` returns `total_qa_pairs: 97`, `records_skipped: 3` with skip reasons.

### Application Layer

- [X] T053 [P] [US3] Create `GetIngestionStatusQuery` in `src/application/queries/get_ingestion_status_query.py`: dataclass with optional `source_system_id: str | None = None`, optional `run_id: str | None = None`
- [X] T054 [P] [US3] Create `GetIngestionStatusPort` in `src/application/ports/primary/get_ingestion_status_port.py`: abstract `execute(query: GetIngestionStatusQuery) -> IngestionStatusResponse`; define response dataclasses matching contracts/api.md `GET /v1/ingest/status` shape
- [X] T055 [US3] Create `GetIngestionStatusUseCase` in `src/application/use_cases/get_ingestion_status_use_case.py`: aggregate counts from `QAPairRepository` and `IngestionRunRepository`; if `run_id` provided return single-run detail; otherwise return summary across all sources; compute `runtime_captures_last_24h` per source using `QAPairRepository.count_by_source_since(source_system_id, now - 24h)`

### Primary Adapter

- [X] T056 [US3] Add `GET /v1/ingest/status` (overall summary) route to `src/adapters/primary/web/ingestion_router.py`; the `GET /v1/ingest/status/{run_id}` single-run route is already defined in T037

### Wiring & Tests

- [X] T057 [US3] Wire US3 in `src/configuration/di_container.py`: add `get_ingestion_status_use_case()` factory method
- [X] T058 [US3] Unit test `GetIngestionStatusUseCase` in `tests/unit/application/test_get_ingestion_status_use_case.py`: mock repositories; test summary includes correct counts per source; unknown run_id raises `NotFoundError`

**Checkpoint**: US3 complete. All three user stories independently functional.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [X] T059 [P] Write contract test `tests/contract/test_qa_pair_repository_contract.py`: abstract base contract test; run against `SqlQAPairRepository` with SQLite fixture; verify save, find_by_hash, dedup behaviour
- [X] T060 [P] Write integration test `tests/integration/test_sql_qa_pair_repository.py` and `test_sql_ingestion_run_repository.py`: full round-trip tests using SQLite in-memory DB
- [ ] T060b [P] Benchmark historical import throughput: import a 100K-row BigQuery test table, measure records/min, assert ≥10,000 records/min (SC-002); document result in `specs/001-qa-response-ingestion/benchmarks.md`
- [ ] T060c [P] Measure SDK capture latency: instrument Python and TypeScript `capture()` calls with timing, run 1,000 iterations, assert p95 < 50ms end-to-end (SC-003); document result in `specs/001-qa-response-ingestion/benchmarks.md`
- [ ] T060d [P] Integration test SC-004: after `capture()` call, poll storage for up to 5 seconds, assert record is retrievable within that window; add to `tests/integration/test_capture_durability.py`
- [ ] T060e [P] Integration test SC-005: simulate storage unavailability during SDK `capture()`, assert original call is unblocked AND failure is logged to stderr; add to `tests/integration/test_capture_fail_open.py`
- [ ] T061 [P] Write `specs/001-qa-response-ingestion/quickstart.md`: step-by-step guide for developer to set up BigQuery connector, run import, verify with status endpoint, integrate Python and TypeScript SDKs
- [X] T062 Run architecture review: execute `/tenets-review-architecture` and fix any violations before marking feature complete

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Requires Phase 1 — blocks all user stories
- **US1 (Phase 3)**: Requires Phase 2 — largest phase, no other story dependencies
- **US2 (Phase 4)**: Requires Phase 2 (including T014b `QAPairRepository` port) — can run in parallel with US1 after Foundational phase completes
- **US3 (Phase 5)**: Requires US1 and US2 to be meaningful — reads data both produce
- **Polish (Phase 6)**: Requires all stories complete

### Within US1 (Phase 3)

```
T015–T021 (value objects) [all parallel]
  ↓
T022 (QAPair entity, depends on value objects)
T023 (IngestionRun entity, depends on value objects)
T024 (domain events) [parallel with T022/T023]
  ↓
T025–T027 (ports) [all parallel]
  ↓
T028–T030 (application layer — command, port, use case)
T031–T032 (ORM models) [parallel with T028–T030]
  ↓
T033 (Alembic migration — depends on ORM models)
  ↓
T034–T036 (repositories + BigQuery adapter) [parallel]
  ↓
T037 (primary adapter)
  ↓
T038 (DI wiring)
  ↓
T039–T041 (tests) [T039/T040 parallel]
```

### Parallel Opportunities

Within any phase, tasks marked `[P]` can run concurrently:
- All value objects (T015–T021): 7 tasks in parallel
- ORM models (T031, T032): 2 tasks in parallel
- Repositories and BigQuery adapter (T034, T035, T036): 3 tasks in parallel
- Domain tests (T039, T040): 2 tasks in parallel
- Python and TypeScript SDK implementation (T046–T048 vs T049–T050): parallel streams

---

## Parallel Example: US1 Domain Layer

```
Stream A: T015 (QAPairId) → T022 (QAPair entity) → T025 (QAPairRepository port)
Stream B: T016 (IngestionMethod) → parallel with Stream A
Stream C: T017 (SourceHash) → parallel with Stream A
Stream D: T018 (IngestionRunId) → T023 (IngestionRun entity) → T026 (IngestionRunRepository port)
Stream E: T019 (IngestionStatus) → parallel with Stream D
Stream F: T020 (FieldMapping) → T021 (SourceConnector) → then feeds T027 (BigQuerySourcePort)
Stream G: T024 (domain events) → parallel with all above
```

---

## Implementation Strategy

### MVP (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: US1 (T015–T041)
4. **STOP and VALIDATE**: Import 100 BigQuery rows, verify in DB, verify no duplicates on second run
5. Merge and demo to client

### Incremental Delivery

1. Setup + Foundational → runnable FastAPI app
2. US1 → historical import working → **demo**
3. US2 → runtime SDK working → **demo**
4. US3 → status/health endpoints → **demo**
5. Polish → tests, quickstart, architecture review

### Total Task Count

| Phase | Tasks | Parallel Opportunities |
|-------|-------|----------------------|
| Setup | 6 | 3 |
| Foundational | 8 | 2 |
| US1 | 27 | 12 |
| US2 | 11 | 4 |
| US3 | 6 | 2 |
| Polish | 4 | 3 |
| **Total** | **62** | **26** |
