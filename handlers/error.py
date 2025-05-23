import logging
from telegram import Update
from telegram.ext import CallbackContext
from utils.logging_utils import log_error

logger = logging.getLogger(__name__)

def error_handler(update: Update, context: CallbackContext):
    """Handle errors and log them."""
    try:
        # Log the error
        error_msg = f"Update '{update}' caused error '{context.error}'"
        logger.error(error_msg)
        log_error(error_msg)

        # Notify the user if possible
        if update and update.effective_message:
            update.effective_message.reply_text("⚠️ An error occurred! The admin has been notified. Please try again later! 😅")
    except Exception as e:
        logger.error(f"🚨 Error in error_handler: {str(e)}")
        log_error(f"🚨 Error in error_handler: {str(e)}")
