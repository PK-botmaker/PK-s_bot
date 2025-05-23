import os
import logging
from telegram import Bot
from datetime import datetime

logger = logging.getLogger(__name__)

# Global Bot instance for sending logs (will be set in bot.py)
log_bot = None

# Store cloned bot logs for table formatting
cloned_bot_logs = []

def set_log_bot(bot: Bot):
    """Set the global Bot instance for logging."""
    global log_bot
    log_bot = bot
    logger.info(f"ℹ️ Log bot initialized: {log_bot.get_me().username if log_bot else 'Not set'}")

def log_error(message: str, context=None):
    """Log an error message to console and send to LOG_ID chat if configured."""
    # Skip logging for "unknown" user
    if "user unknown" in message.lower():
        logger.info(f"⚠️ Skipped logging for unknown user: {message}")
        return

    logger.error(message)

    # Send to Telegram chat if LOG_ID is configured
    log_id = os.getenv("LOG_ID")
    if not log_id:
        logger.warning("⚠️ LOG_ID environment variable not set! Cannot send logs to Telegram chat.")
        print(f"ERROR: {message}")  # Fallback to console
        return

    if not log_bot:
        logger.warning("⚠️ Log bot not initialized! Cannot send logs to Telegram chat.")
        print(f"ERROR: {message}")  # Fallback to console
        return

    try:
        logger.info(f"ℹ️ Sending error log to LOG_ID {log_id}...")
        log_bot.send_message(
            chat_id=log_id,
            text=f"🚨 ERROR: {message}"
        )
        logger.info(f"✅ Sent error log to LOG_ID {log_id}: {message}")
    except Exception as e:
        logger.error(f"⚠️ Failed to send error log to LOG_ID {log_id}: {str(e)}")
        print(f"ERROR: {message} (Failed to send to LOG_ID: {str(e)})")  # Fallback to console

def log_clone_bot(username: str, bot_username: str, creator_id: str, creation_date: str, visibility: str, usage: str):
    """Log cloned bot creation in a table format to LOG_ID chat."""
    # Store the log entry
    cloned_bot_logs.append({
        "username": username,
        "bot_username": bot_username,
        "creator_id": creator_id,
        "creation_date": creation_date,
        "visibility": visibility,
        "usage": usage
    })

    # Build the table
    table_header = "📊 **Cloned Bots Table** 📊\n\n"
    table_rows = "| Username | Bots Cloned | Cloned Bots (with Mention) | Creation Date |\n"
    table_rows += "|----------|-------------|---------------------------|---------------|\n"
    
    total_bots = len(cloned_bot_logs)
    for log in cloned_bot_logs:
        table_rows += f"| {log['username']} (ID: {log['creator_id']}) | {total_bots} | @{log['bot_username']} | {log['creation_date']} |\n"

    log_message = table_header + table_rows

    # Send to Telegram chat if LOG_ID is configured
    log_id = os.getenv("LOG_ID")
    if not log_id:
        logger.warning("⚠️ LOG_ID environment variable not set! Cannot send logs to Telegram chat.")
        print(f"CLONE LOG: {log_message}")  # Fallback to console
        return

    if not log_bot:
        logger.warning("⚠️ Log bot not initialized! Cannot send logs to Telegram chat.")
        print(f"CLONE LOG: {log_message}")  # Fallback to console
        return

    try:
        logger.info(f"ℹ️ Sending clone bot log to LOG_ID {log_id}...")
        log_bot.send_message(
            chat_id=log_id,
            text=log_message,
            parse_mode="Markdown"
        )
        logger.info(f"✅ Sent cloned bot log to LOG_ID {log_id}: {log_message}")
    except Exception as e:
        logger.error(f"⚠️ Failed to send cloned bot log to LOG_ID {log_id}: {str(e)}")
        print(f"CLONE LOG: {log_message} (Failed to send to LOG_ID: {str(e)})")  # Fallback to console
