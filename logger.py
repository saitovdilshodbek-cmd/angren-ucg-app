"""
Structured logging configuration with rotation and security.

Bu modul app.py dagi logging ni to'g'rilaydi:
  - RotatingFileHandler (10 MB, 5 backup)
  - Directory permission 0o755
  - Optional syslog/journal handler
  - Structured format (JSON option)
"""

from __future__ import annotations

import logging
import logging.config
import logging.handlers
import os
from pathlib import Path
from typing import Any, Dict, Optional


def setup_logging(
    log_dir: str = "~/.ucg_platform/logs",
    level: str = "INFO",
    max_bytes: int = 10 * 1024 * 1024,  # 10 MB
    backup_count: int = 5,
    json_format: bool = False,
) -> Path:
    """
    Setup structured logging with rotation.

    Parameters:
        log_dir: Log directory (will be created if missing)
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        max_bytes: Max log file size before rotation (default 10 MB)
        backup_count: Number of backup files to keep
        json_format: If True, use JSON structured logs (for log aggregation)

    Returns:
        Path to the log directory

    Raises:
        OSError: If log directory cannot be created
    """
    log_dir_path = Path(log_dir).expanduser()
    # mode=0o755: rwxr-xr-x (owner can write, others can read)
    log_dir_path.mkdir(parents=True, exist_ok=True, mode=0o755)
    log_file = log_dir_path / "ucg_platform.log"

    if json_format:
        formatter_config = {
            "format": '{"time": "%(asctime)s", "level": "%(levelname)s", '
                      '"logger": "%(name)s", "module": "%(module)s", '
                      '"func": "%(funcName)s:%(lineno)d", "message": "%(message)s"}',
            "datefmt": "%Y-%m-%dT%H:%M:%S%z",
        }
    else:
        formatter_config = {
            "format": "%(asctime)s | %(name)s | %(levelname)-8s | "
                      "%(funcName)s:%(lineno)d | %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        }

    config: Dict[str, Any] = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "detailed": formatter_config,
            "simple": {"format": "%(levelname)s | %(message)s"},
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": level,
                "formatter": "simple",
                "stream": "ext://sys.stdout",
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "DEBUG",
                "formatter": "detailed",
                "filename": str(log_file),
                "encoding": "utf-8",
                "maxBytes": max_bytes,
                "backupCount": backup_count,
            },
        },
        "loggers": {
            "ucg_platform": {
                "level": "DEBUG",
                "handlers": ["console", "file"],
                "propagate": False,
            },
        },
        "root": {
            "level": "WARNING",
            "handlers": ["console"],
        },
    }
    logging.config.dictConfig(config)
    return log_dir_path


def get_logger(name: str) -> logging.Logger:
    """Get a logger under the ucg_platform namespace."""
    if not name.startswith("ucg_platform"):
        name = f"ucg_platform.{name}"
    return logging.getLogger(name)


class LogContext:
    """Context manager for adding contextual fields to log messages."""

    def __init__(self, logger: logging.Logger, **context: Any) -> None:
        self.logger = logger
        self.context = context
        self.old_factory = logging.getLogRecordFactory()

    def __enter__(self) -> "LogContext":
        ctx = self.context
        old_factory = self.old_factory

        def record_factory(*args: Any, **kwargs: Any) -> logging.LogRecord:
            record = old_factory(*args, **kwargs)
            for k, v in ctx.items():
                setattr(record, k, v)
            return record

        logging.setLogRecordFactory(record_factory)
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        logging.setLogRecordFactory(self.old_factory)
