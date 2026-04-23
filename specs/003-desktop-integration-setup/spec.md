# Feature Specification: Desktop App — Integration Setup

**Feature Branch**: `003-desktop-integration-setup`
**Created**: 2026-04-22
**Status**: Draft
**Input**: User description: "i want to build a cross platform desktop app that will be the interface to the platform. the first feature we can build for this app is to make it easy for the user to do the integration with their database, configuring the source connector, defining their field mapping by connecting to their database discovering the schemas and guiding the user to choosing the fields we want to be configured. the success criteria for this feature that that the user can fully configure the integration using the desktop app and see their data ingested, understand what was ingested and then view the data that was ingested which is a starting point for the next features we want to build"

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Connect to AnswerGuard and Set Up the Source Connector (Priority: P1)

A developer opens the AnswerGuard desktop app for the first time. They need to connect the app to their running AnswerGuard instance and then configure where their Q&A data lives — their BigQuery project, dataset, and table. The app connects directly to BigQuery, discovers the table's schema, and walks the developer through mapping their columns to AnswerGuard's required fields.

**Why this priority**: Nothing else in the app is useful until this step is complete. It is the entry point to the entire platform. If this is hard or error-prone, the developer abandons the tool before seeing any value.

**Independent Test**: A developer with a running AnswerGuard instance and a BigQuery dataset can open the desktop app, configure the source connector, and complete field mapping — with no reference to documentation — within 15 minutes. Testable by timing a developer completing the flow from a fresh install.

**Acceptance Scenarios**:

1. **Given** a developer opens the app for the first time, **When** they are prompted to enter their AnswerGuard server URL, **Then** the app validates the connection and confirms the server is reachable before proceeding.
2. **Given** a developer provides their BigQuery connection details (GCP project, dataset, table, and credentials), **When** the app connects to BigQuery, **Then** it automatically discovers and displays all available column names and their data types from the selected table.
3. **Given** the app has discovered the schema, **When** the developer is on the field mapping screen, **Then** the app presents the required fields (question, answer) and optional fields (timestamp, external ID, metadata) and lets the developer assign their source columns by selecting from a dropdown populated with the discovered column names.
4. **Given** a developer has completed field mapping, **When** they save the configuration, **Then** the app validates that all required fields have been mapped before allowing them to proceed.
5. **Given** an invalid BigQuery credential or unreachable table, **When** the connection attempt fails, **Then** the app displays a clear error message identifying the problem (wrong credentials, table not found, insufficient permissions) and allows the developer to correct and retry.

---

### User Story 2 - Run the Historical Import and Monitor Progress (Priority: P2)

With the source connector configured, the developer wants to import their existing Q&A history. They trigger the import from the desktop app, and the app shows them live progress — how many records have been processed, how many were skipped, and whether the import is still running or has completed.

**Why this priority**: Seeing data flow into AnswerGuard is the moment the integration becomes real. Without visible progress and completion confirmation, the developer has no confidence the setup worked.

**Independent Test**: A developer triggers a historical import from the desktop app, watches live progress, and the import completes — all without leaving the app or using curl. Testable by observing a developer complete the import flow end-to-end in the desktop app.

**Acceptance Scenarios**:

1. **Given** a developer has completed source connector setup, **When** they trigger the historical import, **Then** the app shows a live progress view with: records processed, records skipped, current status, and elapsed time — updating at least every 5 seconds.
2. **Given** an import is in progress, **When** the developer closes and reopens the app, **Then** the app reconnects to the running import and continues showing live progress.
3. **Given** an import completes successfully, **When** the status changes to complete, **Then** the app displays a summary: total records ingested, total skipped, any errors with reasons, and a clear "done" state.
4. **Given** an import fails mid-way, **When** the developer views the status, **Then** the app shows what failed, how many records were successfully imported before the failure, and offers a "Resume Import" action.
5. **Given** a developer attempts to start a new import while one is already running, **When** they click the import button, **Then** the app prevents the duplicate and explains that an import is in progress.

---

### User Story 3 - View Ingested Data (Priority: P3)

After the import completes, the developer wants to see the actual Q&A pairs that landed in AnswerGuard. They need to confirm the right data came through, understand its shape, and have a starting point for the PM review workflow that comes next.

**Why this priority**: This closes the integration feedback loop. Without visible data, the developer cannot confirm the integration worked correctly or hand it off to the PM. It also establishes the foundational data view that future features (annotation, guideline creation) will build on.

**Independent Test**: After an import completes, a developer can browse the ingested Q&A pairs in the desktop app, see the question, answer, timestamp, and metadata for each record, and scroll through the full dataset — without leaving the app. Testable by observing a developer navigate the data view after a completed import.

**Acceptance Scenarios**:

1. **Given** an import has completed, **When** the developer navigates to the data view, **Then** they see a paginated list of ingested Q&A pairs showing: question text, answer text, source system ID, capture timestamp, and ingestion method for each record.
2. **Given** a list of Q&A pairs, **When** the developer selects a record, **Then** a detail panel shows the full question and answer text, all metadata fields, and the record's ingestion status.
3. **Given** a large dataset (thousands of records), **When** the developer scrolls through the list, **Then** the app loads records progressively without freezing or requiring a full reload.
4. **Given** the data view is open, **When** the developer types in a search box, **Then** the list filters in real time to show only records whose question or answer text matches the search term.
5. **Given** an import that had skipped records, **When** the developer views the data, **Then** they can see which records were skipped and why (missing required field, duplicate) in a separate "Skipped Records" view.

---

### Edge Cases

- What happens when the AnswerGuard server URL is entered correctly but the server is down? App must distinguish "server unreachable" from "wrong URL" and give actionable guidance.
- What if the BigQuery table has hundreds of columns? The schema discovery display must be scrollable and searchable — not an overwhelming flat list.
- What if the developer changes the field mapping after data has already been imported? The app must warn that changing mapping does not retroactively re-map existing records.
- What if a re-import is triggered (same source connector) after previous data exists? The app must display the deduplication behaviour — only new records will be added, existing ones are skipped.
- What happens if the desktop app loses its connection to the AnswerGuard server while an import is running? The import continues server-side; the app must be able to reconnect and resume showing progress.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The app MUST allow the user to configure the AnswerGuard server URL and validate the connection before any other feature is accessible.
- **FR-002**: The app MUST provide a source connector configuration screen where the user enters their BigQuery connection details: GCP project ID, dataset ID, table ID, and credentials.
- **FR-003**: The app MUST connect to the configured BigQuery source and automatically discover and display the table schema — all column names and their data types — without requiring the user to look them up manually.
- **FR-004**: The app MUST provide a guided field mapping interface where the user assigns discovered source columns to AnswerGuard fields using a visual selection control (not free-text entry).
- **FR-005**: The app MUST clearly indicate which fields are required (question, answer) and which are optional (timestamp, external ID, metadata columns), and prevent saving an incomplete mapping.
- **FR-006**: The app MUST validate the BigQuery connection and field mapping before triggering an import, and display specific, actionable error messages when validation fails.
- **FR-007**: The app MUST allow the user to trigger the historical import and display live progress — records processed, records skipped, elapsed time, current status — polling for updates automatically.
- **FR-008**: The app MUST show an import completion summary including total records ingested, total skipped, and any errors with per-record reasons.
- **FR-009**: The app MUST allow a failed import to be resumed from the point of failure with a single action.
- **FR-010**: The app MUST provide a paginated, searchable data view showing all ingested Q&A pairs with their key fields visible without requiring the user to open each record.
- **FR-011**: The app MUST provide a detail view for individual Q&A pairs showing the full content of all fields including metadata.
- **FR-012**: The app MUST display a separate view for skipped records showing the reason each record was not ingested.
- **FR-013**: The source connector configuration MUST be persisted locally so the user does not need to re-enter it each time they open the app.

### Key Entities

- **ServerConnection**: The configured AnswerGuard server URL and its connection status. Persisted locally.
- **SourceConnectorConfig**: BigQuery connection details and field mapping configuration. Persisted locally.
- **DiscoveredSchema**: The list of column names and data types retrieved from the BigQuery table. Transient — fetched on demand.
- **FieldMapping**: The user's assignment of source columns to AnswerGuard's required and optional fields.
- **ImportJob**: Represents a running or completed historical import, with status, progress counts, and error log.
- **QAPairRecord**: An ingested Q&A pair as displayed in the data view: question, answer, timestamp, source system ID, metadata.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A developer can complete the full integration setup — server connection, source connector configuration, field mapping, import trigger, and data verification — in under 15 minutes on their first use, without consulting documentation.
- **SC-002**: The schema discovery step returns the full list of columns for a target BigQuery table within 10 seconds of the developer providing their connection details.
- **SC-003**: Import progress updates are visible to the developer within 10 seconds of each batch completing — the developer is never left wondering if the import is still running.
- **SC-004**: 100% of successfully ingested Q&A pairs are visible in the data view within 30 seconds of the import completing.
- **SC-005**: A developer can find a specific Q&A pair in the data view using text search within 5 seconds of typing their search term.
- **SC-006**: The app works identically on macOS and Windows without requiring OS-specific installation steps or configuration.

---

## Assumptions

- The desktop app connects to a self-hosted AnswerGuard backend instance (running locally via Docker or on a remote server). The user provides the server URL on first launch. Cloud-hosted AnswerGuard (answerguard.cloud) is out of scope for this feature.
- The only supported data source in v1 is BigQuery. Other sources (PostgreSQL, CSV, etc.) are out of scope for this feature.
- The desktop app communicates with AnswerGuard exclusively via its existing REST API — no new backend endpoints are required for this feature beyond what feature 001 already delivered.
- The app does not handle BigQuery authentication on behalf of the user — the user provides either a service account JSON key file path or relies on Application Default Credentials already configured on their machine.
- The data view shows read-only records. Creating annotations, building guidelines, and the PM review workflow are out of scope for this feature and are the starting point for the next feature.
- The configuration (server URL, source connector, field mapping) is persisted on the user's local machine. Multi-user or team-shared configuration is out of scope.
- The desktop app does not need an authentication layer (login/password) for v1 — access is controlled at the network level (the user connects to their own AnswerGuard instance).
- Runtime SDK capture setup (adding the Python/TypeScript SDK to the agent pipeline) is out of scope for this feature — it is handled via the existing developer documentation.
