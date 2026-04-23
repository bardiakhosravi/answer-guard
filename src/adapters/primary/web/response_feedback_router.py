from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from pydantic import BaseModel, Field

from src.application.commands.delete_response_feedback_command import (
    DeleteResponseFeedbackCommand,
)
from src.application.commands.submit_response_feedback_command import (
    SubmitResponseFeedbackCommand,
)
from src.application.commands.update_response_feedback_command import (
    UpdateResponseFeedbackCommand,
)
from src.application.ports.primary.delete_response_feedback_port import (
    DeleteResponseFeedbackPort,
)
from src.application.ports.primary.get_response_feedback_port import (
    GetResponseFeedbackPort,
    ResponseFeedbackNotFoundError,
)
from src.application.ports.primary.list_response_feedback_port import (
    ListResponseFeedbackPort,
)
from src.application.ports.primary.submit_response_feedback_port import (
    SubmitResponseFeedbackPort,
)
from src.application.ports.primary.update_response_feedback_port import (
    UpdateResponseFeedbackPort,
)
from src.application.queries.list_response_feedback_query import (
    ListResponseFeedbackQuery,
)
from src.domain.exceptions import DomainException

router = APIRouter(prefix="/response-feedback", tags=["response-feedback"])


class SubmitResponseFeedbackRequest(BaseModel):
    source_qa_pair_id: str = Field(min_length=1)
    excerpt: str = Field(min_length=1)
    problem: str = Field(min_length=1)
    desired_behavior: str = Field(min_length=1)
    span_start: int | None = Field(default=None, ge=0)
    span_end: int | None = Field(default=None, ge=1)


class ResponseFeedbackBody(BaseModel):
    id: str
    source_qa_pair_id: str
    excerpt: str
    span_start: int | None
    span_end: int | None
    problem: str
    desired_behavior: str
    created_at: str
    updated_at: str


class UpdateResponseFeedbackRequest(BaseModel):
    problem: str | None = None
    desired_behavior: str | None = None


def _get_submit_use_case() -> SubmitResponseFeedbackPort:
    raise HTTPException(status_code=503, detail="Submit response feedback use case not wired")


def _get_list_use_case() -> ListResponseFeedbackPort:
    raise HTTPException(status_code=503, detail="List response feedback use case not wired")


def _get_get_use_case() -> GetResponseFeedbackPort:
    raise HTTPException(status_code=503, detail="Get response feedback use case not wired")


def _get_update_use_case() -> UpdateResponseFeedbackPort:
    raise HTTPException(status_code=503, detail="Update response feedback use case not wired")


def _get_delete_use_case() -> DeleteResponseFeedbackPort:
    raise HTTPException(status_code=503, detail="Delete response feedback use case not wired")


def _to_body(result) -> "ResponseFeedbackBody":
    return ResponseFeedbackBody(
        id=result.id,
        source_qa_pair_id=result.source_qa_pair_id,
        excerpt=result.excerpt,
        span_start=result.span_start,
        span_end=result.span_end,
        problem=result.problem,
        desired_behavior=result.desired_behavior,
        created_at=result.created_at,
        updated_at=result.updated_at,
    )


class ListResponseFeedbackResponseBody(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[ResponseFeedbackBody]


@router.post("", response_model=ResponseFeedbackBody, status_code=201)
def submit_response_feedback(
    request: SubmitResponseFeedbackRequest,
    use_case: SubmitResponseFeedbackPort = Depends(_get_submit_use_case),
) -> ResponseFeedbackBody:
    try:
        result = use_case.execute(
            SubmitResponseFeedbackCommand(
                source_qa_pair_id=request.source_qa_pair_id,
                excerpt=request.excerpt,
                problem=request.problem,
                desired_behavior=request.desired_behavior,
                span_start=request.span_start,
                span_end=request.span_end,
            )
        )
    except DomainException as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return ResponseFeedbackBody(
        id=result.id,
        source_qa_pair_id=result.source_qa_pair_id,
        excerpt=result.excerpt,
        span_start=result.span_start,
        span_end=result.span_end,
        problem=result.problem,
        desired_behavior=result.desired_behavior,
        created_at=result.created_at,
        updated_at=result.updated_at,
    )


@router.get("", response_model=ListResponseFeedbackResponseBody)
def list_response_feedback(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    search: str | None = Query(None),
    use_case: ListResponseFeedbackPort = Depends(_get_list_use_case),
) -> ListResponseFeedbackResponseBody:
    result = use_case.execute(
        ListResponseFeedbackQuery(page=page, page_size=page_size, search=search)
    )
    return ListResponseFeedbackResponseBody(
        total=result.total,
        page=result.page,
        page_size=result.page_size,
        items=[
            ResponseFeedbackBody(
                id=item.id,
                source_qa_pair_id=item.source_qa_pair_id,
                excerpt=item.excerpt,
                span_start=item.span_start,
                span_end=item.span_end,
                problem=item.problem,
                desired_behavior=item.desired_behavior,
                created_at=item.created_at,
                updated_at=item.updated_at,
            )
            for item in result.items
        ],
    )


@router.get("/{feedback_id}", response_model=ResponseFeedbackBody)
def get_response_feedback(
    feedback_id: str,
    use_case: GetResponseFeedbackPort = Depends(_get_get_use_case),
) -> ResponseFeedbackBody:
    try:
        result = use_case.execute(feedback_id)
    except ResponseFeedbackNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except DomainException as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return _to_body(result)


@router.patch("/{feedback_id}", response_model=ResponseFeedbackBody)
def update_response_feedback(
    feedback_id: str,
    request: UpdateResponseFeedbackRequest,
    use_case: UpdateResponseFeedbackPort = Depends(_get_update_use_case),
) -> ResponseFeedbackBody:
    try:
        result = use_case.execute(
            UpdateResponseFeedbackCommand(
                feedback_id=feedback_id,
                problem=request.problem,
                desired_behavior=request.desired_behavior,
            )
        )
    except ResponseFeedbackNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except DomainException as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return _to_body(result)


@router.delete("/{feedback_id}", status_code=204)
def delete_response_feedback(
    feedback_id: str,
    use_case: DeleteResponseFeedbackPort = Depends(_get_delete_use_case),
) -> Response:
    use_case.execute(DeleteResponseFeedbackCommand(feedback_id=feedback_id))
    return Response(status_code=204)
