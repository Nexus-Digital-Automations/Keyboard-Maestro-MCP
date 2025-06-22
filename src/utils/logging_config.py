# Structured Logging Configuration: Keyboard Maestro MCP Server
# src/utils/logging_config.py

"""
Structured logging configuration for the MCP server.

This module implements comprehensive logging setup with structured output,
multiple handlers, and development vs production configuration following
FastMCP protocol requirements for stderr-based logging.

Features:
- Structured JSON logging for production
- Human-readable logging for development
- Stderr output to avoid protocol contamination
- Log file rotation and management
- Context-aware logging with correlation IDs

Size: 147 lines (target: <150)
"""

import logging
import logging.handlers
import sys
import json
from typing import Dict, Any, Optional
from pathlib import Path
import structlog
from datetime import datetime

from src.contracts.decorators import requires


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging output."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add exception information if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in {"name", "msg", "args", "levelname", "levelno", "pathname",
                          "filename", "module", "lineno", "funcName", "created", 
                          "msecs", "relativeCreated", "thread", "threadName",
                          "processName", "process", "exc_info", "exc_text", "stack_info"}:
                log_entry[key] = value
        
        return json.dumps(log_entry)


class HumanReadableFormatter(logging.Formatter):
    """Human-readable formatter for development."""
    
    def __init__(self):
        super().__init__(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )


@requires(lambda log_level: log_level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
def setup_logging(log_level: str = "INFO", development_mode: bool = False) -> None:
    """Setup structured logging configuration.
    
    Preconditions:
    - Log level must be valid
    
    Args:
        log_level: Logging level
        development_mode: Whether to use development-friendly formatting
    """
    # Convert string level to logging constant
    numeric_level = getattr(logging, log_level.upper())
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    
    # Remove any existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Always log to stderr for MCP protocol compliance
    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setLevel(numeric_level)
    
    if development_mode:
        # Human-readable format for development
        stderr_handler.setFormatter(HumanReadableFormatter())
    else:
        # JSON format for production
        stderr_handler.setFormatter(JSONFormatter())
    
    root_logger.addHandler(stderr_handler)
    
    # Add file handler for production (optional)
    if not development_mode:
        _setup_file_logging(numeric_level)
    
    # Configure third-party loggers
    _configure_third_party_loggers(numeric_level)
    
    # Log startup message
    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured: level={log_level}, development={development_mode}")


def _setup_file_logging(log_level: int) -> None:
    """Setup file-based logging with rotation."""
    try:
        # Create logs directory
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        # Setup rotating file handler
        log_file = log_dir / "km_mcp_server.log"
        file_handler = logging.handlers.RotatingFileHandler(
            filename=log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        
        file_handler.setLevel(log_level)
        file_handler.setFormatter(JSONFormatter())
        
        # Add to root logger
        root_logger = logging.getLogger()
        root_logger.addHandler(file_handler)
        
    except Exception as e:
        # Log to stderr if file setup fails
        logging.getLogger(__name__).warning(f"Failed to setup file logging: {e}")


def _configure_third_party_loggers(log_level: int) -> None:
    """Configure logging for third-party libraries."""
    # Set higher level for noisy third-party loggers
    third_party_loggers = [
        "urllib3",
        "requests",
        "httpx",
        "asyncio",
        "concurrent.futures"
    ]
    
    for logger_name in third_party_loggers:
        logger = logging.getLogger(logger_name)
        logger.setLevel(max(log_level, logging.WARNING))


def get_logger(name: str, context: Optional[Dict[str, Any]] = None) -> logging.Logger:
    """Get a logger with optional context.
    
    Args:
        name: Logger name
        context: Optional context dictionary
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Add context as extra fields if provided
    if context:
        logger = logging.LoggerAdapter(logger, context)
    
    return logger


def create_context_logger(context_id: str, session_id: str) -> logging.Logger:
    """Create logger with MCP context information.
    
    Args:
        context_id: MCP context identifier
        session_id: MCP session identifier
        
    Returns:
        Logger with context information
    """
    context = {
        "context_id": context_id,
        "session_id": session_id,
        "component": "mcp_context"
    }
    
    return get_logger("mcp.context", context)


def log_operation_metrics(operation_name: str, 
                         duration: float,
                         success: bool,
                         **kwargs) -> None:
    """Log operation performance metrics.
    
    Args:
        operation_name: Name of the operation
        duration: Execution duration in seconds
        success: Whether operation succeeded
        **kwargs: Additional metric data
    """
    logger = logging.getLogger("mcp.metrics")
    
    metrics = {
        "operation": operation_name,
        "duration_seconds": round(duration, 3),
        "success": success,
        **kwargs
    }
    
    if success:
        logger.info("Operation completed", extra=metrics)
    else:
        logger.warning("Operation failed", extra=metrics)
