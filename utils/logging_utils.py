import os
import logging
from telegram import Bot
from utils.db_channel import get_setting

logger = logging.getLogger(__name__)

# Placeholder for the bot instance
log_bot = None

def set_log_bot(bot: Bot):
    """Set the bot instance for logging and database operations."""
    global log_bot
    log_bot = bot
    logger.info("✅ Log bot instance set in utils/logging_utils")
    
    # Also set the bot for db_channel operations
    from utils.db_channel import set_db_bot
    set_db_bot(bot)

def log_error(message: str):
    """Log an error message to the log channel."""
    global log_bot
    log_id = get_setting("log_id")
    if not log_bot:
        logger.error("🚨 Log bot not set in utils/logging_utils")
        return
    if not log_id:
        logger.error("🚨 LOG_ID not set")
        return

    try:
        log_bot.send_message(chat_id=log_id, text=f"🚨 ERROR: {message}")
        logger.info("✅ Sent error message to log channel")
    except Exception as e:
        logger.error(f"🚨 Failed to send error to log channel: {str(e)}")
