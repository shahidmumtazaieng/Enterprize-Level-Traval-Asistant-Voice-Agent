import logging
import sys
from typing import Optional
import json
from datetime import datetime

class CustomFormatter(logging.Formatter):
    """Custom formatter for better log formatting"""
    
    grey = "\x1b[38;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s (%(filename)s:%(lineno)d)"

    FORMATS = {
        logging.DEBUG: grey + format + reset,
        logging.INFO: grey + format + reset,
        logging.WARNING: yellow + format + reset,
        logging.ERROR: red + format + reset,
        logging.CRITICAL: bold_red + format + reset
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)

def setup_logger(
    name: str,
    level: int = logging.INFO,
    log_file: Optional[str] = None
) -> logging.Logger:
    """
    Set up a logger with custom formatting
    
    Args:
        name: Logger name
        level: Logging level
        log_file: Optional file to log to
        
    Returns:
        logging.Logger: Configured logger
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Prevent adding multiple handlers
    if logger.handlers:
        return logger
    
    # Create console handler with custom formatter
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(CustomFormatter())
    logger.addHandler(console_handler)
    
    # Create file handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    return logger

def log_session_event(
    logger: logging.Logger,
    session_id: str,
    event_type: str,
    message: str,
    metadata: Optional[dict] = None
):
    """
    Log a session event with structured data
    
    Args:
        logger: Logger instance
        session_id: Session identifier
        event_type: Type of event
        message: Event message
        metadata: Optional metadata
    """
    log_data = {
        "session_id": session_id,
        "event_type": event_type,
        "message": message,
        "timestamp": datetime.utcnow().isoformat(),
    }
    
    if metadata:
        log_data["metadata"] = metadata
    
    logger.info(json.dumps(log_data))

def log_error(
    logger: logging.Logger,
    session_id: str,
    error_type: str,
    message: str,
    exception: Optional[Exception] = None,
    metadata: Optional[dict] = None
):
    """
    Log an error with structured data
    
    Args:
        logger: Logger instance
        session_id: Session identifier
        error_type: Type of error
        message: Error message
        exception: Optional exception
        metadata: Optional metadata
    """
    log_data = {
        "session_id": session_id,
        "error_type": error_type,
        "message": message,
        "timestamp": datetime.utcnow().isoformat(),
    }
    
    if exception:
        log_data["exception"] = {
            "type": type(exception).__name__,
            "message": str(exception)
        }
    
    if metadata:
        log_data["metadata"] = metadata
    
    logger.error(json.dumps(log_data))