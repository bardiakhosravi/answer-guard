import pytest

from src.domain.exceptions import DomainException
from src.domain.model.qa_pair.ingestion_method import IngestionMethod
from src.domain.model.qa_pair.qa_pair import QAPair
from src.domain.model.qa_pair.source_hash import SourceHash


def test_create_qa_pair_without_external_id_has_unique_hash():
    """Without an external_id, every QAPair.create() gets a unique hash (no content dedup)."""
    a = QAPair.create("Q", "A", "sys-1", IngestionMethod.RUNTIME_CAPTURE)
    b = QAPair.create("Q", "A", "sys-1", IngestionMethod.RUNTIME_CAPTURE)
    assert a.source_hash != b.source_hash


def test_create_qa_pair_with_same_external_id_has_same_hash():
    """Two rows from the same source with the same external_id are the same logical row."""
    a = QAPair.create("Q1", "A1", "sys-1", IngestionMethod.HISTORICAL_IMPORT, external_id="ext-42")
    b = QAPair.create("Q2", "A2", "sys-1", IngestionMethod.HISTORICAL_IMPORT, external_id="ext-42")
    # Content differs, but same source + same external_id → same hash
    assert a.source_hash == b.source_hash


def test_create_qa_pair_with_different_external_ids_has_different_hashes():
    a = QAPair.create("Q", "A", "sys-1", IngestionMethod.HISTORICAL_IMPORT, external_id="ext-1")
    b = QAPair.create("Q", "A", "sys-1", IngestionMethod.HISTORICAL_IMPORT, external_id="ext-2")
    assert a.source_hash != b.source_hash


def test_same_external_id_but_different_sources_have_different_hashes():
    a = QAPair.create("Q", "A", "sys-1", IngestionMethod.HISTORICAL_IMPORT, external_id="ext-42")
    b = QAPair.create("Q", "A", "sys-2", IngestionMethod.HISTORICAL_IMPORT, external_id="ext-42")
    assert a.source_hash != b.source_hash


def test_identical_content_but_no_external_id_are_not_deduped():
    """Real-world: 100 different users ask the same question — all 100 are stored."""
    hashes = {
        QAPair.create("Cancel my subscription", "Go to Settings.", "sys-1", IngestionMethod.RUNTIME_CAPTURE).source_hash
        for _ in range(100)
    }
    assert len(hashes) == 100  # every one is unique


def test_source_hash_factory_produces_stable_output():
    a = SourceHash.for_external_id("sys-1", "ext-42")
    b = SourceHash.for_external_id("sys-1", "ext-42")
    assert a == b


def test_create_qa_pair_empty_question_raises():
    with pytest.raises(DomainException):
        QAPair.create("", "answer", "sys-1", IngestionMethod.RUNTIME_CAPTURE)


def test_create_qa_pair_whitespace_question_raises():
    with pytest.raises(DomainException):
        QAPair.create("   ", "answer", "sys-1", IngestionMethod.RUNTIME_CAPTURE)


def test_create_qa_pair_empty_answer_raises():
    with pytest.raises(DomainException):
        QAPair.create("question", "", "sys-1", IngestionMethod.RUNTIME_CAPTURE)


def test_create_qa_pair_empty_source_system_raises():
    with pytest.raises(DomainException):
        QAPair.create("question", "answer", "", IngestionMethod.RUNTIME_CAPTURE)


def test_equality_based_on_id():
    a = QAPair.create("Q", "A", "sys-1", IngestionMethod.HISTORICAL_IMPORT)
    b = QAPair.create("Q", "A", "sys-1", IngestionMethod.HISTORICAL_IMPORT)
    assert a != b  # different ids
    assert a == a


def test_metadata_defaults_to_empty_dict():
    pair = QAPair.create("Q", "A", "sys-1", IngestionMethod.RUNTIME_CAPTURE)
    assert pair.metadata == {}


def test_metadata_stored_when_provided():
    pair = QAPair.create("Q", "A", "sys-1", IngestionMethod.RUNTIME_CAPTURE, metadata={"topic": "billing"})
    assert pair.metadata == {"topic": "billing"}
