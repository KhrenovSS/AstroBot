import logging
from typing import Any

import httpx

from app.config import Settings
from app.domain.interfaces.llm import LLMProvider
from app.exceptions import LLMProviderError

logger = logging.getLogger("astrobot")


class AnthropicClient(LLMProvider):
    """Реализация LLMProvider через Anthropic Claude API (Anthropic Claude LLM provider)."""

    API_VERSION = "2023-06-01"

    def __init__(self, settings: Settings):
        self._api_key = settings.anthropic_api_key
        self._model = settings.anthropic_model
        self._max_tokens = settings.anthropic_max_tokens
        self._temperature = settings.anthropic_temperature
        self._api_base = settings.anthropic_api_base.rstrip("/")
        self._headers = {
            "x-api-key": self._api_key,
            "anthropic-version": self.API_VERSION,
            "content-type": "application/json",
        }

    async def generate_reply(
        self, system_prompt: str, history: list[dict], user_message: str
    ) -> str:
        """Сгенерировать ответ через Claude (Generate reply via Claude)."""
        messages = list(history)
        messages.append({"role": "user", "content": user_message})

        body = {
            "model": self._model,
            "max_tokens": self._max_tokens,
            "temperature": self._temperature,
            "system": system_prompt,
            "messages": messages,
        }

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(
                    f"{self._api_base}/v1/messages",
                    headers=self._headers,
                    json=body,
                )
                resp.raise_for_status()
                data = resp.json()
                return self._extract_text(data)
        except httpx.HTTPStatusError as e:
            logger.error("Anthropic API error: %s — %s", e.response.status_code, e.response.text[:200])
            raise LLMProviderError(f"Anthropic API error: {e.response.status_code}") from e
        except httpx.RequestError as e:
            logger.error("Anthropic request failed: %s", str(e))
            raise LLMProviderError(f"Anthropic request failed: {e}") from e

    async def summarize(self, messages: list[dict]) -> dict:
        """Суммаризировать историю сообщений (Summarize message history)."""
        body = {
            "model": self._model,
            "max_tokens": 1024,
            "temperature": 0.3,
            "system": "Ты — ассистент, который суммаризирует диалоги. "
                      "Верни JSON вида {\"summary\": \"...\", \"key_facts\": [\"...\"], \"mood\": \"...\"}",
            "messages": [
                {"role": "user", "content": f"Суммаризируй этот диалог:\n\n{messages}"}
            ],
        }

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(
                    f"{self._api_base}/v1/messages",
                    headers=self._headers,
                    json=body,
                )
                resp.raise_for_status()
                data = resp.json()
                text = self._extract_text(data)
                return {"summary": text, "key_facts": [], "mood": "neutral"}
        except (httpx.HTTPStatusError, httpx.RequestError) as e:
            logger.error("Anthropic summarize failed: %s", str(e))
            raise LLMProviderError(f"Anthropic summarize failed: {e}") from e

    async def classify_session_end(self, last_messages: list[dict]) -> bool:
        """Определить, хочет ли пользователь завершить сессию (Classify if user wants to end session)."""
        body = {
            "model": self._model,
            "max_tokens": 10,
            "temperature": 0.0,
            "system": "Ты — классификатор. Ответь только 'true' или 'false'. "
                      "Верни 'true', если пользователь явно или косвенно прощается, "
                      "завершает разговор, говорит 'пока', 'до свидания', 'спасибо, хватит'. "
                      "Верни 'false' в остальных случаях.",
            "messages": [
                {"role": "user", "content": f"Последние сообщения:\n{last_messages}\n\nСессия завершается?"}
            ],
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    f"{self._api_base}/v1/messages",
                    headers=self._headers,
                    json=body,
                )
                resp.raise_for_status()
                data = resp.json()
                text = self._extract_text(data).strip().lower()
                return text == "true"
        except (httpx.HTTPStatusError, httpx.RequestError) as e:
            logger.error("Anthropic classify failed: %s", str(e))
            raise LLMProviderError(f"Anthropic classify failed: {e}") from e

    def _extract_text(self, data: dict[str, Any]) -> str:
        """Извлечь текст из ответа Claude API (Extract text from Claude API response)."""
        content = data.get("content", [])
        for block in content:
            if block.get("type") == "text":
                return block.get("text", "")
        return ""
