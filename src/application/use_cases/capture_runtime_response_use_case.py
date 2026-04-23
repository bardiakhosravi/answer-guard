from __future__ import annotations

from src.application.commands.capture_response_command import CaptureResponseCommand
from src.application.ports.primary.capture_runtime_response_port import (
    CaptureResponse,
    CaptureRuntimeResponsePort,
)
from src.domain.model.qa_pair.ingestion_method import IngestionMethod
from src.domain.model.qa_pair.qa_pair import QAPair
from src.domain.ports.qa_pair_repository import QAPairRepository


class CaptureRuntimeResponseUseCase(CaptureRuntimeResponsePort):
    def __init__(self, qa_pair_repository: QAPairRepository) -> None:
        self._qa_repo = qa_pair_repository

    def execute(self, command: CaptureResponseCommand) -> CaptureResponse:
        # Runtime captures don't carry an external_id, so each QAPair.create()
        # produces a unique source_hash (derived from the internal UUID). No
        # content-based dedup — two identical user questions captured a minute
        # apart are two distinct interactions and both get stored.
        qa_pair = QAPair.create(
            question_text=command.question,
            answer_text=command.answer,
            source_system_id=command.source_system_id,
            ingestion_method=IngestionMethod.RUNTIME_CAPTURE,
            metadata=dict(command.metadata),
        )
        self._qa_repo.save(qa_pair)
        return CaptureResponse(
            qa_pair_id=qa_pair.id.value,
            captured_at=qa_pair.captured_at.isoformat(),
        )
