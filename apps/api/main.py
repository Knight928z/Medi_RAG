from fastapi import FastAPI

from apps.api.routers import evaluation, health, memory, reports, workflows
from core.logging import setup_logging


def create_app() -> FastAPI:
    setup_logging()
    app = FastAPI(title="Medi_RAG", version="0.1.0")
    app.include_router(health.router)
    app.include_router(reports.router)
    app.include_router(workflows.router)
    app.include_router(memory.router)
    app.include_router(evaluation.router)
    return app


app = create_app()
