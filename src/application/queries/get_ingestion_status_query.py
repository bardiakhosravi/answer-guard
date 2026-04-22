from dataclasses import dataclass


@dataclass(frozen=True)
class GetIngestionStatusQuery:
    source_system_id: str | None = None
    run_id: str | None = None
