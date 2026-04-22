from unittest.mock import MagicMock

from src.application.commands.capture_response_command import CaptureResponseCommand
from src.application.use_cases.capture_runtime_response_use_case import CaptureRuntimeResponseUseCase
from src.domain.model.qa_pair.ingestion_method import IngestionMethod
from src.domain.model.qa_pair.qa_pair import QAPair


def _make_use_case(qa_repo=None):
    qa_repo = qa_repo or MagicMock()
    qa_repo.find_by_hash.return_value = None
    return CaptureRuntimeResponseUseCase(qa_repo), qa_repo


def _make_command(**kwargs) -> CaptureResponseCommand:
    return CaptureResponseCommand(
        question=kwargs.get("question", "What is X?"),
        answer=kwargs.get("answer", "X is Y."),
        source_system_id=kwargs.get("source_system_id", "sys-1"),
        metadata=kwargs.get("metadata", {}),
    )


def test_successful_capture_stores_with_runtime_method():
    use_case, qa_repo = _make_use_case()
    use_case.execute(_make_command())
    saved_pair: QAPair = qa_repo.save.call_args[0][0]
    assert saved_pair.ingestion_method == IngestionMethod.RUNTIME_CAPTURE


def test_successful_capture_returns_qa_pair_id():
    use_case, qa_repo = _make_use_case()
    result = use_case.execute(_make_command())
    assert result.qa_pair_id is not None
    assert len(result.qa_pair_id) == 36  # UUID format


def test_duplicate_returns_existing_id_without_saving():
    use_case, qa_repo = _make_use_case()
    existing = QAPair.create("What is X?", "X is Y.", "sys-1", IngestionMethod.HISTORICAL_IMPORT)
    qa_repo.find_by_hash.return_value = existing

    result = use_case.execute(_make_command())

    assert result.qa_pair_id == existing.id.value
    qa_repo.save.assert_not_called()


def test_metadata_stored_with_pair():
    use_case, qa_repo = _make_use_case()
    use_case.execute(_make_command(metadata={"topic": "billing"}))
    saved_pair: QAPair = qa_repo.save.call_args[0][0]
    assert saved_pair.metadata == {"topic": "billing"}


def test_capture_result_includes_captured_at():
    use_case, qa_repo = _make_use_case()
    result = use_case.execute(_make_command())
    assert result.captured_at is not None
    assert "T" in result.captured_at  # ISO format contains T separator
