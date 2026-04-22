---
sidebar_position: 10
---

# Troubleshooting

Common errors and how to fix them.

---

## 1. `GOOGLE_APPLICATION_CREDENTIALS` file not found

**Symptom:**
```
FileNotFoundError: [Errno 2] No such file or directory: '/path/to/key.json'
```
or
```
google.auth.exceptions.DefaultCredentialsError: File /path/to/key.json was not found.
```

**Cause:** The path set in `GOOGLE_APPLICATION_CREDENTIALS` doesn't exist or isn't accessible to the AnswerGuard process.

**Resolution:**
1. Confirm the file exists: `ls -la /path/to/key.json`
2. Use an absolute path (not relative): `/home/user/keys/bq-key.json` not `./bq-key.json`
3. Check file permissions: `chmod 600 /path/to/key.json`
4. If running in Docker, ensure the file is mounted: `-v /host/path/key.json:/secrets/key.json`

---

## 2. `FieldMappingValidationError` — column not found

**Symptom:**
```json
{
  "error": "INVALID_FIELD_MAPPING",
  "detail": "Column 'user_question' (question_column) not found in source table. Available: ['question', 'answer', 'created_at']"
}
```

**Cause:** A column name in your `field_mapping` doesn't match the actual column names in your BigQuery table.

**Resolution:**
The error message lists the available columns. Update your `field_mapping` to use the correct column names:

```json
{
  "field_mapping": {
    "question_column": "question",   // ✅ use the name from the error message
    "answer_column": "answer"
  }
}
```

---

## 3. `409 IMPORT_ALREADY_RUNNING`

**Symptom:**
```json
{
  "error": "IMPORT_ALREADY_RUNNING",
  "detail": "An import for source_system_id 'prod-agent-v2' is already in progress. Run ID: a1b2c3..."
}
```

**Cause:** An import is currently RUNNING for the same `source_system_id`. Only one import runs per source at a time.

**Resolution:**
1. Check the current run's progress: `GET /v1/ingest/status/a1b2c3...`
2. Wait for it to complete — large imports can take several minutes
3. If the run appears stuck (no `records_processed` increase after 10+ minutes), the server may have restarted mid-import. Re-trigger the import — AnswerGuard will resume from the last checkpoint

---

## 4. `OperationalError: no such table: qa_pairs`

**Symptom:**
```
sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) no such table: qa_pairs
```

**Cause:** The database migrations haven't been applied.

**Resolution:**
Run the migration command before starting the server:

```bash
DATABASE_URL=sqlite:///./answerguard.db PYTHONPATH=. alembic upgrade head
```

For PostgreSQL:
```bash
DATABASE_URL=postgresql://user:pass@host:5432/db PYTHONPATH=. alembic upgrade head
```

---

## 5. SDK captures not appearing in status

**Symptom:** You've added the SDK and your agent is handling traffic, but `runtime_captures_last_24h` stays at 0.

**Cause:** The `capture()` method is fire-and-forget — if it's failing, the error is only logged to stderr/console.error and never surfaces to the caller.

**Resolution:**

**Step 1 — Check stderr logs.** Look for lines starting with `[AnswerGuard]`:

```
[AnswerGuard] Capture failed: HTTPConnectionPool(host='localhost', port=8080): Max retries exceeded
```

**Step 2 — Switch to `capture_sync()` temporarily** to surface the error:

```python
# Python
result = guard.capture_sync(question, answer)  # raises on failure
```

```typescript
// TypeScript
const result = await guard.captureAsync(question, answer);  // throws on failure
```

**Step 3 — Common causes:**

| Symptom from capture_sync | Fix |
|---------------------------|-----|
| `Connection refused` | AnswerGuard server isn't running, or `endpoint` URL is wrong |
| `404 Not Found` | Check endpoint URL — should end with server root, not `/v1/capture` |
| `422 Unprocessable Entity` | `source_system_id` is empty or missing |

Once fixed, switch back to `capture()` for production.
