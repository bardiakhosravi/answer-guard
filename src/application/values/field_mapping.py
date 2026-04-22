from dataclasses import dataclass, field

from src.domain.exceptions import DomainException


@dataclass(frozen=True)
class FieldMapping:
    question_column: str
    answer_column: str
    timestamp_column: str | None = None
    external_id_column: str | None = None
    metadata_columns: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.question_column.strip():
            raise DomainException("FieldMapping: question_column must not be empty")
        if not self.answer_column.strip():
            raise DomainException("FieldMapping: answer_column must not be empty")
