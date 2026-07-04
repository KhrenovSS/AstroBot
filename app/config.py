from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Telegram
    telegram_bot_token: str = ""

    # LLM
    anthropic_api_key: str = ""

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

    # Postgres (Docker)
    postgres_user: str = "astrobot"
    postgres_password: str = "astrobot_password"
    postgres_db: str = "astrobot"

    # Local dev only — sudo for apt/docker (не коммитится)
    sudo_password: str = ""
