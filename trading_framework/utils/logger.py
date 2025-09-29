"""
Logging setup and configuration for the trading framework.
"""

import os
import sys
from pathlib import Path
from loguru import logger
from typing import Optional

from ..config import get_config


def setup_logging(config: Optional[dict] = None) -> None:
    """
    Setup logging configuration.
    
    Args:
        config: Logging configuration dictionary. If None, uses default config.
    """
    if config is None:
        config = get_config().get('logging', {})
    
    # Remove default handler
    logger.remove()
    
    # Console handler
    logger.add(
        sys.stdout,
        format=config.get('format', "{time:YYYY-MM-DD HH:mm:ss} | {level} | {name} | {message}"),
        level=config.get('level', 'INFO'),
        colorize=True
    )
    
    # File handler
    log_file = config.get('file', 'logs/trading_framework.log')
    log_dir = os.path.dirname(log_file)
    
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)
    
    logger.add(
        log_file,
        format=config.get('format', "{time:YYYY-MM-DD HH:mm:ss} | {level} | {name} | {message}"),
        level=config.get('level', 'INFO'),
        rotation=config.get('max_file_size', '10 MB'),
        retention=config.get('retention', '30 days'),
        compression="zip"
    )
    
    logger.info("Logging configured successfully")


def get_logger(name: str):
    """
    Get a logger instance.
    
    Args:
        name: Logger name
        
    Returns:
        Logger instance
    """
    return logger.bind(name=name)