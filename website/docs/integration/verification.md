---
sidebar_position: 6
---

# Verify Your Integration

Once you've completed the historical import and added SDK capture, use the status endpoint to confirm everything is working correctly.

## Check overall ingestion status

```bash
curl http://localhost:8080/v1/ingest/status
```

A healthy integration looks like this:

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

## What each field means

| Field | Meaning |
|-------|---------|
| `total_qa_pairs` | Total Q&A pairs stored across all sources |
| `sources[].total_records` | Total pairs for this source system |
| `sources[].runtime_captures_last_24h` | New pairs captured by SDK in the last 24 hours |
| `sources[].last_ingested_at` | Timestamp of the most recent record |
| `sources[].last_import_run.status` | `COMPLETED`, `RUNNING`, `FAILED`, or `RESUMED` |

## Signs of a healthy integration

- `runtime_captures_last_24h` is non-zero if your agent system is handling traffic
- `last_import_run.status` is `"COMPLETED"` (not `"FAILED"` or `"RUNNING"` for a long time)
- `last_import_run.records_skipped` is a small fraction of `records_processed` (some skips are normal)

## Signs of a problem

| Symptom | Likely cause |
|---------|-------------|
| `runtime_captures_last_24h` is 0 despite traffic | SDK not integrated, wrong `endpoint`, or wrong `source_system_id` |
| `last_import_run.status` is `"FAILED"` | BigQuery connection issue; re-trigger the import to resume |
| `last_import_run.status` is `"RUNNING"` for hours | Server restarted mid-import; re-trigger to resume |

See the [Troubleshooting](/docs/troubleshooting) guide for specific error resolutions.
