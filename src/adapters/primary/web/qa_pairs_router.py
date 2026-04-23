from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from src.application.ports.primary.list_qa_pairs_port import ListQAPairsPort
from src.application.queries.list_qa_pairs_query import ListQAPairsQuery
from src.domain.exceptions import DomainException

router = APIRouter(prefix="/qa-pairs", tags=["qa-pairs"])


class QAPairSummaryBody(BaseModel):
    id: str
    question_text: str
    answer_text: str
    source_system_id: str
    captured_at: str
    source_timestamp: str | None = None
    ingestion_method: str
    external_id: str | None = None
    metadata: dict = {}


class ListQAPairsResponseBody(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[QAPairSummaryBody]


def _get_list_qa_pairs_use_case() -> ListQAPairsPort:
    raise HTTPException(status_code=503, detail="List Q&A pairs use case not wired")


@router.get("", response_model=ListQAPairsResponseBody)
def list_qa_pairs(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    source_system_id: str | None = Query(None),
    search: str | None = Query(None),
    use_case: ListQAPairsPort = Depends(_get_list_qa_pairs_use_case),
) -> ListQAPairsResponseBody:
    try:
        result = use_case.execute(
            ListQAPairsQuery(
                page=page,
                page_size=page_size,
                source_system_id=source_system_id,
                search=search,
            )
        )
        return ListQAPairsResponseBody(
            total=result.total,
            page=result.page,
            page_size=result.page_size,
            items=[
                QAPairSummaryBody(
                    id=item.id,
                    question_text=item.question_text,
                    answer_text=item.answer_text,
                    source_system_id=item.source_system_id,
                    captured_at=item.captured_at,
                    source_timestamp=item.source_timestamp,
                    ingestion_method=item.ingestion_method,
                    external_id=item.external_id,
                    metadata=item.metadata,
                )
                for item in result.items
            ],
        )
    except DomainException as exc:
        raise HTTPException(status_code=400, detail=str(exc))
