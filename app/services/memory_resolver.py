import logging

from app.domain.entities.memory import MemorySummary
from app.domain.interfaces.llm import LLMProvider
from app.domain.interfaces.repositories import MemoryRepository, UserRepository
from app.exceptions import MemoryConflictError

logger = logging.getLogger("astrobot")


class MemoryResolver:
    """Управление памятью пользователя: суммаризация, конфликт-резолюция
    (User memory management: summarization, conflict resolution)."""

    def __init__(
        self,
        memory_repo: MemoryRepository,
        user_repo: UserRepository,
        llm_provider: LLMProvider,
    ):
        self._memory_repo = memory_repo
        self._user_repo = user_repo
        self._llm = llm_provider

    async def get_or_create_summary(self, user_id: int) -> MemorySummary | None:
        """Получить существующую суммаризацию или None (Get existing summary or None)."""
        return await self._memory_repo.get_by_user_id(user_id)

    async def summarize_and_save(self, user_id: int, messages: list[dict]) -> MemorySummary:
        """Суммаризировать диалог и сохранить с optimistic lock (Summarize dialog and save)."""
        summary_data = await self._llm.summarize(messages)
        summary_text = summary_data.get("summary", "")

        # Получаем текущую версию (Get current version)
        existing = await self._memory_repo.get_by_user_id(user_id)
        new_version = (existing.version + 1) if existing else 1

        # Оптимистичная блокировка: пробуем обновить через user_repo (Optimistic lock via user_repo)
        try:
            await self._user_repo.update_memory_summary(
                user_id=user_id,
                summary=summary_text,
                version=new_version - 1,
            )
        except MemoryConflictError:
            logger.warning("Memory conflict for user %d, version %d", user_id, new_version - 1)
            raise

        # Сохраняем в таблицу memory_summaries (Save to memory_summaries table)
        memory = MemorySummary(
            user_id=user_id,
            summary=summary_text,
            version=new_version,
        )
        return await self._memory_repo.save(memory)
