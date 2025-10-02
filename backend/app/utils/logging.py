"""
Logging utilities for the CSR Lambda API
"""
import logging
import json
from typing import Dict, Any
from datetime import datetime


class JSONFormatter(logging.Formatter):
    """
    Custom JSON formatter for structured logging
    """
    
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add extra fields if present
        if hasattr(record, 'request_id'):
            log_entry["request_id"] = record.request_id
            
        if hasattr(record, 'user_id'):
            log_entry["user_id"] = record.user_id
            
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
            
        return json.dumps(log_entry)


def setup_logging(level: str = "INFO") -> None:
    """
    Setup structured logging for the application
    """
    # Create logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, level.upper()))
    
    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Create console handler with JSON formatter
    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter())
    logger.addHandler(handler)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name
    """
    return logging.getLogger(name)


def log_api_call(
    logger: logging.Logger,
    method: str,
    endpoint: str,
    status_code: int,
    duration: float,
    request_id: str,
    user_id: str = None
) -> None:
    """
    Log API call information
    """
    logger.info(
        f"API Call: {method} {endpoint} - {status_code} ({duration:.3f}s)",
        extra={
            "request_id": request_id,
            "user_id": user_id,
            "method": method,
            "endpoint": endpoint,
            "status_code": status_code,
            "duration": duration
        }
    )