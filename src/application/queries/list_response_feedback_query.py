from dataclasses import dataclass


@dataclass(frozen=True)
class ListResponseFeedbackQuery:
    page: int = 1
    page_size: int = 50
    search: str | None = None
