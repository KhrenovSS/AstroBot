import logging
from typing import Any

import httpx

from app.config import Settings
from app.domain.interfaces.llm import LLMProvider
from app.exceptions import LLMProviderError

logger = logging.getLogger("astrobot")


class GroqClient(LLMProvider):
    """Реализация LLMProvider через Groq API (OpenAI-совместимый) (Groq LLM provider)."""

    def __init__(self, settings: Settings):
        self._api_key = settings.groq_api_key
        self._model = settings.groq_model
        self._max_tokens = settings.groq_max_tokens
        self._temperature = settings.groq_temperature
        self._api_base = settings.groq_api_base.rstrip("/")
        self._headers = {
            "Authorization": f"Bearer {self._api_key}",
            "content-type": "application/json",
        }

    async def generate_reply(
        self, system_prompt: str, history: list[dict], user_message: str
    ) -> str:
        """Сгенерировать ответ через Groq (Generate reply via Groq)."""
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(history)
        messages.append({"role": "user", "content": user_message})

        body = {
            "model": self._model,
            "max_tokens": self._max_tokens,
            "temperature": self._temperature,
            "messages": messages,
        }

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(
                    f"{self._api_base}/openai/v1/chat/completions",
                    headers=self._headers,
                    json=body,
                )
                resp.raise_for_status()
                data = resp.json()
                return self._extract_text(data)
        except httpx.HTTPStatusError as e:
            logger.error("Groq API error: %s — %s", e.response.status_code, e.response.text[:200])
            raise LLMProviderError(f"Groq API error: {e.response.status_code}") from e
        except httpx.RequestError as e:
            logger.error("Groq request failed: %s", str(e))
            raise LLMProviderError(f"Groq request failed: {e}") from e

    async def summarize(self, messages: list[dict]) -> dict:
        """Суммаризировать историю сообщений (Summarize message history)."""
        body = {
            "model": self._model,
            "max_tokens": 1024,
            "temperature": 0.3,
            "messages": [
                {
                    "role": "system",
                    "content": "Ты — ассистент, который суммаризирует диалоги. "
                    "Верни JSON вида {\"summary\": \"...\", \"key_facts\": [\"...\"], \"mood\": \"...\"}",
                },
                {"role": "user", "content": f"Суммаризируй этот диалог:\n\n{messages}"},
            ],
        }

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(
                    f"{self._api_base}/openai/v1/chat/completions",
                    headers=self._headers,
                    json=body,
                )
                resp.raise_for_status()
                data = resp.json()
                text = self._extract_text(data)
                return {"summary": text, "key_facts": [], "mood": "neutral"}
        except (httpx.HTTPStatusError, httpx.RequestError) as e:
            logger.error("Groq summarize failed: %s", str(e))
            raise LLMProviderError(f"Groq summarize failed: {e}") from e

    async def classify_session_end(self, last_messages: list[dict]) -> bool:
        """Определить, хочет ли пользователь завершить сессию (Classify if user wants to end session)."""
        body = {
            "model": self._model,
            "max_tokens": 10,
            "temperature": 0.0,
            "messages": [
                {
                    "role": "system",
                    "content": "Ты — классификатор. Ответь только 'true' или 'false'. "
                    "Верни 'true', если пользователь явно или косвенно прощается, "
                    "завершает разговор, говорит 'пока', 'до свидания', 'спасибо, хватит'. "
                    "Верни 'false' в остальных случаях.",
                },
                {
                    "role": "user",
                    "content": f"Последние сообщения:\n{last_messages}\n\nСессия завершается?",
                },
            ],
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    f"{self._api_base}/openai/v1/chat/completions",
                    headers=self._headers,
                    json=body,
                )
                resp.raise_for_status()
                data = resp.json()
                text = self._extract_text(data).strip().lower()
                return text == "true"
        except (httpx.HTTPStatusError, httpx.RequestError) as e:
            logger.error("Groq classify failed: %s", str(e))
            raise LLMProviderError(f"Groq classify failed: {e}") from e

    def _extract_text(self, data: dict[str, Any]) -> str:
        """Извлечь текст из ответа Groq API (Extract text from Groq API response)."""
        choices = data.get("choices", [])
        if choices:
            message = choices[0].get("message", {})
            return message.get("content", "")
        return ""
