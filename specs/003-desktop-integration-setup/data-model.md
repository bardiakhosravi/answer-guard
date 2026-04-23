# Data Model: Desktop App — Integration Setup

**Feature**: 003-desktop-integration-setup
**Date**: 2026-04-22

---

## Local App State (persisted to disk via Tauri store)

### ServerConfig

Persisted. Stores the user's AnswerGuard connection.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `url` | string | ✅ | AnswerGuard server URL (e.g. `http://localhost:8000`) |
| `lastVerifiedAt` | ISO string | ❌ | Timestamp of last successful health check |

---

### SourceConnectorConfig

Persisted. Stores the full BigQuery source configuration including field mapping.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `sourceSystemId` | string | ✅ | User-chosen identifier for this source |
| `gcpProjectId` | string | ✅ | GCP project ID |
| `datasetId` | string | ✅ | BigQuery dataset ID |
| `tableId` | string | ✅ | BigQuery table or view ID |
| `credentialsPath` | string | ❌ | Absolute path to service account JSON key file |
| `rowFilter` | string | ❌ | Optional BigQuery WHERE clause |
| `pageSize` | integer | ❌ | Rows per batch; default 5000 |
| `fieldMapping` | FieldMapping | ✅ | Column mapping configuration |

---

### FieldMapping

Embedded in `SourceConnectorConfig`. Maps source columns to AnswerGuard fields.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `questionColumn` | string | ✅ | Source column for question text |
| `answerColumn` | string | ✅ | Source column for answer text |
| `timestampColumn` | string | ❌ | Source column for original timestamp |
| `externalIdColumn` | string | ❌ | Source column for external record ID |
| `metadataColumns` | `Record<string, string>` | ❌ | Map of AnswerGuard key → source column |

---

## Transient App State (in-memory only)

### DiscoveredColumn

Returned by `POST /v1/sources/discover-schema`. Displayed in field mapping dropdowns.

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Column name |
| `type` | string | BigQuery data type (e.g. `STRING`, `TIMESTAMP`, `INTEGER`) |

---

### ImportJob

Tracks a running or completed historical import. Sourced by polling `GET /v1/ingest/status/{run_id}`.

| Field | Type | Description |
|-------|------|-------------|
| `runId` | string | UUID of the ingestion run |
| `status` | `RUNNING` \| `COMPLETED` \| `FAILED` \| `RESUMED` | Current state |
| `recordsProcessed` | integer | Successfully ingested records |
| `recordsSkipped` | integer | Records skipped (duplicates, missing fields) |
| `lastCheckpoint` | integer \| null | Last committed batch index |
| `startedAt` | ISO string | When the run began |
| `completedAt` | ISO string \| null | When the run ended |
| `errors` | `{ index: number, reason: string }[]` | Per-record skip reasons |

---

### QAPairRecord

A single ingested Q&A pair as returned by `GET /v1/qa-pairs` (new list endpoint).

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Internal AnswerGuard UUID |
| `questionText` | string | The user's question |
| `answerText` | string | The agent's response |
| `sourceSystemId` | string | Which source system produced this pair |
| `capturedAt` | ISO string | When it was stored in AnswerGuard |
| `sourceTimestamp` | ISO string \| null | Original timestamp from source |
| `ingestionMethod` | `HISTORICAL_IMPORT` \| `RUNTIME_CAPTURE` | How it arrived |
| `externalId` | string \| null | Source system record ID |
| `metadata` | `Record<string, string>` | Developer-provided key-value pairs |

---

## New Backend Endpoints Required

### POST /v1/sources/discover-schema

Takes BigQuery connection details and returns all column names and types from the target table.

**Request:**
```json
{
  "gcp_project_id": "my-project",
  "dataset_id": "agent_logs",
  "table_id": "qa_responses",
  "credentials_path": "/path/to/key.json"
}
```

**Response — 200 OK:**
```json
{
  "columns": [
    { "name": "user_question", "type": "STRING" },
    { "name": "agent_response", "type": "STRING" },
    { "name": "created_at", "type": "TIMESTAMP" },
    { "name": "session_id", "type": "STRING" }
  ]
}
```

**Error responses:**
| Status | When |
|--------|------|
| `400` | Missing required fields |
| `502` | BigQuery connection failed (invalid credentials, table not found) |

---

### GET /v1/qa-pairs

Returns a paginated list of ingested Q&A pairs for the data view.

**Query parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `page` | integer | ❌ | `1` | Page number (1-indexed) |
| `page_size` | integer | ❌ | `50` | Records per page |
| `source_system_id` | string | ❌ | all | Filter by source |
| `search` | string | ❌ | none | Full-text filter on question + answer |

**Response — 200 OK:**
```json
{
  "total": 125430,
  "page": 1,
  "page_size": 50,
  "items": [
    {
      "id": "b2c3d4e5-...",
      "question_text": "How do I get a refund?",
      "answer_text": "Go to Settings > Billing > Request Refund.",
      "source_system_id": "prod-agent-v2",
      "captured_at": "2026-04-22T10:30:00Z",
      "ingestion_method": "HISTORICAL_IMPORT",
      "metadata": { "topic": "billing" }
    }
  ]
}
```
