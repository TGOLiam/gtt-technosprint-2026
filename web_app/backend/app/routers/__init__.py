from fastapi import FastAPI

from app.routers.health import router as health_router
from app.routers.prompts import router as prompts_router
from app.routers.record import router as record_router
from app.routers.pipeline import router as pipeline_router
from app.routers.stats import router as stats_router


def register_routers(app: FastAPI) -> None:
    app.include_router(health_router)
    app.include_router(prompts_router)
    app.include_router(record_router)
    app.include_router(stats_router)
    app.include_router(pipeline_router)
