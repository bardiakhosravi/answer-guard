# Documentation Structure Contract

**Feature**: 002-developer-docs
**Date**: 2026-04-22

This contract defines the page structure and sidebar navigation of the AnswerGuard developer documentation site (Docusaurus). Every page listed here must exist and be reachable from the sidebar or top navigation.

---

## Sidebar Navigation (`website/sidebars.ts`)

```typescript
const sidebars = {
  docs: [
    { type: 'doc', id: 'intro', label: 'Overview' },
    { type: 'doc', id: 'quickstart', label: 'Quickstart' },
    {
      type: 'category',
      label: 'Integration Guide',
      items: [
        'integration/index',
        'integration/bigquery',
        'integration/historical-import',
        'integration/python-sdk',
        'integration/typescript-sdk',
        'integration/verification',
      ],
    },
    {
      type: 'category',
      label: 'Reference',
      items: [
        'reference/api',
        'reference/configuration',
      ],
    },
    { type: 'doc', id: 'troubleshooting', label: 'Troubleshooting' },
  ],
};
```

---

## Page Contracts

### `website/docs/intro.md` — Overview

Must contain:
- What AnswerGuard is (1 paragraph, non-technical)
- Who it is for (primary audience: developers integrating agent systems)
- The problem it solves
- Data flow description or diagram: `agent system → AnswerGuard → PM review interface`
- Quick links: Quickstart and Integration Guide

Must NOT contain:
- Code samples or installation instructions

---

### `website/docs/quickstart.md` — Quickstart

Must contain:
- **Prerequisites**: Python 3.11+, pip, git — no Docker required
- **Step 1**: Clone the repository
- **Step 2**: Create virtual environment and install dependencies
- **Step 3**: Copy `.env.example` to `.env` (SQLite `DATABASE_URL` pre-set)
- **Step 4**: Run Alembic database migrations
- **Step 5**: Start the server (`uvicorn main:app --port 8080`)
- **Step 6**: Verify with `GET /health`
- **Step 7**: Send a test capture via `POST /v1/capture` and confirm it appears via `GET /v1/ingest/status`
- Time estimate callout: "This quickstart takes under 30 minutes"
- Next steps: link to Integration Guide

Must NOT contain:
- PostgreSQL or Docker instructions

---

### `website/docs/integration/index.md` — Integration Overview

Must contain:
- The two integration tasks: (1) historical import from BigQuery, (2) runtime capture via SDK
- Order recommendation: set up historical import first, then SDK
- Prerequisites: existing agent system, BigQuery dataset with Q&A data

---

### `website/docs/integration/bigquery.md` — BigQuery Source Configuration

Must contain:
- GCP prerequisites (project ID, dataset, table, service account with BigQuery Data Viewer role)
- Authentication options: service account JSON key file vs Application Default Credentials (ADC)
- All `SourceConnector` configuration fields with types, required/optional, defaults, and examples
- `FieldMapping` configuration: mapping source columns to AnswerGuard fields
- How to verify the connection before running an import (schema validation endpoint or dry-run)

---

### `website/docs/integration/historical-import.md` — Historical Import

Must contain:
- `POST /v1/ingest/import` — full request body with every field documented
- How to monitor import progress: `GET /v1/ingest/status/{run_id}`
- Understanding `records_processed` vs `records_skipped`
- How to resume a FAILED import (re-send same request — auto-resumes from checkpoint)
- Skip-and-log behaviour: what it means, how to inspect skipped records in the status endpoint

---

### `website/docs/integration/python-sdk.md` — Python SDK

Must contain:
- Installation: `pip install answerguard-sdk` (or local install path during development)
- Minimal working example (≤5 lines)
- `capture()` — fire-and-forget, never raises, returns immediately
- `capture_sync()` — blocking, raises on failure, returns `CaptureResult`
- Passing `metadata` dict
- Constructor options: `endpoint`, `source_system_id`, `timeout_ms`
- Fail-open explained: what happens when the AnswerGuard server is unreachable

---

### `website/docs/integration/typescript-sdk.md` — TypeScript SDK

Must contain:
- Installation: `npm install @answerguard/sdk`
- Minimal working example (≤5 lines)
- `capture()` — fire-and-forget (no await), logs errors to `console.error`
- `captureAsync()` — awaitable, throws on failure
- Passing `metadata` object
- Constructor options: `endpoint`, `sourceSystemId`, `timeoutMs`
- Fail-open explained

---

### `website/docs/integration/verification.md` — Verify Integration

Must contain:
- Using `GET /v1/ingest/status` to confirm records are being stored
- Sample response showing a healthy integration
- What `runtime_captures_last_24h` means
- How to check that the historical import completed without errors

---

### `website/docs/reference/api.md` — API Reference

Must document every endpoint:

| Endpoint | Description |
|----------|-------------|
| `POST /v1/ingest/import` | Trigger historical bulk import |
| `GET /v1/ingest/status` | Overall ingestion summary |
| `GET /v1/ingest/status/{run_id}` | Single import run detail |
| `POST /v1/capture` | Capture a single Q&A pair at runtime |
| `GET /health` | Health check |

For each endpoint, document:
- Method + path
- Description
- Every request field: name, type, required/optional, default, description
- Every response field: name, type, description
- Example request body (JSON)
- Example response body (JSON)
- Error responses: HTTP status code, error key, description

---

### `website/docs/reference/configuration.md` — Configuration Reference

Must document every configuration item grouped by category:

**Database**: `DATABASE_URL` (type, required, examples for SQLite and PostgreSQL)
**BigQuery**: `GCP_PROJECT_ID`, `GOOGLE_APPLICATION_CREDENTIALS`, `BIGQUERY_PAGE_SIZE`
**Server**: port, host (from `uvicorn` args)
**Python SDK**: `endpoint`, `source_system_id`, `timeout_ms`
**TypeScript SDK**: `endpoint`, `sourceSystemId`, `timeoutMs`

For each item: name, type, required/optional, default, description, example value.

---

### `website/docs/troubleshooting.md` — Troubleshooting

Must document at minimum these 5 errors, each with: symptom/exact error message, cause, resolution steps:

1. `GOOGLE_APPLICATION_CREDENTIALS` file not found or permission denied
2. `FieldMappingValidationError` — column not found in source table
3. `409 IMPORT_ALREADY_RUNNING` — import already in progress
4. `OperationalError: no such table` — database migration not applied
5. SDK capture silently not arriving — how to switch to `capture_sync()` to see errors
