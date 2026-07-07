from aiogram import Bot, Dispatcher

from app.bot.handlers import chat as chat_handler
from app.bot.handlers import onboarding as onboarding_handler
from app.bot.middlewares import DIMiddleware
from app.di import Container


def setup_dispatcher(container: Container) -> Dispatcher:
    dp = Dispatcher()
    dp.include_router(onboarding_handler.router)
    dp.include_router(chat_handler.router)

    dp.update.outer_middleware(DIMiddleware(container))

    return dp
