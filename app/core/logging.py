from sys import stdout

from loguru import logger

from app.core.config import settings


def setup_logging() -> None:
    logger.remove()
    logger.add(
        "logs/app.log",
        format="{time} | {level} | {message} | {name}",
        rotation="128 MB",
        retention="10 days",
        level="DEBUG" if settings.debug else "INFO",
    )
    logger.add(stdout, level="TRACE" if settings.debug else "WARNING")
    logger.info("Logging initialized")