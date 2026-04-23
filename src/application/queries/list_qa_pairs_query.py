from dataclasses import dataclass


@dataclass(frozen=True)
class ListQAPairsQuery:
    page: int = 1
    page_size: int = 50
    source_system_id: str | None = None
    search: str | None = None
