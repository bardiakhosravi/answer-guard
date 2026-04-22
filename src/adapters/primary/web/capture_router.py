from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from src.adapters.exceptions import AdapterException
from src.application.commands.capture_response_command import CaptureResponseCommand
from src.application.ports.primary.capture_runtime_response_port import CaptureRuntimeResponsePort
from src.domain.exceptions import DomainException

router = APIRouter(prefix="/capture", tags=["capture"])


class CaptureRequest(BaseModel):
    question: str
    answer: str
    source_system_id: str
    metadata: dict[str, str] = {}


class CaptureResponseBody(BaseModel):
    qa_pair_id: str
    captured_at: str


def _get_capture_use_case() -> CaptureRuntimeResponsePort:
    raise HTTPException(status_code=503, detail="Capture use case not wired")


@router.post("", status_code=status.HTTP_201_CREATED, response_model=CaptureResponseBody)
def capture(
    request: CaptureRequest,
    use_case: CaptureRuntimeResponsePort = Depends(_get_capture_use_case),
) -> CaptureResponseBody:
    try:
        result = use_case.execute(
            CaptureResponseCommand(
                question=request.question,
                answer=request.answer,
                source_system_id=request.source_system_id,
                metadata=request.metadata,
            )
        )
        return CaptureResponseBody(qa_pair_id=result.qa_pair_id, captured_at=result.captured_at)
    except DomainException as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except AdapterException as exc:
        raise HTTPException(status_code=502, detail=str(exc))
