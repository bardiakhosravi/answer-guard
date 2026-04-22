from dataclasses import dataclass, field


@dataclass(frozen=True)
class CaptureResponseCommand:
    question: str
    answer: str
    source_system_id: str
    metadata: dict[str, str] = field(default_factory=dict)
