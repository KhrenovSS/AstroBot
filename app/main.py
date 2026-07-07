import asyncio
from contextlib import asynccontextmanager

from aiogram import Bot
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

    # Telegram bot
    poll_task = None
    bot_instance: Bot | None = None
    if settings.telegram_bot_token:
        from app.bot import setup_dispatcher

        bot_instance = Bot(token=settings.telegram_bot_token)
        dp = setup_dispatcher(container)

        async def _poll():
            try:
                logger.info("Starting Telegram bot polling...")
                await dp.start_polling(bot_instance)
            finally:
                logger.info("Telegram bot polling stopped")

        poll_task = asyncio.create_task(_poll())
        logger.info("Telegram bot polling task created")
    else:
        logger.warning("TELEGRAM_BOT_TOKEN not set — bot polling disabled")

    app.state.bot_instance = bot_instance
    app.state.poll_task = poll_task

    yield

    if poll_task:
        poll_task.cancel()
        try:
            await poll_task
        except asyncio.CancelledError:
            pass
    if bot_instance:
        await bot_instance.session.close()

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
