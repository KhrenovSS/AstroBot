import logging

from aiogram import Router
from aiogram.filters import Command, StateFilter
from aiogram.types import Message

from app.bot.fsm.onboarding_states import OnboardingStates
from app.services.chat_service import ChatService

logger = logging.getLogger("astrobot")

router = Router()


@router.message(Command("help"))
async def cmd_help(message: Message):
    """Показать справку (Show help message)."""
    await message.answer(
        "🤖 **AstroBot — предиктивный астролог**\n\n"
        "Я интерпретирую данные вашей натальной матрицы, "
        "построенной на основе момента зачатия.\n\n"
        "**Команды:**\n"
        "/start — начать / продолжить\n"
        "/help — эта справка\n"
        "/new — начать новый диалог\n\n"
        "Просто напишите мне сообщение, чтобы начать консультацию."
    )


@router.message(Command("new"))
async def cmd_new(message: Message, chat_service: ChatService):
    """Начать новый диалог (Start a new conversation)."""
    tg_id = message.from_user.id
    reply = await chat_service.handle_message(tg_id, "/new")
    await message.answer(reply)


@router.message(StateFilter(None))
async def handle_message(message: Message, chat_service: ChatService):
    """Обработать обычное текстовое сообщение (Handle regular text message)."""
    if not message.text:
        return

    tg_id = message.from_user.id
    try:
        reply = await chat_service.handle_message(tg_id, message.text)
        await message.answer(reply)
    except Exception as e:
        logger.error("Chat error for user %d: %s", tg_id, str(e))
        await message.answer(
            "Произошла ошибка при обработке сообщения. "
            "Попробуйте позже или используйте /start."
        )
