import logging
import os
from logging.handlers import RotatingFileHandler
from config import Config

def setup_logger():
    """Configure and return a logger instance"""
    # Create logger
    logger = logging.getLogger('trading_bot')
    logger.setLevel(getattr(logging, Config.LOG_LEVEL))
    
    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # File handler
    file_handler = RotatingFileHandler(
        Config.LOG_FILE,
        maxBytes=10485760,  # 10MB
        backupCount=5
    )
    file_handler.setFormatter(formatter)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

# Create the logger instance to be imported by other modules
logger = setup_logger()