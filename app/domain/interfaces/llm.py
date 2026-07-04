from abc import ABC, abstractmethod


class LLMProvider(ABC):
    """Интерфейс провайдера LLM (LLM provider interface)."""

    @abstractmethod
    async def generate_reply(
        self, system_prompt: str, history: list[dict], user_message: str
    ) -> str:
        ...

    @abstractmethod
    async def summarize(self, messages: list[dict]) -> dict:
        ...

    @abstractmethod
    async def classify_session_end(self, last_messages: list[dict]) -> bool:
        ...
