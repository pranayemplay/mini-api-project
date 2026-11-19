"""Configures loguru once, at startup. Docker collects whatever the app writes to stdout."""
import sys

from loguru import logger


def setup_logging(level: str) -> None:
    logger.remove()  # drop loguru's default handler so lines aren't printed twice
    logger.add(
        sys.stdout,
        level=level,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
    )
