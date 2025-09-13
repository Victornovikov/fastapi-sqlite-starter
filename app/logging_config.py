"""
Centralized logging configuration for FastAPI application.
Provides rotating file handler with consistent formatting across all loggers.
"""
import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional


def setup_logging(
    log_level: str = "INFO",
    log_dir: str = "logs",
    log_file: str = "app.log",
    max_bytes: int = 5 * 1024 * 1024,  # 5MB
    backup_count: int = 5,
    enable_console: bool = True
) -> RotatingFileHandler:
    """
    Configure centralized logging for the entire application.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory to store log files
        log_file: Name of the log file
        max_bytes: Maximum size of each log file before rotation
        backup_count: Number of backup files to keep
        enable_console: Whether to also log to console (useful for development)

    Returns:
        RotatingFileHandler instance for additional configuration if needed
    """

    # Create logs directory if it doesn't exist
    log_path = Path(log_dir)
    log_path.mkdir(exist_ok=True)

    # Create .gitkeep file to ensure directory is tracked but not log files
    gitkeep_path = log_path / ".gitkeep"
    if not gitkeep_path.exists():
        gitkeep_path.touch()

    # Set up the log format
    log_format = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format=log_format,
        datefmt=date_format
    )

    # Create rotating file handler
    file_handler = RotatingFileHandler(
        filename=log_path / log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8"
    )
    file_handler.setLevel(getattr(logging, log_level.upper()))
    file_handler.setFormatter(
        logging.Formatter(log_format, datefmt=date_format)
    )

    # Add handler to root logger
    root_logger = logging.getLogger()
    root_logger.addHandler(file_handler)

    # Configure Uvicorn loggers to use our file handler
    uvicorn_loggers = [
        "uvicorn",
        "uvicorn.error",
        "uvicorn.access",
        "uvicorn.asgi"
    ]

    for logger_name in uvicorn_loggers:
        logger = logging.getLogger(logger_name)
        logger.addHandler(file_handler)
        logger.setLevel(getattr(logging, log_level.upper()))
        # Prevent duplicate logs by not propagating to root logger
        if logger_name != "uvicorn":
            logger.propagate = False

    # Configure SQLAlchemy logger for database operations (less verbose)
    sqlalchemy_logger = logging.getLogger("sqlalchemy.engine")
    sqlalchemy_logger.addHandler(file_handler)
    if log_level.upper() == "DEBUG":
        sqlalchemy_logger.setLevel(logging.INFO)  # Even in DEBUG, SQL can be too verbose
    else:
        sqlalchemy_logger.setLevel(logging.WARNING)

    # Configure FastAPI/Starlette loggers
    for logger_name in ["fastapi", "starlette"]:
        logger = logging.getLogger(logger_name)
        logger.addHandler(file_handler)
        logger.setLevel(getattr(logging, log_level.upper()))

    # Optionally add console handler for development
    if enable_console:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(getattr(logging, log_level.upper()))
        console_handler.setFormatter(
            logging.Formatter(log_format, datefmt=date_format)
        )
        # Only add to specific loggers to avoid duplication
        for logger_name in ["uvicorn.error", "app"]:
            logger = logging.getLogger(logger_name)
            logger.addHandler(console_handler)

    # Log the logging configuration itself
    logger = logging.getLogger(__name__)
    logger.info(
        f"Logging configured: level={log_level}, "
        f"file={log_path / log_file}, "
        f"max_size={max_bytes / (1024*1024):.1f}MB, "
        f"backups={backup_count}"
    )

    return file_handler


def get_client_ip(request) -> str:
    """
    Extract client IP from request, checking for proxy headers.

    Args:
        request: FastAPI Request object

    Returns:
        Client IP address as string
    """
    # Check for proxy headers
    x_forwarded_for = request.headers.get("X-Forwarded-For")
    if x_forwarded_for:
        # Get the first IP in the chain
        return x_forwarded_for.split(",")[0].strip()

    # Check for X-Real-IP header
    x_real_ip = request.headers.get("X-Real-IP")
    if x_real_ip:
        return x_real_ip

    # Fall back to direct client IP
    if request.client:
        return request.client.host

    return "unknown"


def mask_sensitive_data(value: str, visible_chars: int = 4) -> str:
    """
    Mask sensitive data for logging, showing only first and last few characters.

    Args:
        value: Sensitive value to mask
        visible_chars: Number of characters to show at start and end

    Returns:
        Masked string
    """
    if not value or len(value) <= visible_chars * 2:
        return "***"

    return f"{value[:visible_chars]}...{value[-visible_chars:]}"


def sanitize_email(email: str) -> str:
    """
    Partially mask email for privacy while maintaining traceability.

    Args:
        email: Email address to sanitize

    Returns:
        Partially masked email
    """
    if not email or "@" not in email:
        return "invalid_email"

    local, domain = email.split("@", 1)
    if len(local) <= 2:
        masked_local = "*" * len(local)
    else:
        masked_local = f"{local[0]}{'*' * (len(local) - 2)}{local[-1]}"

    return f"{masked_local}@{domain}"


class LoggerMixin:
    """
    Mixin class to provide consistent logger instance to classes.
    """

    @property
    def logger(self) -> logging.Logger:
        """Get logger instance for the class."""
        if not hasattr(self, "_logger"):
            self._logger = logging.getLogger(
                f"{self.__class__.__module__}.{self.__class__.__name__}"
            )
        return self._logger