"""
Logging configuration for the application.
"""
import logging
import sys
from pathlib import Path
from datetime import datetime

from .config import Config


def setup_logging(log_file: str = None) -> None:
    """
    Setup application logging.
    
    Args:
        log_file: Optional specific log file name
    """
    # Create logs directory
    Config.LOGS_DIR.mkdir(exist_ok=True)
    
    # Generate log filename
    if not log_file:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file = Config.LOGS_DIR / f"infinite_lives_{timestamp}.log"
    else:
        log_file = Config.LOGS_DIR / log_file
    
    # Configure logging
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Root logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, Config.LOG_LEVEL))
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter('%(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(log_format)
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    logger.info(f"Logging initialized. File: {log_file}")


def get_logger(name: str) -> logging.Logger:
    """Get a logger for a module."""
    return logging.getLogger(name)
