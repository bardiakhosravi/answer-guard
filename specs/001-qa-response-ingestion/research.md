# Research: Q&A Response Ingestion & Storage

**Feature**: 001-qa-response-ingestion
**Date**: 2026-04-21

---

## Decision 1: BigQuery Source Connector

**Decision**: Use `google-cloud-bigquery` Python client library with paginated `list_rows()` reads.

**Rationale**:
- Official Google client, well-maintained, supports both ADC and service account JSON auth
- `list_rows(table_id, page_size=N)` with `.pages` iteration avoids loading millions of rows into memory
- Use `selected_fields` to fetch only Q&A columns and reduce data transfer

**Resumable import**: BigQuery has no built-in checkpointing. We track an `IngestionRun` record in AnswerGuard's own database, storing the last successfully committed `start_index`. On resume, `list_rows(start_index=last_offset)` picks up from where it stopped. Checkpoint is written per batch (not per row) — balance between durability and throughput.

**Authentication**: Support both:
- Application Default Credentials (ADC) via `GOOGLE_APPLICATION_CREDENTIALS` env var — recommended for self-hosted
- Service account JSON key file path in config

**Throughput**: `list_rows` achieves ~10–100K rows/sec depending on row size and network. With page_size=5000, expect ~100ms per page. At 10K rows/min target from spec (SC-002), this is well within range.

**Alternatives considered**: BigQuery Storage Read API (~100MB/sec with Arrow parallel reads) — rejected as overcomplicated for v1 volumes. Can be added as an optimization later.

---

## Decision 2: AnswerGuard Storage — SQLAlchemy + Alembic

**Decision**: SQLAlchemy 2.0 (sync) + Alembic for both SQLite (local dev) and PostgreSQL (production).

**Rationale**:
- Same ORM models and queries work against both databases by swapping the connection string
- Alembic with `render_as_batch=True` handles SQLite's ALTER TABLE limitations transparently
- Sync SQLAlchemy is simpler and sufficient — async only needed for hundreds of concurrent connections which is not a v1 concern
- One schema, one migration set, two environments

**Field type decisions**:
- Use `JSON` (not `JSONB`) as the base type for metadata fields; specify `JSONB` as a Postgres variant for production performance: `JSON().with_variant(JSONB(), "postgresql")`
- Use SQLAlchemy's `GUID` type for UUIDs — stored as string on SQLite, native UUID on Postgres
- Avoid Postgres-specific operators (`@>`, `?`) in generic queries

**Migration**: Alembic with `render_as_batch=True` in `env.py`. SQLite runs batch operations (temp table + copy); PostgreSQL runs normal ALTER statements.

**Alternatives considered**: `databases` library (encode/databases) — lighter but less battle-tested for schema management. Rejected in favour of SQLAlchemy for hexagonal architecture clarity.

---

## Decision 3: Sync model — One-time import, SDK for ongoing

**Decision**: Historical import is a one-time operation. All new Q&A data after onboarding flows through the SDK/API at runtime.

**Rationale**: Periodic sync (nightly pull) would require a scheduler, state tracking, and conflict resolution — significant scope increase. The SDK integration is lightweight (2–3 lines of code) and gives better real-time coverage. One-time import solves the cold-start problem.

---

## Decision 4: Deduplication

**Decision**: Use a deterministic SHA-256 hash of `(question_text + answer_text + source_system_id)` as the deduplication key, stored as `source_hash` on `QAPair`. Source-provided IDs are stored as `external_id` and indexed, and can also be used for deduplication when provided.

**Rationale**: Client source databases may not have stable IDs, or IDs may collide across source systems. A content hash is stable and independent of the source schema.

---

## Decision 5: SDK fail-open pattern

**Decision**: SDK capture is fire-and-forget with a background thread/coroutine. The calling code never awaits the capture result. Failures are logged to stderr silently.

**Rationale**: SC-003 requires <50ms overhead. A synchronous HTTP call to AnswerGuard would add 50–200ms. Background dispatch adds <1ms to the hot path.
