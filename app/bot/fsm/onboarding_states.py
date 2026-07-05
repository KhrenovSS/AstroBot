from aiogram.fsm.state import State, StatesGroup


class OnboardingStates(StatesGroup):
    """Состояния FSM онбординга (Onboarding FSM states)."""

    ASK_BIRTH_DATE = State()
    ASK_BIRTH_PLACE = State()
    ASK_BIRTH_TIME = State()
    ASK_PARENTS_DATES = State()
    ASK_GRANDPARENTS_DATES = State()
    CONFIRM_DATA = State()
    COMPLETE = State()
