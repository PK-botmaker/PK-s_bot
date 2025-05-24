import logging
import os
from logging.handlers import RotatingFileHandler

def setup_logging():
    """Set up logging with rotation for the bot. 📜"""
    log_directory = "/opt/render/project/src/logs"
    if not os.path.exists(log_directory):
        os.makedirs(log_directory)

    log_file = os.path.join(log_directory, "bot.log")

    # Create a rotating file handler (max 5 MB, keep 5 backups) 📊
    file_handler = RotatingFileHandler(log_file, maxBytes=5 * 1024 * 1024, backupCount=5)
    file_handler.setLevel(logging.INFO)
    file_formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(file_formatter)

    # Create a console handler 🖥️
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter("%(name)s - %(levelname)s - %(message)s")
    console_handler.setFormatter(console_formatter)

    # Configure the root logger 🌳
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    logging.info("✅ Logging setup completed")
