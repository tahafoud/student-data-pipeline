"""
logger.py
---------
Centralized logging configuration for the whole pipeline.

Every module imports `get_logger(__name__)` instead of configuring its
own logging, so all log records end up in the same file
(logs/pipeline.log) with a consistent format, as required by the
assignment:

    2026-09-21 10:00:01 INFO CSV extraction started
"""

import logging
from pathlib import Path

LOG_DIR = Path(__file__).resolve().parents[2] / "logs"
LOG_FILE = LOG_DIR / "pipeline.log"

_CONFIGURED = False


def _configure_root_logger() -> None:
    global _CONFIGURED
    if _CONFIGURED:
        return

    LOG_DIR.mkdir(parents=True, exist_ok=True)

    formatter = logging.Formatter(
        fmt="%(asctime)s %(levelname)s %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = logging.FileHandler(LOG_FILE, mode="a", encoding="utf-8")
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.addHandler(file_handler)
    root.addHandler(console_handler)

    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    """Return a module-level logger that writes to logs/pipeline.log."""
    _configure_root_logger()
    return logging.getLogger(name)
