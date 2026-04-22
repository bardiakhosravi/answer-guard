# Data Model: Q&A Response Ingestion & Storage

**Feature**: 001-qa-response-ingestion
**Date**: 2026-04-21

---

## Entities

### QAPair (Aggregate Root)

The core record. Represents one question posed to the agent system and the response it generated.

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| `id` | UUID | PK, auto-generated | AnswerGuard's internal ID |
| `question_text` | Text | NOT NULL | Full question text, no length limit |
| `answer_text` | Text | NOT NULL | Full answer text, no length limit |
| `captured_at` | DateTime (UTC) | NOT NULL | When this record was created in AnswerGuard |
| `source_timestamp` | DateTime (UTC) | nullable | Timestamp from the source system, if available |
| `source_system_id` | String(255) | NOT NULL | Developer-provided identifier for the source agent system |
| `external_id` | String(255) | nullable, indexed | Original ID from the source database, if provided |
| `source_hash` | String(64) | UNIQUE, NOT NULL | SHA-256 hash of `question_text + answer_text + source_system_id` — deduplication key |
| `ingestion_method` | Enum | NOT NULL | `HISTORICAL_IMPORT` or `RUNTIME_CAPTURE` |
| `ingestion_run_id` | UUID | nullable, FK → IngestionRun | Set only for historical imports |
| `metadata` | JSON | nullable | Extensible map for developer-provided fields (topic, session_id, user_segment, etc.) |

**Invariants:**
- `source_hash` must be unique — inserting a duplicate is a no-op (skip and log)
- `question_text` and `answer_text` must be non-empty strings
- `ingestion_method` = `HISTORICAL_IMPORT` implies `ingestion_run_id` is set

**State transitions**: QAPair is immutable after creation. No state machine.

---

### IngestionRun (Entity)

Represents one execution of the historical import process. Tracks progress for resumability.

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| `id` | UUID | PK, auto-generated | |
| `source_system_id` | String(255) | NOT NULL | Links to the SourceConnector config |
| `started_at` | DateTime (UTC) | NOT NULL | |
| `completed_at` | DateTime (UTC) | nullable | Set when status = COMPLETED or FAILED |
| `status` | Enum | NOT NULL | `RUNNING`, `COMPLETED`, `FAILED`, `RESUMED` |
| `records_processed` | Integer | NOT NULL, default 0 | Count of successfully stored records |
| `records_skipped` | Integer | NOT NULL, default 0 | Count of skipped (invalid or duplicate) records |
| `last_checkpoint` | Integer | nullable | `start_index` of last committed batch — for resume |
| `error_log` | JSON | nullable | Array of `{index, reason}` objects for skipped/failed records |
| `config_snapshot` | JSON | NOT NULL | Snapshot of FieldMapping and SourceConnector config at time of run |

**State transitions**:
```
RUNNING → COMPLETED (all records processed)
RUNNING → FAILED (unrecoverable error)
FAILED  → RESUMED (import restarted from last_checkpoint)
RESUMED → COMPLETED
RESUMED → FAILED
```

---

## Value Objects

### FieldMapping

Configuration that maps source columns to AnswerGuard's standard fields.

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `question_column` | String | YES | Source column name for question text |
| `answer_column` | String | YES | Source column name for answer text |
| `timestamp_column` | String | NO | Source column for timestamp |
| `external_id_column` | String | NO | Source column for external ID |
| `metadata_columns` | Map[String, String] | NO | `{answerguard_key: source_column}` |

**Validation rules:**
- `question_column` and `answer_column` must be non-empty and must exist in the source table (validated before import starts)
- `metadata_columns` keys must be valid identifiers (no spaces, no reserved keywords)

---

### SourceConnector

Configuration for accessing the client's BigQuery source.

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `source_system_id` | String | YES | Developer-chosen identifier (e.g., "prod-agent-v2") |
| `gcp_project_id` | String | YES | Google Cloud project ID |
| `dataset_id` | String | YES | BigQuery dataset ID |
| `table_id` | String | YES | BigQuery table or view ID |
| `credentials_path` | String | NO | Path to service account JSON; if absent, uses ADC |
| `field_mapping` | FieldMapping | YES | Column mapping config |
| `row_filter` | String | NO | Optional BigQuery WHERE clause (e.g., `created_at > '2024-01-01'`) |
| `page_size` | Integer | NO | Rows per batch; default 5000 |

---

## Domain Events

```python
@dataclass(frozen=True)
class QAPairIngested(DomainEvent):
    qa_pair_id: str = ""
    source_system_id: str = ""
    ingestion_method: str = ""   # "HISTORICAL_IMPORT" or "RUNTIME_CAPTURE"

@dataclass(frozen=True)
class IngestionRunStarted(DomainEvent):
    run_id: str = ""
    source_system_id: str = ""

@dataclass(frozen=True)
class IngestionRunCompleted(DomainEvent):
    run_id: str = ""
    records_processed: int = 0
    records_skipped: int = 0

@dataclass(frozen=True)
class IngestionRunFailed(DomainEvent):
    run_id: str = ""
    reason: str = ""
    last_checkpoint: int = 0
```

---

## Database Schema (PostgreSQL / SQLite)

```sql
CREATE TABLE qa_pairs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    question_text   TEXT NOT NULL,
    answer_text     TEXT NOT NULL,
    captured_at     TIMESTAMP NOT NULL DEFAULT NOW(),
    source_timestamp TIMESTAMP,
    source_system_id VARCHAR(255) NOT NULL,
    external_id     VARCHAR(255),
    source_hash     VARCHAR(64) NOT NULL UNIQUE,
    ingestion_method VARCHAR(32) NOT NULL CHECK (ingestion_method IN ('HISTORICAL_IMPORT', 'RUNTIME_CAPTURE')),
    ingestion_run_id UUID REFERENCES ingestion_runs(id),
    metadata        JSON
);

CREATE INDEX idx_qa_pairs_source_system ON qa_pairs(source_system_id);
CREATE INDEX idx_qa_pairs_external_id ON qa_pairs(external_id);
CREATE INDEX idx_qa_pairs_captured_at ON qa_pairs(captured_at);

CREATE TABLE ingestion_runs (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_system_id    VARCHAR(255) NOT NULL,
    started_at          TIMESTAMP NOT NULL DEFAULT NOW(),
    completed_at        TIMESTAMP,
    status              VARCHAR(16) NOT NULL CHECK (status IN ('RUNNING', 'COMPLETED', 'FAILED', 'RESUMED')),
    records_processed   INTEGER NOT NULL DEFAULT 0,
    records_skipped     INTEGER NOT NULL DEFAULT 0,
    last_checkpoint     INTEGER,
    error_log           JSON,
    config_snapshot     JSON NOT NULL
);
```

*SQLite note: `gen_random_uuid()` is replaced by application-generated UUIDs; `CHECK` constraints work on SQLite 3.25+.*
