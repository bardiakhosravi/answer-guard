---
sidebar_position: 3
---

# Historical Import

The historical import reads your existing Q&A data from BigQuery and loads it into AnswerGuard's database. This is a one-time operation — after it completes, all new data flows through the [runtime SDK](/docs/integration/python-sdk).

## Trigger the import

```bash
curl -X POST http://localhost:8080/v1/ingest/import \
  -H "Content-Type: application/json" \
  -d '{
    "source_system_id": "prod-agent-v2",
    "gcp_project_id": "my-gcp-project",
    "dataset_id": "agent_logs",
    "table_id": "qa_responses",
    "field_mapping": {
      "question_column": "user_question",
      "answer_column": "agent_response"
    }
  }'
```

A successful response returns `202 Accepted` with a run ID:

```json
{
  "ingestion_run_id": "a1b2c3d4-...",
  "status": "RUNNING",
  "message": "Import started. Poll /v1/ingest/status/{run_id} for progress."
}
```

## Monitor progress

Poll the status endpoint with your run ID:

```bash
curl http://localhost:8080/v1/ingest/status/a1b2c3d4-...
```

Response during import:

```json
{
  "ingestion_run_id": "a1b2c3d4-...",
  "source_system_id": "prod-agent-v2",
  "status": "RUNNING",
  "started_at": "2026-04-22T09:00:00Z",
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

When complete, `status` changes to `"COMPLETED"`.

## Understanding the results

| Field | Meaning |
|-------|---------|
| `records_processed` | Q&A pairs successfully stored in AnswerGuard |
| `records_skipped` | Rows skipped due to missing required fields or duplicates |
| `errors` | Details for each skipped row (index in source table + reason) |

**Skip-and-log behaviour**: AnswerGuard never stops an import due to individual bad rows. Rows with missing `question` or `answer` text are skipped and logged. You can inspect all skipped rows in the `errors` array.

## Resuming a failed import

If the import fails mid-way (network issue, server restart), re-send the exact same request. AnswerGuard automatically detects the `FAILED` run for the same `source_system_id` and resumes from the last checkpoint — no records are re-imported.

```bash
# Same request as before — AnswerGuard resumes automatically
curl -X POST http://localhost:8080/v1/ingest/import \
  -H "Content-Type: application/json" \
  -d '{ ... same body ... }'
```

The resumed run's status changes to `"RESUMED"` and then `"COMPLETED"` when done.

## Next steps

Once the import is complete, add [runtime capture via SDK](/docs/integration/python-sdk) so new responses are captured automatically going forward.
