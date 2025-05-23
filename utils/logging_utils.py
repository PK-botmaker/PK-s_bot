import logging
import os
from logging.handlers import RotatingFileHandler

def setup_logging():
    """Set up logging for the bot. 📜"""
    log_level = logging.INFO
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Configure root logger 📝
    logger = logging.getLogger()
    logger.setLevel(log_level)

    # File handler with rotation 📂
    log_file = "/opt/render/project/src/logs/bot.log"
    file_handler = RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=3)  # 5MB per file, 3 backups
    file_handler.setFormatter(logging.Formatter(log_format))
    logger.addHandler(file_handler)

    # Console handler 🖥️
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(log_format))
    logger.addHandler(console_handler)