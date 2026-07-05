from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Telegram
    telegram_bot_token: str = ""

    # LLM (Ollama — local)
    ollama_api_base: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5:0.5b"
    ollama_timeout: int = 120

    # Whisper
    openai_api_key: str = ""

    # Database
    database_url: str = "postgresql+asyncpg://astrobot:astrobot_password@postgres:5432/astrobot"
    database_url_sync: str = "postgresql://astrobot:astrobot_password@postgres:5432/astrobot"

    # Redis
    redis_url: str = "redis://redis:6379/0"
    celery_broker_url: str = "redis://redis:6379/1"
    celery_result_backend: str = "redis://redis:6379/2"

    # Encryption
    aes_encryption_key: str = ""

    # Payments
    crypto_bot_token: str = ""

    # Geocoding (Nominatim)
    nominatim_url: str = "https://nominatim.openstreetmap.org"
    nominatim_user_agent: str = "AstroBot/1.0"
    geocoding_timeout: int = 10

    # Admin API
    secret_key: str = ""

    # App
    log_level: str = "info"
    session_timeout_minutes: int = 30
    free_trial_messages_daily: int = 50
    free_trial_messages_weekly: int = 200
    free_trial_cumulative_seconds: int = 3600
    astrobot_host: str = "0.0.0.0"
    astrobot_port: int = 8000

    # Chat settings
    semantic_check_interval: int = 5  # messages_since_last_semantic_check before LLM check
    n_system_prompt: str = "Ты — предиктивный астролог. Интерпретируй данные натальной матрицы и общайся с пользователем. Не давай медицинских, юридических или финансовых советов."
    explicit_end_phrases: list[str] = ["пока", "до свидания", "до встречи", "всего доброго", "bye", "goodbye"]

    # Postgres (Docker)
    postgres_user: str = "astrobot"
    postgres_password: str = "astrobot_password"
    postgres_db: str = "astrobot"

    # Local dev only — sudo for apt/docker (не коммитится)
    sudo_password: str = ""
