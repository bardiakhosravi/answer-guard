---
sidebar_position: 2
---

# Configuration Reference

All configuration is done via environment variables. Copy `.env.example` to `.env` and fill in the required values.

---

## Database

| Variable | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `DATABASE_URL` | string | ✅ | — | SQLAlchemy connection string |

**SQLite (local development):**
```env
DATABASE_URL=sqlite:///./answerguard.db
```

**PostgreSQL (production):**
```env
DATABASE_URL=postgresql://user:password@host:5432/answerguard
```

---

## BigQuery

| Variable | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `GCP_PROJECT_ID` | string | ❌ | — | Default GCP project ID (can be overridden per import request) |
| `GOOGLE_APPLICATION_CREDENTIALS` | string | ❌ | uses ADC | Absolute path to GCP service account JSON key file |
| `BIGQUERY_PAGE_SIZE` | integer | ❌ | `5000` | Default rows per batch for BigQuery imports |

:::tip
`GOOGLE_APPLICATION_CREDENTIALS` is optional if you're running on Google Cloud infrastructure (Cloud Run, GKE, Compute Engine) with a service account attached. Leave it empty to use Application Default Credentials.
:::

---

## Server

The server is started with `uvicorn`. Configuration is passed as CLI arguments:

```bash
uvicorn main:app --host 0.0.0.0 --port 8080
```

| Argument | Default | Description |
|----------|---------|-------------|
| `--host` | `127.0.0.1` | Bind address. Use `0.0.0.0` to accept external connections. |
| `--port` | `8000` | Port to listen on |
| `--workers` | `1` | Number of worker processes (use multiple for production) |

---

## Python SDK

The Python SDK is configured in code when instantiating `AnswerGuard`:

```python
from answerguard import AnswerGuard

guard = AnswerGuard(
    endpoint="http://localhost:8080",  # required
    source_system_id="my-agent",       # required
    timeout_ms=2000,                   # optional, default: 2000
)
```

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `endpoint` | string | ✅ | — | AnswerGuard server URL |
| `source_system_id` | string | ✅ | — | Identifies this agent system |
| `timeout_ms` | integer | ❌ | `2000` | HTTP timeout for capture calls (milliseconds) |

---

## TypeScript SDK

The TypeScript SDK is configured in the constructor:

```typescript
import { AnswerGuard } from '@answerguard/sdk';

const guard = new AnswerGuard({
  endpoint: 'http://localhost:8080',  // required
  sourceSystemId: 'my-agent',         // required
  timeoutMs: 2000,                    // optional, default: 2000
});
```

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `endpoint` | string | ✅ | — | AnswerGuard server URL |
| `sourceSystemId` | string | ✅ | — | Identifies this agent system |
| `timeoutMs` | number | ❌ | `2000` | HTTP timeout for capture calls (milliseconds) |
