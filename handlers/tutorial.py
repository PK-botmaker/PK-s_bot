from telegram import Update
from telegram.ext import CallbackContext
from utils.logging_utils import log_error
import logging

logger = logging.getLogger(__name__)

def tutorial(update: Update, context: CallbackContext):
    """📝 Show a tutorial for using the bot."""
    user_id = update.effective_user.id

    try:
        tutorial_text = (
            "📝 Welcome to the @bot_paiyan_official Tutorial! 🌟\n\n"
            "1️⃣ Use /start to see the main menu.\n"
            "2️⃣ Use /search <term> to find files.\n"
            "3️⃣ Admins can manage settings, clone bots, and more!\n"
            "4️⃣ Have fun cloning and sharing files! 🎉"
        )
        update.callback_query.message.reply_text(tutorial_text)
        logger.info(f"✅ User {user_id} viewed tutorial! 🌟")
    except Exception as e:
        update.callback_query.message.reply_text("⚠️ Failed to load tutorial! Try again! 😅")
        log_error(f"🚨 Tutorial error for user {user_id}: {str(e)}")
