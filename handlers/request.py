from telegram import Update
from telegram.ext import CallbackContext
from utils.db_channel import get_setting
from utils.logging_utils import log_error
import logging

logger = logging.getLogger(__name__)

def handle_request(update: Update, context: CallbackContext):
    """📩 Handle user requests and forward to admin channel."""
    user_id = update.effective_user.id
    request_text = update.message.text.strip()

    try:
        log_channel = get_setting("log_channel", None)
        if not log_channel:
            update.message.reply_text("⚠️ Request feature not set up! Contact the admin! 😅")
            logger.info(f"⚠️ User {user_id} attempted request - no log channel set")
            return

        context.bot.send_message(
            chat_id=log_channel,
            text=f"📩 New Request from User {user_id}:\n\n{request_text}"
        )
        update.message.reply_text("✅ Your request has been sent to the admins! 🎉")
        logger.info(f"✅ User {user_id} sent request: {request_text}! 🌟")
    except Exception as e:
        update.message.reply_text("⚠️ Failed to send request! Try again! 😅")
        log_error(f"🚨 Request error for user {user_id}: {str(e)}")
