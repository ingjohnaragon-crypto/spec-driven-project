from fastapi import FastAPI

from src.infrastructure.config.settings import Settings
from src.presentation.routers.health_router import router as health_router
from src.presentation.exception_handlers.global_handlers import register_exception_handlers

settings = Settings()


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )
    app.include_router(health_router)
    register_exception_handlers(app)
    return app


app = create_app()
