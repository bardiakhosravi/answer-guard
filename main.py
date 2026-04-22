from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI

from src.configuration.app_settings import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Startup: settings are validated on import
    get_settings()
    yield
    # Shutdown: nothing to clean up at this stage


app = FastAPI(
    title="AnswerGuard",
    description="Response feedback and adherence layer for agent-based products",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


# Routers registered as user stories are implemented:
# from src.adapters.primary.web.ingestion_router import router as ingestion_router
# from src.adapters.primary.web.capture_router import router as capture_router
# app.include_router(ingestion_router, prefix="/v1")
# app.include_router(capture_router, prefix="/v1")
