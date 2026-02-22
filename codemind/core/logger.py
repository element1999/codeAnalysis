"""Logging configuration"""

import logging
import os
from pathlib import Path

def setup_logger():
    """Setup logger"""
    logger = logging.getLogger("codemind")
    logger.setLevel(logging.INFO)
    
    # Remove existing handlers
    for handler in logger.handlers:
        logger.removeHandler(handler)
    
    # Console handler - set to DEBUG to show all details
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_formatter = logging.Formatter(
        "%(message)s"
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler
    log_dir = Path(".codemind/logs")
    log_dir.mkdir(exist_ok=True, parents=True)
    log_file = log_dir / "codemind.log"
    
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    return logger

logger = setup_logger()