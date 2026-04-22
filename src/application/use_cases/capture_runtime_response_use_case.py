from __future__ import annotations

from src.application.commands.capture_response_command import CaptureResponseCommand
from src.application.ports.primary.capture_runtime_response_port import (
    CaptureResponse,
    CaptureRuntimeResponsePort,
)
from src.domain.model.qa_pair.ingestion_method import IngestionMethod
from src.domain.model.qa_pair.qa_pair import QAPair
from src.domain.model.qa_pair.source_hash import SourceHash
from src.domain.ports.qa_pair_repository import QAPairRepository


class CaptureRuntimeResponseUseCase(CaptureRuntimeResponsePort):
    def __init__(self, qa_pair_repository: QAPairRepository) -> None:
        self._qa_repo = qa_pair_repository

    def execute(self, command: CaptureResponseCommand) -> CaptureResponse:
        candidate_hash = SourceHash.compute(
            command.question, command.answer, command.source_system_id
        )
        existing = self._qa_repo.find_by_hash(candidate_hash)
        if existing:
            return CaptureResponse(
                qa_pair_id=existing.id.value,
                captured_at=existing.captured_at.isoformat(),
            )

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
