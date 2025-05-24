import logging
from telegram import Update
from telegram.ext import CallbackContext

logger = logging.getLogger(__name__)

def send_log_to_channel(context: CallbackContext, message: str):
    """Send a log message to the Telegram log channel. 📜"""
    LOG_CHANNEL_ID = os.getenv("LOG_CHANNEL_ID")
    if not LOG_CHANNEL_ID:
        logger.error("🚨 LOG_CHANNEL_ID not set in environment variables")
        return

    try:
        context.bot.send_message(chat_id=LOG_CHANNEL_ID, text=f"📝 {message}")
        logger.info(f"✅ Log sent to channel {LOG_CHANNEL_ID}: {message}")
    except Exception as e:
        logger.error(f"🚨 Failed to send log to channel {LOG_CHANNEL_ID}: {str(e)}")

def error_handler(update: Update, context: CallbackContext):
    """Handle errors gracefully and notify the user. 🚨"""
    error = context.error
    user_id = str(update.effective_user.id) if update.effective_user else "Unknown"
    username = update.effective_user.username or "Unknown"

    logger.error(f"🚨 Update {update} caused error: {error}")
    send_log_to_channel(context, f"Error occurred for user {user_id}: {str(error)} 🚨")

    try:
        update.effective_message.reply_text("🚫 An error occurred. Please try again later. 😓")
    except Exception as e:
        logger.error(f"🚨 Failed to send error message to user {user_id}: {str(e)}")
