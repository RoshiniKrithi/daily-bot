"""Structured logger setup for Zero-Contest Streak Bot."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

LOG_FILE = Path(__file__).parent.resolve() / "streak_execution.log"


class SensitiveDataFilter(logging.Filter):
    """Filter to ensure session tokens or sensitive credentials are never logged."""

    def filter(self, record: logging.LogRecord) -> bool:
        msg = str(record.msg)
        for token_key in ["LEETCODE_SESSION", "CSRFTOKEN", "session", "cookie"]:
            if token_key.lower() in msg.lower() and "=" in msg:
                # Sanitize potential key=val pairs
                record.msg = "[SANITIZED LOG ENTRY CONTAINING SENSITIVE DATA]"
        return True


def setup_logger(log_level: str = "INFO") -> logging.Logger:
    """Configure and return the root structured logger."""
    logger = logging.getLogger("StreakBot")
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    logger.handlers.clear()

    # Log format matching specification:
    # 2026-08-08 09:00:01 | INFO | Message
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-7s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.addFilter(SensitiveDataFilter())
    logger.addHandler(console_handler)

    # File Handler
    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    file_handler.setFormatter(formatter)
    file_handler.addFilter(SensitiveDataFilter())
    logger.addHandler(file_handler)

    return logger
