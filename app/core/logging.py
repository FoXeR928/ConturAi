from sys import stdout

from loguru import logger

from app.core.config import settings
from app.core.paths import LOG_FILE


def setup_logging() -> None:
    logger.remove()
    logger.add(
        LOG_FILE,
        format="{time} | {level} | {message} | {name}",
        rotation="128 MB",
        retention="10 days",
        level="DEBUG" if settings.debug else "INFO",
        encoding="utf-8",
    )
    logger.add(stdout, level="TRACE" if settings.debug else "WARNING")
    logger.info(f"Logging initialized → {LOG_FILE}")