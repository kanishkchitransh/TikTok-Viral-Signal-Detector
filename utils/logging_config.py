"""
Structured logging configuration for TikTok Viral Signal Detector.
Uses structlog for structured, JSON-formatted logs.
"""

import logging
import sys
from pathlib import Path
from typing import Any
import structlog
from pythonjsonlogger import jsonlogger

from config.settings import get_settings


def setup_logging():
    """
    Configure structured logging for the application.
    Supports both JSON and console formats based on settings.
    """
    settings = get_settings()

    # Ensure log directory exists
    log_file = Path(settings.LOG_FILE_PATH)
    log_file.parent.mkdir(parents=True, exist_ok=True)

    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.LOG_LEVEL),
    )

    # Shared processors for all log entries
    shared_processors = [
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]

    if settings.LOG_FORMAT == "json":
        # JSON format for production
        processors = shared_processors + [
            structlog.processors.JSONRenderer()
        ]
    else:
        # Console format for development
        processors = shared_processors + [
            structlog.dev.ConsoleRenderer()
        ]

    # Configure structlog
    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Setup file handler with JSON formatting
    file_handler = logging.FileHandler(settings.LOG_FILE_PATH)
    file_handler.setLevel(getattr(logging, settings.LOG_LEVEL))

    if settings.LOG_FORMAT == "json":
        json_formatter = jsonlogger.JsonFormatter(
            '%(asctime)s %(name)s %(levelname)s %(message)s'
        )
        file_handler.setFormatter(json_formatter)

    # Add file handler to root logger
    root_logger = logging.getLogger()
    root_logger.addHandler(file_handler)

    # Reduce noise from third-party libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("playwright").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

    if not settings.DEBUG_MODE:
        logging.getLogger("TikTokApi").setLevel(logging.WARNING)


def get_logger(name: str = __name__) -> structlog.BoundLogger:
    """
    Get a structured logger instance.

    Args:
        name: Logger name (typically __name__)

    Returns:
        structlog.BoundLogger: Configured logger
    """
    return structlog.get_logger(name)


class LogContext:
    """
    Context manager for adding context to log messages.

    Usage:
        with LogContext(creator_id=123, agent="scraper") as logger:
            logger.info("processing_video", video_id="abc")
            # Logs: {"creator_id": 123, "agent": "scraper", "video_id": "abc", ...}
    """

    def __init__(self, **context):
        self.context = context
        self.bound_logger = None

    def __enter__(self):
        self.bound_logger = structlog.get_logger().bind(**self.context)
        return self.bound_logger

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.bound_logger.error(
                "context_exception",
                exc_type=exc_type.__name__,
                exc_msg=str(exc_val)
            )
        # Note: No need to unbind as we're using a bound instance
        # The context is scoped to this bound logger only


# Convenience functions for common log patterns
def log_agent_start(logger: structlog.BoundLogger, agent_name: str, **kwargs):
    """Log agent start with standard format."""
    logger.info(
        "agent_started",
        agent=agent_name,
        **kwargs
    )


def log_agent_complete(logger: structlog.BoundLogger, agent_name: str, duration: float = None, **kwargs):
    """Log agent completion with standard format."""
    log_data = {
        "agent": agent_name,
        **kwargs
    }
    if duration is not None:
        log_data["duration_seconds"] = round(duration, 2)

    logger.info("agent_completed", **log_data)


def log_agent_error(logger: structlog.BoundLogger, agent_name: str, error: Exception, **kwargs):
    """Log agent error with standard format."""
    logger.error(
        "agent_error",
        agent=agent_name,
        error_type=type(error).__name__,
        error_msg=str(error),
        **kwargs,
        exc_info=True
    )


def log_api_call(
    logger: structlog.BoundLogger,
    api_name: str,
    endpoint: str,
    status: str = "started",
    **kwargs
):
    """Log API call with standard format."""
    logger.info(
        "api_call",
        api=api_name,
        endpoint=endpoint,
        status=status,
        **kwargs
    )


def log_database_operation(
    logger: structlog.BoundLogger,
    operation: str,
    table: str,
    status: str = "started",
    **kwargs
):
    """Log database operation with standard format."""
    logger.info(
        "database_operation",
        operation=operation,
        table=table,
        status=status,
        **kwargs
    )


def log_video_processing(
    logger: structlog.BoundLogger,
    video_id: str,
    stage: str,
    status: str = "started",
    **kwargs
):
    """Log video processing with standard format."""
    logger.info(
        "video_processing",
        video_id=video_id,
        stage=stage,
        status=status,
        **kwargs
    )


def log_prediction(
    logger: structlog.BoundLogger,
    creator_handle: str,
    probability: float,
    **kwargs
):
    """Log prediction with standard format."""
    logger.info(
        "prediction_generated",
        creator_handle=creator_handle,
        viral_probability=round(probability, 3),
        **kwargs
    )


# Initialize logging on module import
setup_logging()


if __name__ == "__main__":
    # Test logging setup
    logger = get_logger(__name__)

    print("Testing structured logging...\n")

    # Test different log levels
    logger.debug("debug_message", key="value")
    logger.info("info_message", count=42, status="active")
    logger.warning("warning_message", threshold=0.8)
    logger.error("error_message", error_code=500)

    # Test convenience functions
    print("\nTesting convenience functions...")
    log_agent_start(logger, "test_agent", creator_id=123)
    log_agent_complete(logger, "test_agent", duration=1.5, videos_processed=10)
    log_api_call(logger, "TikTok", "/user/info", status="success", response_time=0.3)
    log_database_operation(logger, "INSERT", "creators", status="success", rows_affected=1)
    log_video_processing(logger, "abc123", "transcription", status="complete")
    log_prediction(logger, "@testuser", 0.85, confidence=0.92)

    # Test context manager
    print("\nTesting LogContext...")
    with LogContext(session_id="sess_123", user_id=456):
        logger.info("operation_in_context", operation="test")

    print("\n✓ Logging tests complete!")
    print(f"Check log file: {get_settings().LOG_FILE_PATH}")
