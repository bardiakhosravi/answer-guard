---
sidebar_position: 2
---

# Quickstart

:::tip ⏱ Under 5 minutes
This guide gets you from zero to a running AnswerGuard instance using Docker. No Python setup, no migrations, no configuration — one command and you're running.
:::

## Prerequisites

- **Docker Desktop** (or Docker + Docker Compose on Linux) — [install here](https://www.docker.com/products/docker-desktop/)
- **git**

## Step 1: Clone the repository

```bash
git clone https://github.com/bardiakhosravi/answer-guard.git
cd answer-guard
```

## Step 2: Start AnswerGuard

```bash
docker compose up
```

This starts two containers:
- **AnswerGuard API** on port `8080` — runs database migrations automatically on startup
- **PostgreSQL** on port `5432` — your local database

Wait until you see:

```
answerguard-api-1  | Starting AnswerGuard...
answerguard-api-1  | INFO:     Uvicorn running on http://0.0.0.0:8080
```

## Step 3: Verify the server is running

```bash
curl http://localhost:8000/health
```

Expected response:

```json
{"status": "ok"}
```

## Step 4: Capture a test Q&A pair

```bash
curl -X POST http://localhost:8000/v1/capture \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is AnswerGuard?",
    "answer": "AnswerGuard is a response quality enforcement tool for AI agent products.",
    "source_system_id": "quickstart-test",
    "metadata": {"topic": "product"}
  }'
```

Expected response:

```json
{"qa_pair_id": "...", "captured_at": "2026-04-22T10:00:00Z"}
```

## Step 5: Verify the data is stored

```bash
curl http://localhost:8000/v1/ingest/status
```

You should see your test capture:

```json
{
  "total_qa_pairs": 1,
  "sources": [
    {
      "source_system_id": "quickstart-test",
      "total_records": 1,
      "runtime_captures_last_24h": 1,
      "last_ingested_at": "...",
      "last_import_run": null
    }
  ]
}
```

🎉 **AnswerGuard is running.** You have a captured Q&A pair in storage.

## Stop the server

```bash
docker compose down
```

To also remove the local database volume:

```bash
docker compose down -v
```

## Next steps

- **[Integration Guide →](/docs/integration/)** — Connect your real agent system and import your BigQuery history.
- **[API Reference →](/docs/reference/api)** — Full documentation for all endpoints and fields.

---

## Without Docker

If you can't use Docker, you can run AnswerGuard directly with Python 3.11+:

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e .
cp .env.example .env
# Edit .env: set DATABASE_URL=sqlite:///./answerguard.db
DATABASE_URL=sqlite:///./answerguard.db PYTHONPATH=. alembic upgrade head
DATABASE_URL=sqlite:///./answerguard.db uvicorn main:app --port 8080
```

Then continue from Step 3 above.
