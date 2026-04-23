# Research: Desktop App — Integration Setup

**Feature**: 003-desktop-integration-setup
**Date**: 2026-04-22

---

## Decision 1: Desktop Framework — Tauri v2 (Rust + React/TypeScript)

**Decision**: Use Tauri v2 with a React/TypeScript frontend.

**Rationale**:
- **Bundle size**: 2–10MB vs Electron's 150–200MB — critical for developer tool adoption
- **TypeScript reuse**: The existing project already uses TypeScript for the SDK and Docusaurus; the Tauri frontend is standard React/TypeScript
- **REST API calls**: Standard `fetch` from the React layer — identical to calling any REST endpoint from a web app
- **Native file picker**: `@tauri-apps/plugin-dialog` — one line to open a native OS file picker for the GCP credentials JSON
- **Local config persistence**: `@tauri-apps/plugin-store` — JSON file on disk, transparent to the user
- **Wizard UI**: Full React ecosystem available (React Hook Form, React Query for polling, etc.)

**Alternatives rejected**:
- **Electron**: 150–200MB bundle is unjustifiable for a developer tool. Feature parity but unacceptable weight.
- **Flutter**: Requires Dart, no TypeScript leverage, overkill (mobile-ready) for desktop-only tool.

---

## Decision 2: Backend addition — `POST /v1/sources/discover-schema`

**Decision**: Add one new AnswerGuard backend endpoint for schema discovery.

**Rationale**: The spec assumed no new backend endpoints were needed, but schema discovery — fetching column names from the BigQuery table — requires calling `BigQuerySourcePort.get_schema()` on the server side. The BigQuery client credentials and logic already live in the backend. Calling BigQuery directly from the desktop app would duplicate auth logic and expose GCP credentials handling in two places.

The new endpoint is thin: it accepts the same connection fields as the import endpoint and returns a list of column names. The implementation reuses the existing `BigQuerySourceAdapter.get_schema()` method.

**New endpoint**: `POST /v1/sources/discover-schema`
```json
Request:  { gcp_project_id, dataset_id, table_id, credentials_path? }
Response: { columns: [{ name, type }] }
```

---

## Decision 3: Local configuration persistence

**Decision**: Use Tauri's `@tauri-apps/plugin-store` to persist config as a JSON file in the OS-appropriate app data directory (`~/.config/answerguard/config.json` on macOS/Linux, `%APPDATA%\answerguard\config.json` on Windows).

**Stored**: server URL, source connector config (project, dataset, table, credentials path, field mapping). Nothing sensitive — credentials_path is a file path, not the key itself.

---

## Decision 4: Import progress polling

**Decision**: The desktop app polls `GET /v1/ingest/status/{run_id}` every 3 seconds during an active import. No WebSocket or server-sent events needed for v1.

**Rationale**: 3-second polling meets SC-003 (updates visible within 10 seconds of each batch). The server already supports this endpoint. Polling is simpler than WebSocket for v1 and avoids connection management complexity.

---

## Decision 5: App structure

**Decision**: Single Tauri window, React Router for screen navigation. Five screens form a progressive flow with a persistent sidebar showing connection and import status.

```
App shell (sidebar: server status, nav)
├── /connect          — Server connection setup
├── /connector        — BigQuery source config + field mapping wizard
│   ├── /connector/details    — Connection details form
│   ├── /connector/schema     — Schema discovery + field mapping
│   └── /connector/review     — Mapping review + save
├── /import           — Import trigger + live progress
└── /data             — Ingested Q&A pairs (list + detail panel)
```
