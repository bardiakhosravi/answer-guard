# API Contracts: Q&A Response Ingestion

**Feature**: 001-qa-response-ingestion
**Date**: 2026-04-21

All endpoints are prefixed with `/v1`.

---

## POST /v1/ingest/import

Triggers a historical bulk import from the configured BigQuery source.

### Request
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
    "external_id_column": "response_id",
    "metadata_columns": {
      "topic": "question_category",
      "session_id": "session_id"
    }
  },
  "row_filter": "created_at > '2024-01-01'",
  "page_size": 5000
}
```

### Response 202 Accepted
```json
{
  "ingestion_run_id": "a1b2c3d4-...",
  "status": "RUNNING",
  "message": "Import started. Poll /v1/ingest/status/{run_id} for progress."
}
```

### Response 400 Bad Request (invalid field mapping)
```json
{
  "error": "INVALID_FIELD_MAPPING",
  "detail": "Column 'user_question' does not exist in table 'agent_logs.qa_responses'. Available columns: [question, answer, created_at]"
}
```

### Response 409 Conflict (import already running)
```json
{
  "error": "IMPORT_ALREADY_RUNNING",
  "detail": "An import for source_system_id 'prod-agent-v2' is already in progress. Run ID: a1b2c3d4-..."
}
```

---

## POST /v1/capture

Captures a single Q&A pair at runtime (SDK and direct API use).

### Request
```json
{
  "question": "How do I get a refund?",
  "answer": "To request a refund, go to Settings > Billing > Request Refund.",
  "source_system_id": "prod-agent-v2",
  "metadata": {
    "topic": "billing",
    "session_id": "sess_abc123",
    "user_segment": "enterprise"
  }
}
```

### Response 201 Created
```json
{
  "qa_pair_id": "b2c3d4e5-...",
  "captured_at": "2026-04-21T10:30:00Z"
}
```

### Response 409 Conflict (duplicate)
```json
{
  "error": "DUPLICATE_RECORD",
  "detail": "A Q&A pair with the same content already exists. ID: b2c3d4e5-..."
}
```

---

## GET /v1/ingest/status/{run_id}

Returns status for a specific historical import run.

### Response 200
```json
{
  "ingestion_run_id": "a1b2c3d4-...",
  "source_system_id": "prod-agent-v2",
  "status": "RUNNING",
  "started_at": "2026-04-21T09:00:00Z",
  "completed_at": null,
  "records_processed": 45000,
  "records_skipped": 12,
  "last_checkpoint": 45000,
  "errors": [
    {"index": 1203, "reason": "missing answer_text"},
    {"index": 8847, "reason": "duplicate record"}
  ]
}
```

### Response 404
```json
{
  "error": "NOT_FOUND",
  "detail": "No ingestion run found with ID a1b2c3d4-..."
}
```

---

## GET /v1/ingest/status

Returns overall ingestion summary across all sources.

### Response 200
```json
{
  "total_qa_pairs": 125430,
  "sources": [
    {
      "source_system_id": "prod-agent-v2",
      "total_records": 125430,
      "last_ingested_at": "2026-04-21T10:30:00Z",
      "last_import_run": {
        "run_id": "a1b2c3d4-...",
        "status": "COMPLETED",
        "records_processed": 100000,
        "records_skipped": 23,
        "started_at": "2026-04-20T08:00:00Z",
        "completed_at": "2026-04-20T08:12:00Z"
      },
      "runtime_captures_last_24h": 25430
    }
  ]
}
```

---

## SDK Contract (TypeScript)

```typescript
interface AnswerGuardConfig {
  endpoint: string;          // e.g., 'http://localhost:8080'
  sourceSystemId: string;
  timeoutMs?: number;        // default: 2000ms; 0 = no timeout
}

interface CaptureOptions {
  metadata?: Record<string, string>;
}

class AnswerGuard {
  constructor(config: AnswerGuardConfig);

  // Fire-and-forget: never throws, never awaits network
  capture(question: string, answer: string, options?: CaptureOptions): void;

  // Async version for callers who want confirmation
  captureAsync(question: string, answer: string, options?: CaptureOptions): Promise<{ qa_pair_id: string }>;
}
```

## SDK Contract (Python)

```python
class AnswerGuard:
    def __init__(self, endpoint: str, source_system_id: str, timeout_ms: int = 2000) -> None: ...

    # Fire-and-forget: dispatches to background thread, never raises
    def capture(self, question: str, answer: str, metadata: dict[str, str] | None = None) -> None: ...

    # Blocking version for callers who want confirmation
    def capture_sync(self, question: str, answer: str, metadata: dict[str, str] | None = None) -> CaptureResult: ...
```
