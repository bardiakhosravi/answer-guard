import pytest

from src.domain.exceptions import DomainException
from src.domain.model.response_feedback.text_span import TextSpan


def test_valid_span():
    span = TextSpan(start=3, end=10)
    assert span.start == 3
    assert span.end == 10


def test_length():
    assert TextSpan(start=2, end=7).length() == 5


def test_covers_middle():
    span = TextSpan(start=5, end=10)
    assert span.covers(5) is True
    assert span.covers(7) is True
    assert span.covers(9) is True


def test_covers_upper_bound_is_exclusive():
    span = TextSpan(start=5, end=10)
    assert span.covers(10) is False


def test_covers_before_start():
    span = TextSpan(start=5, end=10)
    assert span.covers(4) is False


def test_negative_start_raises():
    with pytest.raises(DomainException):
        TextSpan(start=-1, end=5)


def test_end_equal_to_start_raises():
    with pytest.raises(DomainException):
        TextSpan(start=5, end=5)


def test_end_before_start_raises():
    with pytest.raises(DomainException):
        TextSpan(start=10, end=5)


def test_zero_start_allowed():
    span = TextSpan(start=0, end=1)
    assert span.start == 0
