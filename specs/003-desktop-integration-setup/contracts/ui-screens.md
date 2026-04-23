# UI Contract: Desktop App Screens

**Feature**: 003-desktop-integration-setup
**Date**: 2026-04-22

Defines the required screens, their content, and transition rules. Every screen listed here must be implemented and reachable via the navigation described.

---

## App Shell

Present on all screens. Contains:
- **AnswerGuard logo + app name** (top left)
- **Connection status indicator** — green dot "Connected to [URL]" or red dot "Not connected" (top right)
- **Sidebar navigation** (visible after server connection is established):
  - Source Setup (→ `/connector`)
  - Import (→ `/import`) — disabled until source connector is saved
  - Data (→ `/data`) — disabled until at least one import has completed

---

## Screen 1: Server Connection (`/connect`)

**Shown when**: No valid server URL is configured, or the configured server is unreachable.

**Must contain:**
- Page title: "Connect to AnswerGuard"
- Short description: "Enter the URL of your running AnswerGuard instance."
- Text input: "Server URL" with placeholder `http://localhost:8000`
- Primary button: "Connect"
- On success → navigate to `/connector` and persist URL
- On failure → show inline error below input: specific message (e.g. "Server not reachable", "Not an AnswerGuard server")

**Must NOT contain:**
- Username/password fields (no auth in v1)

---

## Screen 2a: Source Connector — Connection Details (`/connector/details`)

**Shown when**: No source connector is configured, or the user navigates to Source Setup.

**Must contain:**
- Page title: "Configure Source"
- Step indicator: "Step 1 of 3 — Connection Details"
- Form fields:
  - **Source System ID** (text input, required) — with helper text: "A name you choose to identify this data source, e.g. `prod-agent-v2`"
  - **GCP Project ID** (text input, required)
  - **Dataset ID** (text input, required)
  - **Table ID** (text input, required)
  - **Credentials file** (file path input + "Browse" button that opens native file picker, optional) — helper text: "Leave empty to use Application Default Credentials"
  - **Row filter** (text input, optional) — helper text: "BigQuery WHERE clause, e.g. `created_at > '2024-01-01'`"
  - **Page size** (number input, optional, default 5000)
- Primary button: "Discover Schema →"
- On click → call `POST /v1/sources/discover-schema`; show loading state; on success navigate to `/connector/schema` with discovered columns; on error show inline error

**Form validation (client-side):**
- Source System ID, GCP Project ID, Dataset ID, Table ID must be non-empty before submit

---

## Screen 2b: Source Connector — Field Mapping (`/connector/schema`)

**Shown after**: Successful schema discovery.

**Must contain:**
- Page title: "Map Your Columns"
- Step indicator: "Step 2 of 3 — Field Mapping"
- **Discovered columns panel** (left side or top): list of all columns returned by discover-schema, each showing name and type badge (e.g. `STRING`, `TIMESTAMP`)
- **Mapping form** (right side or below): for each AnswerGuard field, a labelled dropdown populated with discovered column names:
  - **Question column** *(required)* — dropdown
  - **Answer column** *(required)* — dropdown
  - **Timestamp column** *(optional)* — dropdown with "None" option
  - **External ID column** *(optional)* — dropdown with "None" option
  - **Metadata columns** *(optional)* — repeatable key-value pairs: AnswerGuard key (text input) + source column (dropdown)
- Primary button: "Review Mapping →"
- Back button: "← Back to Connection Details"
- Required fields must be mapped before primary button is enabled

---

## Screen 2c: Source Connector — Review (`/connector/review`)

**Shown after**: Field mapping complete.

**Must contain:**
- Page title: "Review Configuration"
- Step indicator: "Step 3 of 3 — Review"
- Read-only summary of all configured values (source system ID, BigQuery details, field mapping)
- Primary button: "Save Configuration"
- On save → persist config locally; navigate to `/import`
- Back button: "← Edit Mapping"
- Edit link on each section to jump back to the relevant step

---

## Screen 3: Import (`/import`)

**Shown when**: Source connector is configured.

**State A — Ready to import (no active or recent run):**
- Page title: "Historical Import"
- Summary of configured source (source system ID, table)
- Record count estimate if available: "Your table contains approximately X rows"
- Primary button: "Start Import"
- On click → POST to `/v1/ingest/import`; transition to State B

**State B — Import in progress:**
- Page title: "Import Running"
- **Progress card**:
  - Status badge: `RUNNING` or `RESUMED`
  - Records processed: large number, updating every 3 seconds
  - Records skipped: count with link to skipped records detail
  - Elapsed time: live timer
  - Progress bar (if total row count known)
- No "Start Import" button visible (prevents duplicate)
- Polling: `GET /v1/ingest/status/{run_id}` every 3 seconds

**State C — Import completed:**
- Page title: "Import Complete"
- **Summary card**:
  - ✅ "Import completed successfully"
  - Records ingested: N
  - Records skipped: N (with expand button to show reasons)
  - Duration
- Primary button: "View Ingested Data →" (navigates to `/data`)
- Secondary button: "Run Another Import" (resets to State A)

**State D — Import failed:**
- Page title: "Import Failed"
- **Error card**:
  - ❌ "Import failed"
  - Error reason
  - Records successfully ingested before failure: N
  - Last checkpoint
- Primary button: "Resume Import" (re-sends same import request; auto-resumes from checkpoint)
- Secondary button: "Reconfigure Source" (navigates to `/connector`)

---

## Screen 4: Data View (`/data`)

**Shown when**: At least one import has completed.

**Must contain:**
- Page title: "Ingested Data"
- **Stats bar**: Total records | Records this session | Last ingested at
- **Search input**: filters list in real time by question or answer text
- **Source filter** (dropdown): "All sources" or specific source system ID
- **Q&A pair list** (left panel, paginated):
  - Each row: truncated question text (max 2 lines) + answer preview (1 line) + timestamp + source badge
  - Active row highlighted
  - Pagination controls: previous / next / page number
  - Load next page on scroll (infinite scroll or explicit pagination — either acceptable)
- **Detail panel** (right panel, shown when a row is selected):
  - Full question text
  - Full answer text
  - Source system ID
  - Captured at timestamp
  - Ingestion method badge (`HISTORICAL_IMPORT` or `RUNTIME_CAPTURE`)
  - External ID (if present)
  - Metadata key-value pairs (if present)
- **Skipped Records tab**: shows records that were not ingested during the most recent import, with per-record reason

**Must NOT contain:**
- Edit, annotate, or delete actions on Q&A pairs (read-only in this feature)

---

## Navigation Rules

| From | To | Condition |
|------|----|-----------|
| Any screen | `/connect` | Server becomes unreachable |
| `/connect` | `/connector/details` | Server connection verified |
| `/connector/details` | `/connector/schema` | Schema discovery succeeds |
| `/connector/schema` | `/connector/review` | All required fields mapped |
| `/connector/review` | `/import` | Configuration saved |
| `/import` (State C) | `/data` | User clicks "View Ingested Data" |
| Sidebar | `/connector` | Always navigable once connected |
| Sidebar | `/import` | Only after source connector saved |
| Sidebar | `/data` | Only after at least one import completed |
