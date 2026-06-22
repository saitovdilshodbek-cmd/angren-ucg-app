"""
UCG Platform — Structured Logging Setup
========================================

Secure logging with rotation, proper permissions, and structured format.

Usage:
    from ucg_platform.logger import setup_logging, get_logger

    setup_logging()  # Call once at startup
    logger = get_logger(__name__)
    logger.info("Application started")
"""

from __future__ import annotations

import logging
import logging.config
import logging.handlers
from pathlib import Path
from typing import Optional

from .constants import PathConstants, SecurityConstants
from .exceptions import ConfigurationError


def setup_logging(
    log_dir: Optional[Path] = None,
    level: str = "INFO",
    max_bytes: int = 10 * 1024 * 1024,  # 10 MB
    backup_count: int = 5,
) -> None:
    """Setup structured logging with rotation.

    Args:
        log_dir: Directory for log files (default: ~/.ucg_platform/logs)
        level: Logging level ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')
        max_bytes: Maximum log file size before rotation (default: 10 MB)
        backup_count: Number of backup files to keep (default: 5)

    Raises:
        ConfigurationError: If log_dir cannot be created or is not a directory
    """
    log_dir = log_dir or PathConstants.LOG_DIR
    log_dir = Path(log_dir).expanduser()

    # Validate level
    valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
    if level.upper() not in valid_levels:
        raise ConfigurationError(
            f"Invalid log level: {level}. Must be one of {valid_levels}"
        )

    # Create log directory with safe permissions (0o755)
    try:
        log_dir.mkdir(parents=True, exist_ok=True, mode=0o755)
    except OSError as exc:
        raise ConfigurationError(f"Cannot create log directory {log_dir}: {exc}")

    # Verify it's a directory
    if not log_dir.is_dir():
        raise ConfigurationError(f"Log path is not a directory: {log_dir}")

    log_file = log_dir / "ucg_platform.log"

    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "detailed": {
                "format": "%(asctime)s | %(name)s | %(levelname)-8s | %(funcName)s:%(lineno)d | %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "simple": {
                "format": "%(levelname)s | %(message)s",
            },
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
            "ucg_platform.patent_extension": {
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


def get_logger(name: str = "ucg_platform") -> logging.Logger:
    """Get a logger instance.

    Args:
        name: Logger name (typically __name__)

    Returns:
        logging.Logger: Configured logger instance
    """
    return logging.getLogger(name)


# Initialize on import (with safe defaults)
try:
    setup_logging()
except ConfigurationError:
    # Fallback to basic config if directory creation fails
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s | %(message)s",
    )


__all__ = ["setup_logging", "get_logger"]
