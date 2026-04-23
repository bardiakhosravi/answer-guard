# Data Model: Response Improvement (Capture)

**Feature**: 004-response-improvement
**Date**: 2026-04-23

---

## Aggregate: `ResponseFeedback`

PM feedback captured against an agent's answer. Independent aggregate — references the source `QAPair` by identity for provenance, but is **not** owned by it. The QAPair is what the PM was looking at when they submitted the feedback; what we later do with this feedback (synthesize guidelines, run enforcement, train prompts, etc.) is a separate future concern.

### Entity: ResponseFeedback (aggregate root)

| Field | Type | Constraints | Description |
|---|---|---|---|
| `id` | UUID | PK, auto-generated | AnswerGuard-assigned identifier |
| `source_qa_pair_id` | UUID | NOT NULL, indexed | ID of the source QAPair — provenance only (no FK, cross-aggregate reference by identity) |
| `excerpt` | Text | NOT NULL | The text the PM was giving feedback on — either their highlighted selection or the full answer |
| `span_start` | Integer | nullable, ≥0 when set | Character offset of the selection start in the source answer; null when the PM gave feedback on the whole answer |
| `span_end` | Integer | nullable, > `span_start` when set | Character offset of the selection end (exclusive); null when the PM gave feedback on the whole answer |
| `problem` | Text | NOT NULL, non-empty | The PM's description of what's wrong with this response |
| `desired_behavior` | Text | NOT NULL, non-empty | The PM's description of what the agent should do instead |
| `created_at` | DateTime (UTC) | NOT NULL | When the feedback was submitted |
| `updated_at` | DateTime (UTC) | NOT NULL | When the feedback was last modified (equal to `created_at` initially) |

### Value Object: `TextSpan`

Optional on `ResponseFeedback`. Present only when the PM selected a portion of the answer rather than giving feedback on the whole response.

| Field | Type | Validation |
|---|---|---|
| `start` | int | `≥ 0` |
| `end` | int | `> start` |

Methods: `length() -> int`, `covers(offset: int) -> bool`.

### Invariants enforced on creation

- `problem` is non-empty after trimming whitespace
- `desired_behavior` is non-empty after trimming whitespace
- `excerpt` is non-empty
- `source_qa_pair_id` is non-empty
- `span_start` and `span_end` are either both set (valid TextSpan) or both null (whole-response feedback)

### Factory method

```python
ResponseFeedback.create(
    source_qa_pair_id: str,
    excerpt: str,
    problem: str,
    desired_behavior: str,
    span_start: int | None = None,
    span_end: int | None = None,
) -> ResponseFeedback
```

Generates a new `ResponseFeedbackId`, sets `created_at` and `updated_at` to now (UTC), validates invariants, raises `DomainException` on violation.

### Mutation methods

- `update(problem: str, desired_behavior: str) -> None` — updates the two text fields and bumps `updated_at`. Span and excerpt are immutable once captured.

---

## Database Schema (PostgreSQL / SQLite)

```sql
CREATE TABLE response_feedback (
    id                 UUID PRIMARY KEY,
    source_qa_pair_id  UUID NOT NULL,
    excerpt            TEXT NOT NULL,
    span_start         INTEGER,
    span_end           INTEGER,
    problem            TEXT NOT NULL,
    desired_behavior   TEXT NOT NULL,
    created_at         TIMESTAMPTZ NOT NULL,
    updated_at         TIMESTAMPTZ NOT NULL,
    CONSTRAINT ck_response_feedback_span_valid CHECK (
        (span_start IS NULL AND span_end IS NULL)
        OR (span_start >= 0 AND span_end > span_start)
    )
);

CREATE INDEX idx_response_feedback_source_qa_pair_id ON response_feedback(source_qa_pair_id);
CREATE INDEX idx_response_feedback_created_at ON response_feedback(created_at DESC);
```

Deliberately no foreign key on `source_qa_pair_id` — the cross-aggregate relationship is by identity, and feedback records survive deletion of their source QAPair (provenance may become stale but the PM's input remains valuable).

---

## Ports (Hexagonal)

### Domain port: `ResponseFeedbackRepository` (in `src/domain/ports/`)

```python
class ResponseFeedbackRepository(ABC):
    def save(self, feedback: ResponseFeedback) -> None: ...
    def find_by_id(self, feedback_id: ResponseFeedbackId) -> Optional[ResponseFeedback]: ...
    def list_paginated(
        self,
        page: int,
        page_size: int,
        search: str | None = None,
    ) -> tuple[list[ResponseFeedback], int]: ...
    def delete(self, feedback_id: ResponseFeedbackId) -> bool: ...
```

### Application primary ports

- `SubmitResponseFeedbackPort` — takes a `SubmitResponseFeedbackCommand`, returns a `ResponseFeedbackResponse`
- (US2) `ListResponseFeedbackPort` — paginated list with search, for the review screen
- (US3) `GetResponseFeedbackPort`, `UpdateResponseFeedbackPort`, `DeleteResponseFeedbackPort`

### Domain exceptions

- `ResponseFeedbackNotFoundError(DomainException)` — defined alongside the get port when introduced in US3
- All other invariant violations surface via the existing `DomainException`
