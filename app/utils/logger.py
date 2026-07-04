import logging
import sys

from app.config import Settings


def setup_logger(settings: Settings) -> logging.Logger:
    """Настройка корневого логгера (Setup root logger with app config)."""
    level = getattr(logging, settings.log_level.upper(), logging.INFO)

    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S%z",
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    logger = logging.getLogger("astrobot")
    logger.setLevel(level)
    logger.handlers.clear()
    logger.addHandler(handler)

    return logger
