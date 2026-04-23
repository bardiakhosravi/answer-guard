# UI Contract: Response Improvement

**Feature**: 004-response-improvement
**Date**: 2026-04-23

Extensions and additions to the existing desktop app. Every item below must be reachable via the navigation rules stated.

---

## Extension: Data view detail panel (`QAPairDetail`)

### New elements

- **Answer text is selectable.** Any contiguous substring of the agent's response can be selected using native text selection (mouse drag or keyboard with shift+arrows).
- **Floating "Improve" button.** When a non-empty selection exists within the answer text, a small floating button labelled **Improve** appears near the end of the selection. Clicking it opens the Improvement Form modal prefilled with the selected excerpt and span.
- **"Improve whole response" button.** A persistent button shown below the answer (or in the detail header) that opens the Improvement Form with the full answer text preselected.
- **Highlight overlay.** For every guideline attached to this Q&A pair, the corresponding character range of the answer text is rendered with a background highlight. Overlapping ranges are unioned visually (one colour).
- **Guidelines sidebar section.** A new right-side section (below the metadata block) titled "Guidelines (N)" lists all guidelines for this record, each showing:
  - A 60-character preview of the highlighted excerpt
  - The first line of `problem`
  - Created-at timestamp
  - Clicking a list item scrolls the answer text to the corresponding highlight and focuses it
  - Each entry has **Edit** and **Delete** icon actions

### Behaviour rules

- Selection in the question text does **not** show the Improve button (v1 only annotates agent responses).
- If the detail panel is re-rendered for a different Q&A pair, the selection and floating button reset.
- When no guidelines exist for the record, the sidebar section shows "No guidelines yet — select text in the response and click Improve to add one."

---

## New component: Improvement Form Modal

Opened from the **Improve** button (with-selection) or **Improve whole response** button (no-selection). Modal over the main content.

### Must contain

- Modal title: "Improve this response"
- Read-only excerpt preview — labelled "Highlighted text" — showing the captured span inside a bordered box with monospace font
- If the span covers the whole response, the label reads "Whole response" and the box shows the full answer
- Input: **What's wrong?** (multi-line text, required, minimum 3 characters after trim)
- Input: **How should the agent behave instead?** (multi-line text, required, minimum 3 characters after trim)
- Footer buttons: **Cancel** (discards input with confirmation if text entered) and **Save** (primary; disabled until both required fields are non-empty)
- On successful save: modal closes, the record's guidelines sidebar updates with the new entry, the corresponding span in the answer text gets the highlight overlay
- On save failure: the form stays open, shows an inline error at the top, preserves all user input, and the Save button re-enables

### Edit mode

The same modal is reused in "edit mode" when the user clicks Edit on a guideline. Title changes to "Edit guideline". The excerpt preview is still shown (read-only — spans cannot be edited). Only `problem` and `desired_behavior` are editable. Footer shows **Save changes** instead of **Save**.

---

## New screen: Guidelines (`/guidelines`)

New top-level screen, with a sidebar entry in the AppShell.

### Layout

Two-column layout (same pattern as the Data screen):

- **Left column** (fixed width): paginated list
- **Right column** (flexible): detail panel

### Top bar

- Screen title: "Guidelines"
- Stats: `N total guidelines`
- Search input (debounced 300ms, searches `problem` + `desired_behavior` + `excerpt`)

### List column

- Each row shows:
  - Truncated `problem` (max 2 lines)
  - Excerpt preview (1 line, italic)
  - Created-at timestamp
- Active row highlighted
- Pagination controls (prev / next / page number)
- Empty state: "No guidelines yet. Go to the Data view, select text in any response, and click Improve to create your first guideline."

### Detail column (shown when a row is selected)

- Full `problem` text
- Full `desired_behavior` text
- Highlighted excerpt in a bordered monospace box
- Timestamps: created at, updated at (if different)
- **View source record →** link that navigates to the Data view, opens the source Q&A pair, and scrolls to the highlight. If the source record no longer exists, the link is replaced with the label "Source record no longer available".
- **Edit** button → opens the Improvement Form Modal in edit mode
- **Delete** button → opens a confirmation dialog ("Delete this guideline? This cannot be undone.") with Cancel / Delete actions

### Sidebar navigation

AppShell gains a new "Guidelines" entry. It is enabled from the moment the app connects to a configured server (not gated on having created guidelines yet — the empty state handles that).

---

## API usage summary (for reference)

| Action | Endpoint |
|---|---|
| List for screen | `GET /v1/guidelines?page=&search=` |
| Load for record | `GET /v1/qa-pairs/{qa_pair_id}/guidelines` |
| Create | `POST /v1/guidelines` |
| Edit | `PATCH /v1/guidelines/{id}` |
| Delete | `DELETE /v1/guidelines/{id}` |
| Navigate to source | uses existing `GET /v1/qa-pairs?search=<id>` or a direct fetch endpoint |
