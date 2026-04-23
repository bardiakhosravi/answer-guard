---
sidebar_position: 1
---

# Response Feedback

A **ResponseFeedback** record is a single piece of PM-authored feedback about a specific agent answer. It captures:

- **What the PM was looking at** — either a highlighted selection from the answer or the whole answer
- **What's wrong** — the PM's description of the problem
- **How the agent should behave instead** — the PM's description of the desired outcome
- **The source Q&A** — a reference back to the original `QAPair` the feedback is about, purely for provenance

ResponseFeedback is an **independent entity**. It references the source Q&A pair by ID so we can trace feedback back to what it was about, but it is not owned by the Q&A pair. A Q&A pair may have zero, one, or many feedback records written about it; each of those feedback records stands on its own.

## What we do with it

Right now, nothing — the feature only captures and stores feedback. A future engine will use this data to improve agent responses (synthesize reusable guidelines, gate future responses, train prompts, etc.). We've deliberately separated capture from enforcement so teams can start collecting PM input immediately, even while the enforcement strategy is still being designed.

## Capture flow

From the AnswerGuard desktop app:

1. Open the **Data** screen and pick a Q&A pair from the list
2. In the Answer section, either:
   - **Select** a passage with your mouse and click **Improve selected**, or
   - Click **Improve whole response** to give feedback on the entire answer
3. In the modal, fill in two fields:
   - *What's wrong with this response?*
   - *How should the agent behave instead?*
4. Click **Save guideline**

The feedback is stored and a toast confirms success. Navigate to **Response Feedback** in the left sidebar to browse, search, edit, or delete any captured record.

## Data model

| Field | Type | Description |
|---|---|---|
| `id` | UUID | AnswerGuard-assigned identifier for the feedback record |
| `source_qa_pair_id` | UUID | ID of the `QAPair` the feedback is about (provenance only — no foreign key, no cascade) |
| `excerpt` | Text | The text the PM was commenting on — either the highlighted selection or the whole answer |
| `span_start`, `span_end` | int \| null | Character offsets of the selection in the source answer. Both `null` when the PM gave feedback on the whole response |
| `problem` | Text | What's wrong with the response |
| `desired_behavior` | Text | What the agent should do instead |
| `created_at`, `updated_at` | timestamp | Audit timestamps |

See the [API reference](/docs/reference/api) for the HTTP endpoints that back these operations.
