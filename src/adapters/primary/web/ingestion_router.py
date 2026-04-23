from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from src.adapters.exceptions import AdapterException
from src.application.commands.import_historical_data_command import ImportHistoricalDataCommand
from src.application.ports.primary.get_ingestion_status_port import (
    GetIngestionStatusPort,
    IngestionRunNotFoundError,
    IngestionStatusResponse,
)
from src.application.ports.primary.discover_schema_port import InvalidRowFilterError
from src.application.ports.primary.import_historical_data_port import (
    FieldMappingValidationError,
    ImportAlreadyRunningError,
    ImportHistoricalDataPort,
)
from src.application.queries.get_ingestion_status_query import GetIngestionStatusQuery
from src.application.values.field_mapping import FieldMapping
from src.application.values.source_connector import SourceConnector
from src.domain.exceptions import DomainException

router = APIRouter(prefix="/ingest", tags=["ingestion"])


# --- Request / Response schemas ---

class FieldMappingRequest(BaseModel):
    question_column: str
    answer_column: str
    timestamp_column: str | None = None
    external_id_column: str | None = None
    metadata_columns: dict[str, str] = {}


class ImportRequest(BaseModel):
    source_system_id: str
    gcp_project_id: str
    dataset_id: str
    table_id: str
    credentials_path: str | None = None
    field_mapping: FieldMappingRequest
    row_filter: str | None = None
    page_size: int = 5000


class ImportResponse(BaseModel):
    ingestion_run_id: str
    status: str
    message: str


class IngestionRunDetailResponse(BaseModel):
    ingestion_run_id: str
    source_system_id: str
    status: str
    started_at: str
    completed_at: str | None
    records_processed: int
    records_skipped: int
    last_checkpoint: int | None
    errors: list[dict]


# --- Dependency placeholders (replaced at startup via app.dependency_overrides) ---

def _get_import_use_case() -> ImportHistoricalDataPort:
    raise HTTPException(status_code=503, detail="Import use case not wired")


def _get_status_use_case() -> GetIngestionStatusPort:
    raise HTTPException(status_code=503, detail="Status use case not wired")


# --- Endpoints ---

@router.post("/import", status_code=status.HTTP_202_ACCEPTED, response_model=ImportResponse)
def trigger_import(
    request: ImportRequest,
    use_case: ImportHistoricalDataPort = Depends(_get_import_use_case),
) -> ImportResponse:
    try:
        connector = SourceConnector(
            source_system_id=request.source_system_id,
            gcp_project_id=request.gcp_project_id,
            dataset_id=request.dataset_id,
            table_id=request.table_id,
            credentials_path=request.credentials_path,
            field_mapping=FieldMapping(
                question_column=request.field_mapping.question_column,
                answer_column=request.field_mapping.answer_column,
                timestamp_column=request.field_mapping.timestamp_column,
                external_id_column=request.field_mapping.external_id_column,
                metadata_columns=request.field_mapping.metadata_columns,
            ),
            row_filter=request.row_filter,
            page_size=request.page_size,
        )
        result = use_case.execute(ImportHistoricalDataCommand(source_connector=connector))
        return ImportResponse(
            ingestion_run_id=result.ingestion_run_id,
            status=result.status,
            message=result.message,
        )
    except InvalidRowFilterError as exc:
        raise HTTPException(
            status_code=400,
            detail={"error": "INVALID_ROW_FILTER", "field": "row_filter", "detail": str(exc)},
        )
    except FieldMappingValidationError as exc:
        raise HTTPException(status_code=400, detail={"error": "INVALID_FIELD_MAPPING", "detail": str(exc)})
    except ImportAlreadyRunningError as exc:
        raise HTTPException(status_code=409, detail={"error": "IMPORT_ALREADY_RUNNING", "detail": str(exc)})
    except DomainException as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except AdapterException as exc:
        raise HTTPException(status_code=502, detail=str(exc))


@router.get("/status", response_model=dict)
def get_overall_status(
    source_system_id: str | None = None,
    use_case: GetIngestionStatusPort = Depends(_get_status_use_case),
) -> dict:
    try:
        result: IngestionStatusResponse = use_case.execute(
            GetIngestionStatusQuery(source_system_id=source_system_id)
        )
        return {
            "total_qa_pairs": result.total_qa_pairs,
            "sources": [
                {
                    "source_system_id": s.source_system_id,
                    "total_records": s.total_records,
                    "last_ingested_at": s.last_ingested_at,
                    "runtime_captures_last_24h": s.runtime_captures_last_24h,
                    "last_import_run": (
                        {
                            "run_id": s.last_import_run.run_id,
                            "status": s.last_import_run.status,
                            "records_processed": s.last_import_run.records_processed,
                            "records_skipped": s.last_import_run.records_skipped,
                            "started_at": s.last_import_run.started_at,
                            "completed_at": s.last_import_run.completed_at,
                        }
                        if s.last_import_run
                        else None
                    ),
                }
                for s in result.sources
            ],
        }
    except DomainException as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/status/{run_id}", response_model=IngestionRunDetailResponse)
def get_run_status(
    run_id: str,
    use_case: GetIngestionStatusPort = Depends(_get_status_use_case),
) -> IngestionRunDetailResponse:
    try:
        result = use_case.execute(GetIngestionStatusQuery(run_id=run_id))
        src = result.sources[0]
        run = src.last_import_run
        assert run is not None
        return IngestionRunDetailResponse(
            ingestion_run_id=run.run_id,
            source_system_id=src.source_system_id,
            status=run.status,
            started_at=run.started_at,
            completed_at=run.completed_at,
            records_processed=run.records_processed,
            records_skipped=run.records_skipped,
            last_checkpoint=run.last_checkpoint,
            errors=run.errors,
        )
    except IngestionRunNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except DomainException as exc:
        raise HTTPException(status_code=400, detail=str(exc))
