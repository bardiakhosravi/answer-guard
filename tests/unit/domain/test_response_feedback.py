import time

import pytest

from src.domain.exceptions import DomainException
from src.domain.model.response_feedback.response_feedback import ResponseFeedback


def _base_kwargs(**overrides):
    defaults = dict(
        source_qa_pair_id="qa-1",
        excerpt="agent said this",
        problem="too long",
        desired_behavior="be concise",
    )
    defaults.update(overrides)
    return defaults


def test_create_with_span():
    fb = ResponseFeedback.create(**_base_kwargs(span_start=0, span_end=5))
    assert fb.span is not None
    assert fb.span.start == 0
    assert fb.span.end == 5


def test_create_without_span_is_whole_response():
    fb = ResponseFeedback.create(**_base_kwargs())
    assert fb.span is None


def test_create_with_only_span_start_raises():
    with pytest.raises(DomainException):
        ResponseFeedback.create(**_base_kwargs(span_start=0))


def test_create_with_only_span_end_raises():
    with pytest.raises(DomainException):
        ResponseFeedback.create(**_base_kwargs(span_end=5))


def test_empty_problem_raises():
    with pytest.raises(DomainException):
        ResponseFeedback.create(**_base_kwargs(problem=""))


def test_whitespace_problem_raises():
    with pytest.raises(DomainException):
        ResponseFeedback.create(**_base_kwargs(problem="   "))


def test_empty_desired_behavior_raises():
    with pytest.raises(DomainException):
        ResponseFeedback.create(**_base_kwargs(desired_behavior=""))


def test_empty_excerpt_raises():
    with pytest.raises(DomainException):
        ResponseFeedback.create(**_base_kwargs(excerpt=""))


def test_empty_source_qa_pair_id_raises():
    with pytest.raises(DomainException):
        ResponseFeedback.create(**_base_kwargs(source_qa_pair_id=""))


def test_fields_trimmed_on_create():
    fb = ResponseFeedback.create(**_base_kwargs(problem="  oops  ", desired_behavior=" be better "))
    assert fb.problem == "oops"
    assert fb.desired_behavior == "be better"


def test_update_refreshes_updated_at():
    fb = ResponseFeedback.create(**_base_kwargs())
    original_updated = fb.updated_at
    time.sleep(0.01)
    fb.update(problem="new problem", desired_behavior="new behavior")
    assert fb.updated_at > original_updated
    assert fb.problem == "new problem"
    assert fb.desired_behavior == "new behavior"


def test_update_preserves_other_state():
    fb = ResponseFeedback.create(**_base_kwargs(span_start=1, span_end=5))
    fb.update(problem="x", desired_behavior="y")
    assert fb.span is not None
    assert fb.span.start == 1
    assert fb.span.end == 5
    assert fb.excerpt == "agent said this"
    assert fb.source_qa_pair_id == "qa-1"


def test_update_empty_problem_raises():
    fb = ResponseFeedback.create(**_base_kwargs())
    with pytest.raises(DomainException):
        fb.update(problem="", desired_behavior="ok")


def test_equality_based_on_id():
    a = ResponseFeedback.create(**_base_kwargs())
    b = ResponseFeedback.create(**_base_kwargs())
    assert a != b
    assert a == a
