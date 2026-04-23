from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from src.adapters.exceptions import AdapterException
from src.application.commands.discover_schema_command import DiscoverSchemaCommand
from src.application.ports.primary.discover_schema_port import (
    DiscoverSchemaPort,
    InvalidRowFilterError,
)
from src.domain.exceptions import DomainException

router = APIRouter(prefix="/sources", tags=["sources"])


class DiscoverSchemaRequest(BaseModel):
    gcp_project_id: str
    dataset_id: str
    table_id: str
    credentials_path: str | None = None
    row_filter: str | None = None


class DiscoveredColumnBody(BaseModel):
    name: str
    type: str


class DiscoverSchemaResponseBody(BaseModel):
    columns: list[DiscoveredColumnBody]


def _get_discover_schema_use_case() -> DiscoverSchemaPort:
    raise HTTPException(status_code=503, detail="Schema discovery use case not wired")


@router.post(
    "/discover-schema",
    status_code=status.HTTP_200_OK,
    response_model=DiscoverSchemaResponseBody,
)
def discover_schema(
    request: DiscoverSchemaRequest,
    use_case: DiscoverSchemaPort = Depends(_get_discover_schema_use_case),
) -> DiscoverSchemaResponseBody:
    try:
        result = use_case.execute(
            DiscoverSchemaCommand(
                gcp_project_id=request.gcp_project_id,
                dataset_id=request.dataset_id,
                table_id=request.table_id,
                credentials_path=request.credentials_path,
                row_filter=request.row_filter,
            )
        )
        return DiscoverSchemaResponseBody(
            columns=[DiscoveredColumnBody(name=c.name, type=c.type) for c in result.columns],
        )
    except InvalidRowFilterError as exc:
        raise HTTPException(
            status_code=400,
            detail={"error": "INVALID_ROW_FILTER", "field": "row_filter", "detail": str(exc)},
        )
    except DomainException as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except AdapterException as exc:
        raise HTTPException(status_code=502, detail=str(exc))
