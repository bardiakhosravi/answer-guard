---
sidebar_position: 2
---

# BigQuery Source Configuration

AnswerGuard reads your historical Q&A data from a BigQuery table. This page covers everything you need to set up the connection.

## GCP prerequisites

Before you start, you need:

- **GCP project ID** — the project that contains your BigQuery dataset
- **BigQuery dataset and table** — the table containing your Q&A data (tabular format, one row per Q&A pair)
- **Service account** with the `BigQuery Data Viewer` role on your dataset

## Authentication

AnswerGuard supports two authentication methods:

### Option A: Service account JSON key file (recommended for self-hosted)

1. Create a service account in your GCP project
2. Grant it the `BigQuery Data Viewer` role on your dataset
3. Download the JSON key file
4. Set the path in your `.env`:

```env
GOOGLE_APPLICATION_CREDENTIALS=/path/to/your/service-account-key.json
```

### Option B: Application Default Credentials (ADC)

If you're running AnswerGuard on Google Cloud infrastructure (Cloud Run, GKE, Compute Engine), the instance's default service account is used automatically. Leave `GOOGLE_APPLICATION_CREDENTIALS` empty.

## Source connector configuration

When triggering an import, you provide a `SourceConnector` configuration in the request body:

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `source_system_id` | string | ✅ | — | Your identifier for this source (e.g. `"prod-agent-v2"`) |
| `gcp_project_id` | string | ✅ | — | Your GCP project ID |
| `dataset_id` | string | ✅ | — | BigQuery dataset ID |
| `table_id` | string | ✅ | — | BigQuery table or view ID |
| `credentials_path` | string | ❌ | uses ADC | Absolute path to service account JSON key |
| `field_mapping` | object | ✅ | — | Column mapping (see below) |
| `row_filter` | string | ❌ | none | BigQuery WHERE clause (e.g. `"created_at > '2024-01-01'"`) |
| `page_size` | integer | ❌ | `5000` | Rows per batch during import |

## Field mapping

The `field_mapping` object tells AnswerGuard which columns in your BigQuery table correspond to AnswerGuard fields:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `question_column` | string | ✅ | Column containing the user's question |
| `answer_column` | string | ✅ | Column containing the agent's response |
| `timestamp_column` | string | ❌ | Column containing the original timestamp |
| `external_id_column` | string | ❌ | Column containing a unique ID from your source system |
| `metadata_columns` | object | ❌ | Map of AnswerGuard key → source column name |

### Example field mapping

If your BigQuery table has columns `user_question`, `agent_response`, `created_at`, `session_id`, `topic_category`:

```json
{
  "question_column": "user_question",
  "answer_column": "agent_response",
  "timestamp_column": "created_at",
  "external_id_column": null,
  "metadata_columns": {
    "session_id": "session_id",
    "topic": "topic_category"
  }
}
```

## Full example: triggering an import

```bash
curl -X POST http://localhost:8080/v1/ingest/import \
  -H "Content-Type: application/json" \
  -d '{
    "source_system_id": "prod-agent-v2",
    "gcp_project_id": "my-gcp-project",
    "dataset_id": "agent_logs",
    "table_id": "qa_responses",
    "credentials_path": "/secrets/bq-key.json",
    "field_mapping": {
      "question_column": "user_question",
      "answer_column": "agent_response",
      "timestamp_column": "created_at",
      "metadata_columns": {
        "topic": "question_category"
      }
    },
    "row_filter": "created_at > '\''2024-01-01'\''",
    "page_size": 5000
  }'
```

If the field mapping is invalid (a column doesn't exist), you'll receive a `400` response identifying the misconfigured field before the import begins. See [Historical Import →](/docs/integration/historical-import) for monitoring the import progress.
