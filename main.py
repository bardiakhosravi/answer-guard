from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.adapters.primary.web import (
    capture_router,
    ingestion_router,
    qa_pairs_router,
    response_feedback_router,
    sources_router,
)
from src.application.ports.primary.capture_runtime_response_port import (
    CaptureRuntimeResponsePort,
)
from src.application.ports.primary.discover_schema_port import DiscoverSchemaPort
from src.application.ports.primary.get_ingestion_status_port import GetIngestionStatusPort
from src.application.ports.primary.import_historical_data_port import (
    ImportHistoricalDataPort,
)
from src.application.ports.primary.list_qa_pairs_port import ListQAPairsPort
from src.configuration.app_settings import get_settings
from src.configuration.di_container import DIContainer


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    settings = get_settings()
    container = DIContainer(settings)
    app.state.container = container

    # Wire FastAPI dependency overrides for each primary port
    app.dependency_overrides[ingestion_router._get_import_use_case] = (
        container.import_historical_data_use_case
    )
    app.dependency_overrides[ingestion_router._get_status_use_case] = (
        container.get_ingestion_status_use_case
    )
    app.dependency_overrides[capture_router._get_capture_use_case] = (
        container.capture_runtime_response_use_case
    )
    app.dependency_overrides[sources_router._get_discover_schema_use_case] = (
        container.discover_schema_use_case
    )
    app.dependency_overrides[qa_pairs_router._get_list_qa_pairs_use_case] = (
        container.list_qa_pairs_use_case
    )
    app.dependency_overrides[response_feedback_router._get_submit_use_case] = (
        container.submit_response_feedback_use_case
    )
    app.dependency_overrides[response_feedback_router._get_list_use_case] = (
        container.list_response_feedback_use_case
    )
    app.dependency_overrides[response_feedback_router._get_get_use_case] = (
        container.get_response_feedback_use_case
    )
    app.dependency_overrides[response_feedback_router._get_update_use_case] = (
        container.update_response_feedback_use_case
    )
    app.dependency_overrides[response_feedback_router._get_delete_use_case] = (
        container.delete_response_feedback_use_case
    )

    yield


app = FastAPI(
    title="AnswerGuard",
    description="Response feedback and adherence layer for agent-based products",
    version="0.1.0",
    lifespan=lifespan,
)

# Allow the desktop app (running on a different origin in dev) to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(ingestion_router.router, prefix="/v1")
app.include_router(capture_router.router, prefix="/v1")
app.include_router(sources_router.router, prefix="/v1")
app.include_router(qa_pairs_router.router, prefix="/v1")
app.include_router(response_feedback_router.router, prefix="/v1")
