from __future__ import annotations

import hashlib
from dataclasses import dataclass


@dataclass(frozen=True)
class SourceHash:
    """
    Stable identifier used for deduplication.

    Semantics: we dedup on **source row identity**, not on content.
    - If the source row has an `external_id`, the hash is derived from
      `(source_system_id, external_id)`. Re-importing the same source row
      collides; different rows from the same source never collide, even if
      their content is byte-identical.
    - If the source row has no `external_id` (e.g. runtime SDK capture),
      the hash is derived from the `internal_id` (a fresh UUID each time),
      which is unique — so no dedup happens in that case. Every capture
      gets stored.
    """

    value: str

    @classmethod
    def for_external_id(cls, source_system_id: str, external_id: str) -> "SourceHash":
        raw = f"{source_system_id}::{external_id}"
        return cls(value=hashlib.sha256(raw.encode("utf-8")).hexdigest())

    @classmethod
    def for_internal_id(cls, internal_id: str) -> "SourceHash":
        raw = f"internal::{internal_id}"
        return cls(value=hashlib.sha256(raw.encode("utf-8")).hexdigest())
