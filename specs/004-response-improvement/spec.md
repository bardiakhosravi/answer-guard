# Feature Specification: Response Improvement (Capture)

**Feature Branch**: `004-response-improvement`
**Created**: 2026-04-23
**Status**: Draft
**Input**: User description: "lets start very simple. first step is that the user can highlight a part of a response or the select the whole response that the agent provided and sees an 'improve' option, where they can then enter the guidlines what is wrong with this reponse and how we like the agent to behave, we need to store that and figure out how we will then enforce this guideline on future responses."

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Capture an Improvement from a Bad Response (Priority: P1)

A product manager is reviewing agent responses in the desktop app's Data view. They open a response and notice a specific passage that's wrong — maybe the tone is too casual for an enterprise customer, maybe the agent cited the wrong policy, maybe the answer buries the most important information. They select the problematic text (a sentence, paragraph, or the whole response), click **Improve**, write what's wrong and how they want the agent to behave in future, and save. The guideline is now stored and will be visible on the source record and in a dedicated list for later reference.

**Why this priority**: This is the PM's primary workflow. Every other feature in the platform (guideline management, enforcement engine, impact analytics) depends on having captured guidelines to operate on. Without this, AnswerGuard has no way to turn human review into actionable product input.

**Independent Test**: A PM with no prior knowledge of the tool can find a bad response in the data view, create their first guideline in under 30 seconds, and see it reflected on the record and in the guidelines list — using only the on-screen UI.

**Acceptance Scenarios**:

1. **Given** a PM is viewing a Q&A pair in the detail panel, **When** they select any contiguous span of text within the agent's response, **Then** an **Improve** action becomes visible near the selection.
2. **Given** a PM clicks **Improve** with no text selected, **When** the form opens, **Then** the whole response is treated as the highlighted span and that is clearly shown in the form.
3. **Given** a PM clicks **Improve**, **When** the improvement form is presented, **Then** it contains: a read-only preview of the highlighted text, a required **What's wrong?** field, a required **How should the agent behave instead?** field, and **Save** / **Cancel** actions.
4. **Given** the PM fills in both required fields and clicks **Save**, **When** the save succeeds, **Then** the form closes, the selected span in the response becomes visually marked (e.g. highlighted), and a new guideline entry appears in a guidelines list on the detail panel for that record.
5. **Given** the save fails because the backend is unreachable, **When** the save action returns an error, **Then** the form stays open, the user's input is preserved, and a clear error message explains the failure and suggests retrying.
6. **Given** a PM has created guidelines across multiple records, **When** they navigate to the **Guidelines** screen, **Then** they see every guideline they've ever created, most recent first, each showing a preview of the highlighted text and a link back to its source Q&A pair.

---

### User Story 2 - Review and Audit Captured Guidelines (Priority: P2)

Once the PM has captured several guidelines, they want to review what they've written so far — to spot duplicates, confirm coverage of common issues, or brief engineering on what the agent needs to do better. They open the **Guidelines** screen and browse the full list, filtering by free-text search.

**Why this priority**: Without a way to see accumulated guidelines, the PM can't trust that their work is being recorded reliably, and can't reason about whether the ruleset is growing in useful directions. This closes the immediate feedback loop and builds trust in the tool before enforcement exists.

**Independent Test**: A PM who has created 10+ guidelines can open the Guidelines screen and find a specific one they remember writing within 10 seconds using text search.

**Acceptance Scenarios**:

1. **Given** a PM has created guidelines over time, **When** they open the Guidelines screen, **Then** they see a paginated list sorted by creation time (most recent first).
2. **Given** the Guidelines list is open, **When** a PM types in the search box, **Then** the list filters in real time to match guidelines whose problem description, desired behavior, or highlighted text contains the search term.
3. **Given** a PM selects a guideline from the list, **When** the detail view opens, **Then** they see the full problem description, full desired behavior, the highlighted text excerpt, and a link that takes them to the source Q&A pair in the Data view.

---

### User Story 3 - Edit or Remove a Guideline (Priority: P3)

PMs make typos, change their minds, or capture something on a rainy Monday that doesn't make sense on Tuesday. They need to be able to edit the text of a guideline or delete one entirely.

**Why this priority**: Without edit/delete, the guidelines list becomes noisy over time and the PM stops trusting it. These are baseline CRUD operations, not a differentiator, but they're required for the tool to remain useful past day one.

**Independent Test**: A PM can locate a specific guideline, change its desired-behavior text, save the change, and see the updated text reflected everywhere (the record's detail view and the Guidelines list).

**Acceptance Scenarios**:

1. **Given** a PM is viewing a guideline's detail view, **When** they click **Edit**, **Then** the problem and desired-behavior fields become editable.
2. **Given** they save an edit, **When** the save succeeds, **Then** the change is reflected immediately in both the record's detail view and the Guidelines list.
3. **Given** they click **Delete** on a guideline, **When** they confirm the action, **Then** the guideline is removed from both views and the highlight on the source record disappears.

---

### Edge Cases

- What happens when the PM selects text that crosses formatting boundaries (e.g. across a line break)? The selection is captured as a continuous character range in the raw response text.
- What happens when a PM opens a record whose text has been updated since a guideline was created (e.g. future migration changes response storage)? The guideline preserves the originally-highlighted excerpt; if the underlying text no longer matches, the guideline is still listed but shown as "highlighted range no longer available" on the record view.
- What happens when a Q&A pair that has guidelines attached is deleted? The guidelines remain in the Guidelines list but are marked as "source record unavailable" — they are not auto-deleted so the PM's work is never silently destroyed.
- What happens when the same PM creates two guidelines with nearly identical text? Both are stored. Deduplication or similarity grouping is out of scope for this feature.
- What happens when two guidelines contradict each other? Both are stored. Conflict resolution is an enforcement-time concern and is out of scope for this feature.
- What happens when the form is open and the user navigates away? Unsaved input is discarded with a confirmation prompt.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: User MUST be able to select any contiguous span of text within an agent response in the Data view.
- **FR-002**: When text is selected (or when the user invokes the action with no selection), an **Improve** action MUST be available.
- **FR-003**: Invoking **Improve** with no text selected MUST treat the entire response as the highlighted span.
- **FR-004**: The improvement form MUST display a read-only preview of the highlighted text so the user confirms what they're commenting on.
- **FR-005**: The improvement form MUST require the user to fill in both a problem description ("what's wrong") and a desired-behavior statement ("how should the agent behave instead") — both must be non-empty to save.
- **FR-006**: On save, the system MUST persist the guideline in AnswerGuard's backend storage so it survives app restarts and is visible from any instance of the desktop app pointed at the same server.
- **FR-007**: A persisted guideline MUST record, at minimum: the source Q&A pair identifier, the exact highlighted text, the character range within the response, the problem description, the desired-behavior statement, and a creation timestamp.
- **FR-008**: The record detail view MUST visually highlight every text span that has a guideline attached to it and list those guidelines in a side panel.
- **FR-009**: A dedicated **Guidelines** screen MUST list every guideline created across the product, sorted by creation time with most recent first, and support free-text search across the problem description, desired behavior, and highlighted text.
- **FR-010**: Each guideline in the list MUST link back to its source Q&A pair in the Data view.
- **FR-011**: User MUST be able to edit an existing guideline's problem description and desired behavior.
- **FR-012**: User MUST be able to delete an existing guideline, with a confirmation step.
- **FR-013**: If a saved guideline's source Q&A pair is deleted, the guideline MUST remain in the Guidelines list and indicate that the source is no longer available — it MUST NOT be auto-deleted.
- **FR-014**: On any save or delete failure, the system MUST inform the user clearly, preserve their in-progress input, and not pretend the operation succeeded.

### Key Entities

- **Guideline**: The captured improvement. A guideline records what was wrong with a specific passage of an agent response and how the PM wants the agent to behave differently. Attached to one source Q&A pair but intended to influence the agent's behavior broadly.
  - Attributes: unique identifier, source Q&A pair reference, highlighted text excerpt, character range within the source response, problem description, desired-behavior statement, created-at timestamp, last-updated-at timestamp.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A PM can create a guideline from an open Q&A pair in under 30 seconds (select → Improve → fill two fields → save), measured by observing 5 users through the flow.
- **SC-002**: A PM can find any previously-created guideline in the Guidelines list within 10 seconds using text search, measured on a list of 100+ entries.
- **SC-003**: 100% of saved guidelines are retrievable after the desktop app is fully restarted and the backend is unaffected — no data loss in normal operation.
- **SC-004**: The stored guideline data includes every piece of context that a future enforcement engine would need to evaluate a draft response against it — specifically: the original response text, the exact highlighted span, the problem description, and the desired-behavior statement. No information loss that would require PMs to re-enter anything when the enforcement feature ships.
- **SC-005**: Zero silent failures: every save or delete operation either completes successfully and is reflected in all views, or returns a clear error to the user with their input preserved.

---

## Out of Scope (Explicitly Deferred)

These are intentionally not part of this feature. They're noted here so the spec boundary is clear.

- **Enforcement**: applying stored guidelines to future agent responses (e.g. at runtime via an SDK interceptor, or as a batch critique pass) is a separate feature. The user's request to "figure out how we will enforce" is acknowledged — this feature's job is to **capture guidelines in a form that enforcement can consume**. Enforcement itself is Feature 005.
- **Guideline scope**: treating guidelines as topic-scoped, source-scoped, or conditional (e.g. "only for billing questions"). All guidelines captured in this feature apply globally to future responses. Scoping is an enforcement-time concern.
- **Priority / weight**: ranking guidelines against each other when they conflict. All guidelines are equal weight in v1.
- **Auto-grouping / deduplication**: detecting near-duplicate guidelines and proposing consolidation. All guidelines are stored as-is.
- **Multi-user attribution**: tracking which PM created which guideline. The desktop app is single-user per install, matching the rest of the platform.
- **Templates or structured issue types**: the earlier PRD had fields for issue type (tone, accuracy, etc.) and severity. Intentionally omitted in v1 to keep the form to two free-text fields — these can be added later if needed.

---

## Assumptions

- The desktop app is the only entry point for capturing guidelines in v1. A web-based PM portal is out of scope.
- A single-user-per-install model persists, matching Features 001–003. No authentication, no roles.
- Guidelines are stored in AnswerGuard's existing backend database (the same one that holds Q&A pairs), so they're consistent across app restarts and across any future client that connects to the same backend.
- The free-text "problem" and "desired behavior" fields are stored as-is. No structured taxonomy (tone/accuracy/etc.) is enforced at this stage.
- Character-range highlighting uses the raw text offsets of the agent response as it exists at the time of capture. Changes to the underlying response text after the fact are handled per the edge case above.
- The feature extends the existing Data view in the desktop app. A separate Guidelines screen is added as a new sidebar entry.
- The backend gains a new `Guideline` aggregate and associated CRUD endpoints; no changes are required to the existing `QAPair` data model.
