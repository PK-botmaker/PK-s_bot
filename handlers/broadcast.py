from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
from utils.db_channel import get_setting
from utils.logging_utils import log_error
import logging

logger = logging.getLogger(__name__)

def broadcast(update: Update, context: CallbackContext):
    """📢 Initiate a broadcast for admins (main bot only)."""
    user_id = update.effective_user.id
    if str(user_id) not in context.bot_data.get("admin_ids", []):
        update.callback_query.answer("🚫 Admins only!")
        log_error(f"🚨 Unauthorized broadcast attempt by {user_id}")
        return
    if not context.bot_data.get("is_main_bot", False):
        update.callback_query.answer("🚫 Main bot only!")
        log_error(f"🚨 Unauthorized broadcast attempt by {user_id} on clone")
        return

    try:
        context.user_data["awaiting_broadcast"] = True
        update.callback_query.message.reply_text(
            "📢 Send the message you want to broadcast! 🗣️\n"
            "It’ll go to all users or the configured channel! 🌐",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Cancel 🚫", callback_data="cancel_broadcast")]
            ])
        )
        logger.info(f"✅ Admin {user_id} started broadcast! 🌟")
    except Exception as e:
        update.callback_query.message.reply_text("⚠️ Oops! Broadcast setup failed! Try again! 😅")
        log_error(f"🚨 Broadcast setup error for {user_id}: {str(e)}")

def handle_broadcast_input(update: Update, context: CallbackContext):
    """📝 Handle the broadcast message input."""
    user_id = update.effective_user.id
    if not context.user_data.get("awaiting_broadcast"):
        return
    if str(user_id) not in context.bot_data.get("admin_ids", []):
        update.message.reply_text("🚫 Admins only!")
        log_error(f"🚨 Unauthorized broadcast input by {user_id}")
        return
    if not context.bot_data.get("is_main_bot", False):
        update.message.reply_text("🚫 Main bot only!")
        log_error(f"🚨 Unauthorized broadcast input by {user_id} on clone")
        return

    try:
        message = update.message.text.strip()
        log_channel = get_setting("log_channel", None)
        if log_channel:
            context.bot.send_message(chat_id=log_channel, text=f"📢 Broadcast: {message}")
            update.message.reply_text("✅ Broadcast sent to log channel! 🎉")
            logger.info(f"✅ Admin {user_id} broadcasted to log channel! 🌟")
        else:
            update.message.reply_text(
                "⚠️ No log channel set! Set one in settings first! 😅",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("Go to Settings ⚙️", callback_data="settings")]
                ])
            )
            logger.info(f"⚠️ Admin {user_id} attempted broadcast without log channel! 🌟")
        context.user_data["awaiting_broadcast"] = None
    except Exception as e:
        update.message.reply_text("⚠️ Failed to send broadcast! Try again! 😅")
        log_error(f"🚨 Broadcast error for {user_id}: {str(e)}")

def cancel_broadcast(update: Update, context: CallbackContext):
    """🚫 Cancel the broadcast process."""
    user_id = update.effective_user.id
    if str(user_id) not in context.bot_data.get("admin_ids", []):
        update.callback_query.answer("🚫 Admins only!")
        log_error(f"🚨 Unauthorized broadcast cancel by {user_id}")
        return
    if not context.bot_data.get("is_main_bot", False):
        update.callback_query.answer("🚫 Main bot only!")
        log_error(f"🚨 Unauthorized broadcast cancel by {user_id} on clone")
        return

    try:
        if context.user_data.get("awaiting_broadcast"):
            context.user_data["awaiting_broadcast"] = None
            update.callback_query.message.reply_text("✅ Broadcast cancelled! 🎉")
            logger.info(f"✅ Admin {user_id} cancelled broadcast! 🌟")
        else:
            update.callback_query.message.reply_text("⚠️ No broadcast to cancel! 😅")
    except Exception as e:
        update.callback_query.message.reply_text("⚠️ Failed to cancel broadcast! Try again! 😅")
        log_error(f"🚨 Broadcast cancel error for {user_id}: {str(e)}")
