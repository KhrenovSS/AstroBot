import json
import logging
from typing import Any

import httpx

from app.config import Settings
from app.domain.interfaces.llm import LLMProvider
from app.exceptions import LLMProviderError

logger = logging.getLogger("astrobot")


class OllamaClient(LLMProvider):
    """Реализация LLMProvider через локальный Ollama API (Ollama local LLM provider)."""

    def __init__(self, settings: Settings):
        self._model = settings.ollama_model
        self._api_base = settings.ollama_api_base.rstrip("/")
        self._timeout = settings.ollama_timeout
        self._temperature = settings.llm_temperature

    async def generate_reply(
        self, system_prompt: str, history: list[dict], user_message: str
    ) -> str:
        """Сгенерировать ответ через Ollama (Generate reply via Ollama)."""
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(history)
        messages.append({"role": "user", "content": user_message})

        body = {
            "model": self._model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": self._temperature,
            },
        }

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.post(
                    f"{self._api_base}/api/chat",
                    json=body,
                )
                resp.raise_for_status()
                data = resp.json()
                return self._extract_text(data)
        except httpx.HTTPStatusError as e:
            logger.error("Ollama API error: %s — %s", e.response.status_code, e.response.text[:200])
            raise LLMProviderError(f"Ollama API error: {e.response.status_code}") from e
        except httpx.RequestError as e:
            logger.error("Ollama request failed: %s", str(e))
            raise LLMProviderError(f"Ollama request failed: {e}") from e

    async def summarize(self, messages: list[dict]) -> dict:
        """Суммаризировать историю сообщений (Summarize message history)."""
        body = {
            "model": self._model,
            "messages": [
                {
                    "role": "system",
                    "content": "Ты — ассистент, который суммаризирует диалоги. "
                    "Верни JSON вида {\"summary\": \"...\", \"key_facts\": [\"...\"], \"mood\": \"...\"}",
                },
                {"role": "user", "content": f"Суммаризируй этот диалог:\n\n{messages}"},
            ],
            "stream": False,
            "options": {
                "temperature": self._temperature,
            },
        }

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.post(
                    f"{self._api_base}/api/chat",
                    json=body,
                )
                resp.raise_for_status()
                data = resp.json()
                text = self._extract_text(data)
                try:
                    parsed = json.loads(text)
                    return {
                        "summary": parsed.get("summary", text),
                        "key_facts": parsed.get("key_facts", []),
                        "mood": parsed.get("mood", "neutral"),
                    }
                except json.JSONDecodeError:
                    return {"summary": text, "key_facts": [], "mood": "neutral"}
        except (httpx.HTTPStatusError, httpx.RequestError) as e:
            logger.error("Ollama summarize failed: %s", str(e))
            raise LLMProviderError(f"Ollama summarize failed: {e}") from e

    async def classify_session_end(self, last_messages: list[dict]) -> bool:
        """Определить, хочет ли пользователь завершить сессию (Classify if user wants to end session)."""
        body = {
            "model": self._model,
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
            "stream": False,
            "options": {
                "temperature": self._temperature,
            },
        }

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.post(
                    f"{self._api_base}/api/chat",
                    headers={"Content-Type": "application/json"},
                    json=body,
                )
                resp.raise_for_status()
                data = resp.json()
                text = self._extract_text(data).strip().lower()
                return text == "true"
        except (httpx.HTTPStatusError, httpx.RequestError) as e:
            logger.error("Ollama classify failed: %s", str(e))
            raise LLMProviderError(f"Ollama classify failed: {e}") from e

    def _extract_text(self, data: dict[str, Any]) -> str:
        """Извлечь текст из ответа Ollama (Extract text from Ollama response)."""
        message = data.get("message", {})
        return message.get("content", "")
