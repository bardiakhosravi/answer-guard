# Implementation Plan: Desktop App — Integration Setup

**Branch**: `003-desktop-integration-setup` | **Date**: 2026-04-22 | **Spec**: [spec.md](./spec.md)

---

## Summary

Build the AnswerGuard desktop app v1 using Tauri v2 + React/TypeScript. Covers: server connection, BigQuery source connector setup with guided field mapping via live schema discovery, historical import with live progress, and a paginated searchable data view.

Also adds two new AnswerGuard backend endpoints (`POST /v1/sources/discover-schema` and `GET /v1/qa-pairs`) following the existing hexagonal architecture.

---

## Technical Context

**Desktop framework**: Tauri v2 (Rust shell + React/TypeScript frontend)
**Frontend**: React 18, TypeScript, React Router v6, React Query (polling), React Hook Form, Tailwind CSS
**Local persistence**: `@tauri-apps/plugin-store` (JSON config in OS app data dir)
**File picker**: `@tauri-apps/plugin-dialog`
**HTTP**: Standard `fetch` from React frontend to AnswerGuard REST API
**Backend additions**: Python/FastAPI (same stack as existing)
**Target platforms**: macOS, Windows

---

## Constitution Check

| Principle | Applies To | Status | Notes |
|-----------|-----------|--------|-------|
| Domain layer independence | Backend | PASS | New endpoints are adapters; domain untouched |
| Ports define external boundaries | Backend | PASS | New primary ports for each use case |
| Use cases contain no business logic | Backend | PASS | Both new use cases orchestrate only |
| Aggregates own mutations | Backend | PASS | Both new endpoints are read-only |
| Desktop app architecture | Frontend | N/A | Tauri/React; hexagonal rules don't apply |

---

## Project Structure

### Backend additions (`src/`)

```text
src/
├── domain/
│   └── ports/
│       └── qa_pair_repository.py        # Add: list_paginated() method
├── application/
│   ├── ports/
│   │   └── primary/
│   │       ├── discover_schema_port.py      # NEW
│   │       └── list_qa_pairs_port.py        # NEW
│   ├── commands/
│   │   └── discover_schema_command.py       # NEW
│   ├── queries/
│   │   └── list_qa_pairs_query.py           # NEW
│   └── use_cases/
│       ├── discover_schema_use_case.py      # NEW
│       └── list_qa_pairs_use_case.py        # NEW
├── adapters/
│   ├── primary/
│   │   └── web/
│   │       ├── sources_router.py            # NEW: POST /v1/sources/discover-schema
│   │       └── qa_pairs_router.py           # NEW: GET /v1/qa-pairs
│   └── secondary/
│       └── sql/
│           └── sql_qa_pair_repository.py    # Add: list_paginated()
└── configuration/
    └── di_container.py                      # Wire new use cases
```

### Desktop app (`desktop/`)

```text
desktop/
├── src-tauri/                     # Tauri Rust shell
│   ├── src/main.rs
│   ├── Cargo.toml
│   └── tauri.conf.json
├── src/                           # React/TypeScript frontend
│   ├── main.tsx
│   ├── App.tsx                    # Router + app shell
│   ├── lib/
│   │   ├── api.ts                 # fetch wrapper for AnswerGuard REST API
│   │   └── store.ts              # Tauri store wrapper (config persistence)
│   ├── screens/
│   │   ├── ConnectScreen.tsx
│   │   ├── connector/
│   │   │   ├── DetailsScreen.tsx
│   │   │   ├── SchemaScreen.tsx
│   │   │   └── ReviewScreen.tsx
│   │   ├── ImportScreen.tsx
│   │   └── DataScreen.tsx
│   ├── components/
│   │   ├── AppShell.tsx
│   │   ├── ProgressCard.tsx
│   │   ├── QAPairList.tsx
│   │   ├── QAPairDetail.tsx
│   │   └── FieldMappingForm.tsx
│   └── types/index.ts
├── package.json
├── tsconfig.json
└── tailwind.config.js
```

---

## Key Implementation Notes

### Schema discovery endpoint
`POST /v1/sources/discover-schema` reuses `BigQuerySourceAdapter.get_schema()`. Creates a minimal `SourceConnector` value object from the request (no field mapping needed) and calls the existing port. Returns `{ columns: [{name, type}] }`.

### QA pairs list endpoint
`GET /v1/qa-pairs` adds `list_paginated(page, page_size, source_system_id?, search?)` to `QAPairRepository`. SQL implementation uses `LIKE` for search on question/answer text. Returns total count for pagination controls.

### Tauri app initialisation
On launch, Tauri reads stored config. If no server URL or health check fails → route to `/connect`. Otherwise route to last active screen. Config persisted as JSON via `@tauri-apps/plugin-store`.

### Import progress polling
`ImportScreen` uses React Query `refetchInterval: 3000` while status is `RUNNING` or `RESUMED`. Polling stops automatically on `COMPLETED` or `FAILED`.

### Field mapping UX
`SchemaScreen` renders discovered columns on the left with type badges, dropdowns on the right for each AnswerGuard field. "Question" and "Answer" dropdowns are required — the next button is disabled until both are selected.

---

## Verification

1. **Backend unit tests**: `pytest tests/unit/` — new use cases with mocked ports
2. **Backend integration**: `pytest tests/integration/` — `list_paginated()` against SQLite in-memory
3. **Schema discovery**: Valid BigQuery credentials in desktop app → column list appears within 10 seconds
4. **Field mapping**: Select required columns → config persists after app restart
5. **Import flow**: Trigger import → progress updates every ~3 seconds → completion summary correct
6. **Data view**: Records visible, search filters work, detail panel shows full content
7. **Cross-platform**: Build runs identically on macOS and Windows
