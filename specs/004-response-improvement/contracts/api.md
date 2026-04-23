# API Contracts: Response Improvement (Capture)

**Feature**: 004-response-improvement
**Date**: 2026-04-23

All endpoints are prefixed with `/v1`.

---

## POST /v1/guidelines

Create a new guideline attached to a specific Q&A pair.

### Request

```json
{
  "qa_pair_id": "b2c3d4e5-...",
  "excerpt": "Sorry, I don't have access to that information.",
  "span_start": 142,
  "span_end": 192,
  "problem": "Agent deflects instead of offering an alternative.",
  "desired_behavior": "Acknowledge the limitation and suggest 'Contact support@example.com for account-specific help.'"
}
```

### Response — 201 Created

```json
{
  "id": "g1a2b3c4-...",
  "qa_pair_id": "b2c3d4e5-...",
  "excerpt": "Sorry, I don't have access to that information.",
  "span_start": 142,
  "span_end": 192,
  "problem": "Agent deflects instead of offering an alternative.",
  "desired_behavior": "Acknowledge the limitation and suggest 'Contact support@example.com for account-specific help.'",
  "created_at": "2026-04-23T12:34:56Z",
  "updated_at": "2026-04-23T12:34:56Z"
}
```

### Error responses

| Status | When |
|---|---|
| 400 | Empty `problem`, empty `desired_behavior`, invalid span (`end ≤ start`, negative `start`), or missing `qa_pair_id` |

---

## GET /v1/guidelines

Paginated list of all guidelines.

### Query parameters

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `page` | integer | ❌ | 1 | 1-indexed page number |
| `page_size` | integer | ❌ | 50 | Items per page, max 500 |
| `search` | string | ❌ | none | Case-insensitive substring match on `problem`, `desired_behavior`, or `excerpt` |

### Response — 200 OK

```json
{
  "total": 42,
  "page": 1,
  "page_size": 50,
  "items": [
    {
      "id": "g1a2b3c4-...",
      "qa_pair_id": "b2c3d4e5-...",
      "excerpt": "...",
      "span_start": 142,
      "span_end": 192,
      "problem": "...",
      "desired_behavior": "...",
      "created_at": "2026-04-23T12:34:56Z",
      "updated_at": "2026-04-23T12:34:56Z"
    }
  ]
}
```

Ordered by `created_at DESC`.

---

## GET /v1/guidelines/{guideline_id}

Fetch a single guideline by ID.

### Response — 200 OK

Same shape as an item in the list.

### Error responses

| Status | When |
|---|---|
| 404 | No guideline with that ID |

---

## GET /v1/qa-pairs/{qa_pair_id}/guidelines

Fetch all guidelines attached to a specific Q&A pair. Returned in natural `span_start` order so the UI can render them alongside the response text.

### Response — 200 OK

```json
{
  "qa_pair_id": "b2c3d4e5-...",
  "items": [
    { "id": "g1...", "excerpt": "...", "span_start": 0, "span_end": 42, ... },
    { "id": "g2...", "excerpt": "...", "span_start": 100, "span_end": 150, ... }
  ]
}
```

---

## PATCH /v1/guidelines/{guideline_id}

Update the `problem` and/or `desired_behavior` of an existing guideline. Span and excerpt are immutable.

### Request

```json
{
  "problem": "Updated text",
  "desired_behavior": "Updated text"
}
```

Either field may be omitted to leave it unchanged. At least one must be supplied. Empty strings are rejected.

### Response — 200 OK

Full guideline body with `updated_at` refreshed.

### Error responses

| Status | When |
|---|---|
| 400 | Both fields omitted, or any supplied field is empty |
| 404 | No guideline with that ID |

---

## DELETE /v1/guidelines/{guideline_id}

Permanently delete a guideline. Idempotent.

### Response — 204 No Content

### Error responses

None — a delete against a non-existent ID still returns 204. (Idempotent semantics avoid frontend races.)
