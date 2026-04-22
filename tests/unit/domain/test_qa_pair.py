import pytest

from src.domain.exceptions import DomainException
from src.domain.model.qa_pair.ingestion_method import IngestionMethod
from src.domain.model.qa_pair.qa_pair import QAPair
from src.domain.model.qa_pair.source_hash import SourceHash


def test_create_qa_pair_computes_correct_hash():
    pair = QAPair.create("What is X?", "X is Y.", "sys-1", IngestionMethod.HISTORICAL_IMPORT)
    expected = SourceHash.compute("What is X?", "X is Y.", "sys-1")
    assert pair.source_hash == expected


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


def test_identical_pairs_have_same_source_hash():
    a = QAPair.create("Q", "A", "sys-1", IngestionMethod.HISTORICAL_IMPORT)
    b = QAPair.create("Q", "A", "sys-1", IngestionMethod.RUNTIME_CAPTURE)
    assert a.source_hash == b.source_hash


def test_different_pairs_have_different_hash():
    a = QAPair.create("Q1", "A", "sys-1", IngestionMethod.HISTORICAL_IMPORT)
    b = QAPair.create("Q2", "A", "sys-1", IngestionMethod.HISTORICAL_IMPORT)
    assert a.source_hash != b.source_hash


def test_equality_based_on_id():
    a = QAPair.create("Q", "A", "sys-1", IngestionMethod.HISTORICAL_IMPORT)
    b = QAPair.create("Q", "A", "sys-1", IngestionMethod.HISTORICAL_IMPORT)
    assert a != b  # different IDs
    assert a == a


def test_metadata_defaults_to_empty_dict():
    pair = QAPair.create("Q", "A", "sys-1", IngestionMethod.RUNTIME_CAPTURE)
    assert pair.metadata == {}


def test_metadata_stored_when_provided():
    pair = QAPair.create("Q", "A", "sys-1", IngestionMethod.RUNTIME_CAPTURE, metadata={"topic": "billing"})
    assert pair.metadata == {"topic": "billing"}
