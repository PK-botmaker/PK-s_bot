from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
from utils.db_channel import set_setting, get_setting
from utils.logging_utils import log_error
import logging

logger = logging.getLogger(__name__)

def set_custom_caption(update: Update, context: CallbackContext):
    """📝 Set a custom caption for files (main bot only)."""
    user_id = update.effective_user.id
    if str(user_id) not in context.bot_data.get("admin_ids", []):
        update.callback_query.answer("🚫 Admins only!")
        log_error(f"🚨 Unauthorized caption access by {user_id}")
        return
    if not context.bot_data.get("is_main_bot", False):
        update.callback_query.answer("🚫 Main bot only!")
        log_error(f"🚨 Unauthorized caption access by {user_id} on clone")
        return

    try:
        context.user_data["awaiting_caption"] = True
        update.callback_query.message.reply_text(
            "📝 Send the custom caption for files! 📄",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Cancel 🚫", callback_data="cancel_caption")]
            ])
        )
        logger.info(f"✅ Admin {user_id} started setting caption! 🌟")
    except Exception as e:
        update.callback_query.message.reply_text("⚠️ Failed to set caption! Try again! 😅")
        log_error(f"🚨 Caption error for {user_id}: {str(e)}")

def set_custom_buttons(update: Update, context: CallbackContext):
    """🔘 Set custom buttons for files (main bot only)."""
    user_id = update.effective_user.id
    if str(user_id) not in context.bot_data.get("admin_ids", []):
        update.callback_query.answer("🚫 Admins only!")
        log_error(f"🚨 Unauthorized buttons access by {user_id}")
        return
    if not context.bot_data.get("is_main_bot", False):
        update.callback_query.answer("🚫 Main bot only!")
        log_error(f"🚨 Unauthorized buttons access by {user_id} on clone")
        return

    try:
        context.user_data["awaiting_buttons"] = True
        update.callback_query.message.reply_text(
            "🔘 Send the custom buttons in format: Button Text | URL (one per line)\n"
            "Example:\nDownload | https://example.com\nSupport | https://t.me/support",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Cancel 🚫", callback_data="cancel_buttons")]
            ])
        )
        logger.info(f"✅ Admin {user_id} started setting buttons! 🌟")
    except Exception as e:
        update.callback_query.message.reply_text("⚠️ Failed to set buttons! Try again! 😅")
        log_error(f"🚨 Buttons error for {user_id}: {str(e)}")

def handle_caption_input(update: Update, context: CallbackContext):
    """📝 Handle custom caption input."""
    user_id = update.effective_user.id
    if not context.user_data.get("awaiting_caption"):
        return
    if str(user_id) not in context.bot_data.get("admin_ids", []):
        update.message.reply_text("🚫 Admins only!")
        log_error(f"🚨 Unauthorized caption input by {user_id}")
        return
    if not context.bot_data.get("is_main_bot", False):
        update.message.reply_text("🚫 Main bot only!")
        log_error(f"🚨 Unauthorized caption input by {user_id} on clone")
        return

    try:
        caption = update.message.text.strip()
        set_setting("custom_caption", caption)
        context.user_data["awaiting_caption"] = None
        update.message.reply_text("✅ Custom caption set! 🎉")
        logger.info(f"✅ Admin {user_id} set custom caption! 🌟")
    except Exception as e:
        update.message.reply_text("⚠️ Failed to save caption! Try again! 😅")
        log_error(f"🚨 Caption input error for {user_id}: {str(e)}")

def handle_buttons_input(update: Update, context: CallbackContext):
    """🔘 Handle custom buttons input."""
    user_id = update.effective_user.id
    if not context.user_data.get("awaiting_buttons"):
        return
    if str(user_id) not in context.bot_data.get("admin_ids", []):
        update.message.reply_text("🚫 Admins only!")
        log_error(f"🚨 Unauthorized buttons input by {user_id}")
        return
    if not context.bot_data.get("is_main_bot", False):
        update.message.reply_text("🚫 Main bot only!")
        log_error(f"🚨 Unauthorized buttons input by {user_id} on clone")
        return

    try:
        buttons_text = update.message.text.strip()
        buttons = []
        for line in buttons_text.split("\n"):
            if "|" in line:
                text, url = [part.strip() for part in line.split("|", 1)]
                buttons.append({"text": text, "url": url})
        set_setting("custom_buttons", buttons)
        context.user_data["awaiting_buttons"] = None
        update.message.reply_text("✅ Custom buttons set! 🎉")
        logger.info(f"✅ Admin {user_id} set custom buttons! 🌟")
    except Exception as e:
        update.message.reply_text("⚠️ Failed to save buttons! Check format! 😅")
        log_error(f"🚨 Buttons input error for {user_id}: {str(e)}")
