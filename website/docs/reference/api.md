---
sidebar_position: 1
---

# API Reference

All endpoints are prefixed with the server URL (default: `http://localhost:8080`).

---

## POST /v1/ingest/import

Trigger a historical bulk import from a BigQuery source.

### Request body

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `source_system_id` | string | ✅ | — | Your identifier for this source (e.g. `"prod-agent-v2"`) |
| `gcp_project_id` | string | ✅ | — | GCP project ID containing the BigQuery dataset |
| `dataset_id` | string | ✅ | — | BigQuery dataset ID |
| `table_id` | string | ✅ | — | BigQuery table or view ID |
| `credentials_path` | string | ❌ | uses ADC | Absolute path to service account JSON key file |
| `field_mapping` | object | ✅ | — | Column mapping (see below) |
| `row_filter` | string | ❌ | none | BigQuery WHERE clause applied to the source table |
| `page_size` | integer | ❌ | `5000` | Rows per batch during import |

**`field_mapping` object:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `question_column` | string | ✅ | Source column for question text |
| `answer_column` | string | ✅ | Source column for answer text |
| `timestamp_column` | string | ❌ | Source column for original timestamp |
| `external_id_column` | string | ❌ | Source column for external record ID |
| `metadata_columns` | object | ❌ | `{ "answerguard_key": "source_column" }` map |

### Example request

```json
{
  "source_system_id": "prod-agent-v2",
  "gcp_project_id": "my-gcp-project",
  "dataset_id": "agent_logs",
  "table_id": "qa_responses",
  "credentials_path": "/secrets/bq-key.json",
  "field_mapping": {
    "question_column": "user_question",
    "answer_column": "agent_response",
    "timestamp_column": "created_at",
    "metadata_columns": { "topic": "question_category" }
  },
  "page_size": 5000
}
```

### Response — 202 Accepted

```json
{
  "ingestion_run_id": "a1b2c3d4-...",
  "status": "RUNNING",
  "message": "Import started. Poll /v1/ingest/status/:run_id for progress."
}
```

### Error responses

| Status | Error key | When |
|--------|-----------|------|
| `400` | `INVALID_FIELD_MAPPING` | A mapped column doesn't exist in the source table |
| `409` | `IMPORT_ALREADY_RUNNING` | An import is already running for this `source_system_id` |

---

## GET /v1/ingest/status

Overall ingestion summary across all sources.

### Query parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `source_system_id` | string | ❌ | Filter results to a specific source |

### Example request

```bash
curl http://localhost:8080/v1/ingest/status
```

### Response — 200 OK

```json
{
  "total_qa_pairs": 125430,
  "sources": [
    {
      "source_system_id": "prod-agent-v2",
      "total_records": 125430,
      "last_ingested_at": "2026-04-22T10:30:00Z",
      "runtime_captures_last_24h": 847,
      "last_import_run": {
        "run_id": "a1b2c3d4-...",
        "status": "COMPLETED",
        "records_processed": 100000,
        "records_skipped": 23,
        "started_at": "2026-04-22T08:00:00Z",
        "completed_at": "2026-04-22T08:12:00Z"
      }
    }
  ]
}
```

---

## GET /v1/ingest/status/:run_id

Detailed status for a specific import run.

### Path parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `run_id` | string (UUID) | The `ingestion_run_id` returned by `POST /v1/ingest/import` |

### Response — 200 OK

```json
{
  "ingestion_run_id": "a1b2c3d4-...",
  "source_system_id": "prod-agent-v2",
  "status": "COMPLETED",
  "started_at": "2026-04-22T09:00:00Z",
  "completed_at": "2026-04-22T09:12:00Z",
  "records_processed": 100000,
  "records_skipped": 23,
  "last_checkpoint": 100023,
  "errors": [
    { "index": 1203, "reason": "missing answer_text" },
    { "index": 8847, "reason": "duplicate record" }
  ]
}
```

`status` is one of: `RUNNING`, `COMPLETED`, `FAILED`, `RESUMED`

### Error responses

| Status | When |
|--------|------|
| `404` | No run found with the given `run_id` |

---

## POST /v1/capture

Capture a single Q&A pair at runtime. Used by the SDK internally and available directly.

### Request body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `question` | string | ✅ | The user's question |
| `answer` | string | ✅ | The agent's response |
| `source_system_id` | string | ✅ | Identifies the agent system |
| `metadata` | object | ❌ | Arbitrary string key-value pairs |

### Example request

```json
{
  "question": "How do I get a refund?",
  "answer": "To request a refund, go to Settings > Billing > Request Refund.",
  "source_system_id": "prod-agent-v2",
  "metadata": {
    "topic": "billing",
    "session_id": "sess_abc123"
  }
}
```

### Response — 201 Created

```json
{
  "qa_pair_id": "b2c3d4e5-...",
  "captured_at": "2026-04-22T10:30:00Z"
}
```

### Error responses

| Status | When |
|--------|------|
| `400` | Empty `question` or `answer` |
| `409` | Duplicate — a pair with identical content and `source_system_id` already exists; returns existing `qa_pair_id` |

---

## POST /v1/response-feedback

Submit PM feedback about an agent answer.

### Request body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `source_qa_pair_id` | string (UUID) | ✅ | ID of the source `QAPair` the feedback is about |
| `excerpt` | string | ✅ | The text the PM was commenting on — either the selected passage or the full answer |
| `problem` | string | ✅ | What's wrong with the response |
| `desired_behavior` | string | ✅ | How the agent should behave instead |
| `span_start` | integer | ❌ | Character offset where the highlight begins (both `span_start` and `span_end` must be provided together, or both omitted) |
| `span_end` | integer | ❌ | Character offset where the highlight ends (exclusive) |

### Example request

```json
{
  "source_qa_pair_id": "b2c3d4e5-6789-4abc-8def-0123456789ab",
  "excerpt": "To request a refund, go to Settings > Billing.",
  "problem": "The response is too vague — it doesn't mention that refunds are only available within 30 days.",
  "desired_behavior": "Always include the 30-day refund policy window when discussing refunds.",
  "span_start": 0,
  "span_end": 47
}
```

### Response — 201 Created

```json
{
  "id": "f1e2d3c4-...",
  "source_qa_pair_id": "b2c3d4e5-...",
  "excerpt": "To request a refund, go to Settings > Billing.",
  "span_start": 0,
  "span_end": 47,
  "problem": "The response is too vague...",
  "desired_behavior": "Always include the 30-day refund policy...",
  "created_at": "2026-04-23T14:00:00Z",
  "updated_at": "2026-04-23T14:00:00Z"
}
```

### Error responses

| Status | When |
|--------|------|
| `400` | Empty required field; one-sided span (only `span_start` or `span_end` provided) |

---

## GET /v1/response-feedback

List all response feedback records, paginated. Ordered by `created_at` descending.

### Query parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page` | integer | `1` | Page number (1-indexed) |
| `page_size` | integer | `50` | Records per page (max `500`) |
| `search` | string | none | Case-insensitive search across `excerpt`, `problem`, and `desired_behavior` |

### Response — 200 OK

```json
{
  "total": 342,
  "page": 1,
  "page_size": 50,
  "items": [
    {
      "id": "f1e2d3c4-...",
      "source_qa_pair_id": "b2c3d4e5-...",
      "excerpt": "...",
      "span_start": 0,
      "span_end": 47,
      "problem": "...",
      "desired_behavior": "...",
      "created_at": "2026-04-23T14:00:00Z",
      "updated_at": "2026-04-23T14:00:00Z"
    }
  ]
}
```

---

## GET /v1/response-feedback/:feedback_id

Retrieve a single feedback record.

### Response — 200 OK

Same shape as items in the list response above.

### Error responses

| Status | When |
|--------|------|
| `404` | No record with the given ID |

---

## PATCH /v1/response-feedback/:feedback_id

Update `problem` and/or `desired_behavior` on an existing feedback record. Excerpt and span are immutable.

### Request body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `problem` | string | ❌ | New problem text. At least one of `problem` or `desired_behavior` must be provided |
| `desired_behavior` | string | ❌ | New desired-behavior text |

### Response — 200 OK

The updated record (same shape as GET).

### Error responses

| Status | When |
|--------|------|
| `400` | Both fields omitted; empty value supplied |
| `404` | No record with the given ID |

---

## DELETE /v1/response-feedback/:feedback_id

Idempotent delete. Returns 204 whether or not the record existed.

### Response — 204 No Content

---

## GET /health

Health check.

### Response — 200 OK

```json
{ "status": "ok" }
```
