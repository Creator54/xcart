import logging
import sys
from typing import Any, Dict
from .config import settings


class CustomFormatter(logging.Formatter):
    """Custom formatter with colors"""

    grey = "\x1b[38;21m"
    blue = "\x1b[38;5;39m"
    yellow = "\x1b[38;5;226m"
    red = "\x1b[38;5;196m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"

    def __init__(self, fmt: str):
        super().__init__()
        self.fmt = fmt
        self.FORMATS = {
            logging.DEBUG: self.grey + self.fmt + self.reset,
            logging.INFO: self.blue + self.fmt + self.reset,
            logging.WARNING: self.yellow + self.fmt + self.reset,
            logging.ERROR: self.red + self.fmt + self.reset,
            logging.CRITICAL: self.bold_red + self.fmt + self.reset,
        }

    def format(self, record: logging.LogRecord) -> str:
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


def setup_logging() -> None:
    """Setup logging configuration"""
    logger = logging.getLogger(settings.OTEL_SERVICE_NAME)
    logger.setLevel(getattr(logging, settings.LOG_LEVEL))

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, settings.LOG_LEVEL))

    # Format
    console_handler.setFormatter(CustomFormatter(settings.LOG_FORMAT))

    # Add handlers
    logger.addHandler(console_handler)


def get_logger(name: str) -> logging.Logger:
    """Get logger instance"""
    return logging.getLogger(f"{settings.OTEL_SERVICE_NAME}.{name}")


def log_request_info(
    logger: logging.Logger, request: Any, extra: Dict[str, Any] = None
) -> None:
    """Log request information"""
    info = {
        "method": request.method,
        "url": str(request.url),
        "client": request.client.host if request.client else None,
    }
    if extra:
        info.update(extra)
    logger.info(f"Request: {info}")


def log_response_info(
    logger: logging.Logger, response: Any, duration: float, extra: Dict[str, Any] = None
) -> None:
    """Log response information"""
    info = {
        "status_code": response.status_code,
        "duration_ms": round(duration * 1000, 2),
    }
    if extra:
        info.update(extra)
    logger.info(f"Response: {info}")
