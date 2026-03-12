"""
Loguru configuration.

Call setup_logging() once at startup to configure console + file sinks.
"""

import sys
from pathlib import Path

from loguru import logger


def setup_logging(level: str = "INFO", log_dir: str = "logs",
                  rotation: str = "10 MB", retention: str = "7 days") -> None:
    """Configure loguru sinks: stderr (colored) + rotating file."""

    # Remove loguru's default stderr handler so we can replace it
    logger.remove()

    # Console: colored, human-friendly
    logger.add(
        sys.stderr,
        level=level.upper(),
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
            "<level>{message}</level>"
        ),
        colorize=True,
    )

    # File: JSON-ish structured, auto-rotated
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    logger.add(
        log_path / "index_{time:YYYY-MM-DD}.log",
        level=level.upper(),
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
        rotation=rotation,
        retention=retention,
        encoding="utf-8",
        enqueue=True,  # thread-safe async writes
    )

    # Separate error log for quick diagnosis
    logger.add(
        log_path / "error_{time:YYYY-MM-DD}.log",
        level="ERROR",
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
        rotation=rotation,
        retention=retention,
        encoding="utf-8",
        enqueue=True,
        backtrace=True,
        diagnose=True,
    )

    logger.info(f"Logging configured: level={level}, dir={log_dir}")
