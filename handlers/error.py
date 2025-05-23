import logging
from telegram import Update
from telegram.ext import CallbackContext

logger = logging.getLogger(__name__)

def error_handler(update: Update, context: CallbackContext):
    """Handle errors and notify the user. 🚨"""
    try:
        raise context.error
    except Exception as e:
        logger.error(f"🚨 Error occurred: {str(e)}", exc_info=True)
        if update:
            if update.message:
                update.message.reply_text("🚫 An error occurred. Please try again later. 😓")
            elif update.callback_query:
                update.callback_query.message.reply_text("🚫 An error occurred. Please try again later. 😓")