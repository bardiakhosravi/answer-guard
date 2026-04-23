---
sidebar_position: 1
---

# Desktop App

The AnswerGuard desktop app is the primary interface for configuring your BigQuery source, running historical imports, and browsing the Q&A pairs that have been ingested into AnswerGuard.

It's a native app built with Tauri and ships as a small `.dmg` (macOS) or `.msi` (Windows) — no browser required, no web hosting to set up. It talks to your self-hosted AnswerGuard backend over its existing REST API.

## Download

Signed builds are produced by CI on every push to `main`. Grab the latest from the repository's [Releases page](https://github.com/bardiakhosravi/answer-guard/releases) or the [latest workflow run artifacts](https://github.com/bardiakhosravi/answer-guard/actions/workflows/desktop-build.yml).

Available platforms:

- **macOS** — universal `.dmg` for Apple Silicon (Intel builds via the CI matrix)
- **Windows** — `.msi` installer for x64

## Before you install

You need a running AnswerGuard backend the app can talk to. Follow the [Quickstart](/docs/quickstart) if you haven't set one up yet — `docker compose up` is the fastest path.

## First run

1. **Open the app.** On first launch it shows a connection screen asking for your AnswerGuard server URL (for example `http://localhost:8000`).
2. **Configure the source** — a 3-step wizard:
   - **Connection details** — GCP project, dataset, table, and optional credentials file (falls back to Application Default Credentials).
   - **Field mapping** — the app connects to BigQuery, discovers your table's columns, and walks you through mapping them to AnswerGuard's fields (question, answer, timestamp, external ID, metadata).
   - **Review** — confirm the full configuration before saving.
3. **Run the import.** On the Import screen you can optionally apply a BigQuery `WHERE` clause (row filter) to limit which rows are imported. Click *Start Import* and watch the live progress — records processed, records skipped, elapsed time, and the last checkpoint.
4. **Browse your data.** Once the import completes, the Data screen shows every ingested Q&A pair in a paginated, searchable list with a detail panel. A separate "Skipped during last import" tab surfaces rows that were rejected (e.g. missing question text).
5. **Capture feedback on an answer.** In any Q&A detail view, the Answer section supports text selection. Highlight a passage and click **Improve selected**, or use **Improve whole response** for feedback on the whole answer. A modal collects the problem and desired behavior; on save the feedback is stored as a standalone record.
6. **Review feedback.** The **Response Feedback** screen (left sidebar) lists every captured feedback record across the product. Full-text search covers the excerpt, problem, and desired-behavior fields. Each row's detail view includes a **View source record →** link back to the original Q&A, and **Edit** / **Delete** actions. See [Response feedback →](/docs/governance/response-feedback) for the data model and API.

## What gets stored where

- **Your configuration** (server URL, source connector, field mapping) is saved locally on your machine as a JSON file:
  - macOS: `~/Library/Application Support/com.answerguard.desktop/config.json`
  - Windows: `%APPDATA%\com.answerguard.desktop\config.json`
- **Your Q&A data** goes to the PostgreSQL/SQLite database your AnswerGuard backend is pointed at — the desktop app never stores it itself.

## Error handling

The app surfaces actionable error messages inline:

- **Invalid row filter** — BigQuery's syntax error appears under the Row Filter field; the import never starts and no partial data is written.
- **Unreachable server** — the connection screen shows a clear "Could not reach an AnswerGuard server at that URL" with guidance to check the URL and server status.
- **Import failure mid-run** — the Import screen shows the error and a single-click **Resume Import** button, which picks up from the last successfully checkpointed batch.

## Building from source

If you want to build locally:

```bash
cd desktop
npm install
npm run tauri dev    # live-reload dev mode
npm run tauri build  # produce a signed .dmg / .msi
```

You need Node.js 20+ and the Rust toolchain installed.
