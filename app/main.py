from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import Settings
from app.di import build_container
from app.utils.logger import setup_logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения (Application lifespan: startup/shutdown)."""
    settings = Settings()
    logger = setup_logger(settings)
    logger.info("AstroBot starting up")

    container = build_container(settings)
    app.state.container = container
    app.state.logger = logger

    yield

    logger.info("AstroBot shutting down")


def create_app() -> FastAPI:
    """Фабрика FastAPI-приложения (FastAPI application factory)."""
    app = FastAPI(
        title="AstroBot",
        version="0.1.0",
        lifespan=lifespan,
    )

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    return app


app = create_app()
