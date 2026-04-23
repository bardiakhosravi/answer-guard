from unittest.mock import MagicMock

from src.application.commands.capture_response_command import CaptureResponseCommand
from src.application.use_cases.capture_runtime_response_use_case import CaptureRuntimeResponseUseCase
from src.domain.model.qa_pair.ingestion_method import IngestionMethod
from src.domain.model.qa_pair.qa_pair import QAPair


def _make_use_case():
    qa_repo = MagicMock()
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


def test_repeated_identical_captures_are_all_stored():
    """Content-based dedup is gone: identical repeated captures all get stored."""
    use_case, qa_repo = _make_use_case()
    result_a = use_case.execute(_make_command())
    result_b = use_case.execute(_make_command())
    assert qa_repo.save.call_count == 2
    assert result_a.qa_pair_id != result_b.qa_pair_id


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
