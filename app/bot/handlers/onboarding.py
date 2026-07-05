from datetime import date, datetime, time

from aiogram import Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.bot.fsm.onboarding_states import OnboardingStates
from app.services.onboarding_service import OnboardingService

router = Router()
TEMP_DATA_KEY = "birth_data"


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext, onboarding_service: OnboardingService):
    """Обработчик /start: начать онбординг (Start command: begin onboarding)."""
    tg_id = message.from_user.id
    user = await onboarding_service.start(tg_id)

    if user.status == "ACTIVE":
        await message.answer("Вы уже завершили регистрацию. Используйте /help для списка команд.")
        return

    await state.set_state(OnboardingStates.ASK_BIRTH_DATE)
    await state.update_data({TEMP_DATA_KEY: {"tg_id": tg_id}})
    await message.answer(
        "Добро пожаловать! Я — предиктивный астролог. "
        "Для начала мне нужно собрать некоторые данные.\n\n"
        "Укажите вашу **дату рождения** (в формате ДД.ММ.ГГГГ):"
    )


@router.message(StateFilter(OnboardingStates.ASK_BIRTH_DATE))
async def process_birth_date(message: Message, state: FSMContext):
    """Обработчик ввода даты рождения (Process birth date input)."""
    text = message.text.strip()
    try:
        parsed = datetime.strptime(text, "%d.%m.%Y").date()
    except ValueError:
        try:
            parsed = datetime.strptime(text, "%Y-%m-%d").date()
        except ValueError:
            await message.answer(
                "Пожалуйста, введите дату в формате ДД.ММ.ГГГГ (например, 15.05.1990):"
            )
            return

    data = await state.get_data()
    data[TEMP_DATA_KEY]["birth_date"] = parsed.isoformat()
    await state.update_data(data)
    await state.set_state(OnboardingStates.ASK_BIRTH_PLACE)
    await message.answer("Укажите **место рождения** (город, страна):")


@router.message(StateFilter(OnboardingStates.ASK_BIRTH_PLACE))
async def process_birth_place(message: Message, state: FSMContext):
    """Обработчик ввода места рождения (Process birth place input)."""
    place = message.text.strip()
    if not place:
        await message.answer("Пожалуйста, укажите место рождения:")
        return

    data = await state.get_data()
    data[TEMP_DATA_KEY]["birth_place"] = place
    await state.update_data(data)
    await state.set_state(OnboardingStates.ASK_BIRTH_TIME)
    await message.answer(
        "Укажите **время рождения** (в формате ЧЧ:ММ) или отправьте «—», если не знаете:"
    )


@router.message(StateFilter(OnboardingStates.ASK_BIRTH_TIME))
async def process_birth_time(message: Message, state: FSMContext):
    """Обработчик ввода времени рождения (Process birth time input)."""
    text = message.text.strip()
    birth_time = None

    if text != "—" and text != "-":
        try:
            parsed = datetime.strptime(text, "%H:%M").time()
            birth_time = parsed.isoformat()
        except ValueError:
            await message.answer(
                "Пожалуйста, введите время в формате ЧЧ:ММ (например, 14:30) или «—»:"
            )
            return

    data = await state.get_data()
    data[TEMP_DATA_KEY]["birth_time"] = birth_time
    await state.update_data(data)
    await state.set_state(OnboardingStates.CONFIRM_DATA)
    await _show_confirmation(message, data)


async def _show_confirmation(message: Message, data: dict):
    """Показать данные пользователю для подтверждения (Show collected data for confirmation)."""
    d = data.get(TEMP_DATA_KEY, {})
    lines = [
        "Проверьте введённые данные:",
        f"• Дата рождения: {d.get('birth_date', '—')}",
        f"• Место рождения: {d.get('birth_place', '—')}",
        f"• Время рождения: {d.get('birth_time', '—') or 'не указано'}",
        "",
        "Всё верно? Отправьте «Да» для подтверждения или «Нет» для отмены.",
    ]
    await message.answer("\n".join(lines))


@router.message(StateFilter(OnboardingStates.CONFIRM_DATA))
async def process_confirmation(
    message: Message, state: FSMContext, onboarding_service: OnboardingService
):
    """Обработчик подтверждения данных (Process data confirmation)."""
    text = message.text.strip().lower()

    if text in ("нет", "н", "no"):
        await state.clear()
        await message.answer("Регистрация отменена. Отправьте /start, чтобы начать заново.")
        return

    if text not in ("да", "д", "yes"):
        await message.answer("Отправьте «Да» для подтверждения или «Нет» для отмены.")
        return

    data = await state.get_data()
    d = data.get(TEMP_DATA_KEY, {})

    try:
        birth_date = date.fromisoformat(d["birth_date"])
        birth_place = d["birth_place"]
        birth_time = time.fromisoformat(d["birth_time"]) if d.get("birth_time") else None

        await onboarding_service.finalize(
            tg_id=d["tg_id"],
            birth_date=birth_date,
            birth_place=birth_place,
            birth_time=birth_time,
        )

        await state.clear()
        await message.answer(
            "✅ Регистрация завершена! Ваши данные сохранены в зашифрованном виде.\n\n"
            "Теперь вы можете задавать вопросы. Используйте /help для списка команд."
        )
    except Exception:
        await message.answer(
            "Произошла ошибка при обработке данных. "
            "Попробуйте позже или начните заново через /start."
        )
        await state.clear()
