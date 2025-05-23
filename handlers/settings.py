from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
from utils.db_channel import set_setting, get_setting
from utils.logging_utils import log_error
from handlers.start import shortener_menu
import logging

logger = logging.getLogger(__name__)

def handle_settings(update: Update, context: CallbackContext):
    """⚙️ Handle bot settings based on callback patterns (main bot only)."""
    user_id = update.effective_user.id
    if str(user_id) not in context.bot_data.get("admin_ids", []):
        update.callback_query.answer("🚫 Admins only!")
        log_error(f"🚨 Unauthorized settings action by {user_id}")
        return
    if not context.bot_data.get("is_main_bot", False):
        update.callback_query.answer("🚫 Main bot only!")
        log_error(f"🚨 Unauthorized settings action by {user_id} on clone")
        return

    callback_data = update.callback_query.data
    try:
        if callback_data == "add_channel":
            context.user_data["awaiting_channel"] = "add"
            update.callback_query.message.reply_text(
                "📺 Send the channel ID or username to add! (e.g., @ChannelName or -100123456789)"
            )
            logger.info(f"✅ Admin {user_id} started adding channel! 🌟")
        elif callback_data == "remove_channel":
            context.user_data["awaiting_channel"] = "remove"
            update.callback_query.message.reply_text(
                "🗑️ Send the channel ID or username to remove! (e.g., @ChannelName or -100123456789)"
            )
            logger.info(f"✅ Admin {user_id} started removing channel! 🌟")
        elif callback_data == "set_group_link":
            context.user_data["awaiting_group_link"] = True
            update.callback_query.message.reply_text(
                "🔗 Send the group link! (e.g., https://t.me/+GroupLink)"
            )
            logger.info(f"✅ Admin {user_id} started setting group link! 🌟")
        elif callback_data == "shortener":
            shortener_menu(update, context)
        elif callback_data in ["set_force_sub", "set_db_channel", "set_log_channel", "welcome_message", "auto_delete", "banner", "set_webhook", "anti_ban", "enable_redis"]:
            update.callback_query.message.reply_text(
                f"⚙️ {callback_data.replace('_', ' ').title()} is not fully implemented yet! Coming soon! 🚧"
            )
            logger.info(f"✅ Admin {user_id} tried {callback_data} (unimplemented)! 🌟")
        else:
            update.callback_query.message.reply_text("⚠️ Unknown setting! Try again! 😅")
            log_error(f"🚨 Unknown callback {callback_data} by {user_id}")
    except Exception as e:
        update.callback_query.message.reply_text("⚠️ Failed to process setting! Try again! 😅")
        log_error(f"🚨 Settings error for {user_id}: {str(e)}")

def handle_settings_input(update: Update, context: CallbackContext):
    """📝 Handle input for settings (channels, group link, etc.)."""
    user_id = update.effective_user.id
    if str(user_id) not in context.bot_data.get("admin_ids", []):
        update.message.reply_text("🚫 Admins only!")
        log_error(f"🚨 Unauthorized settings input by {user_id}")
        return
    if not context.bot_data.get("is_main_bot", False):
        update.message.reply_text("🚫 Main bot only!")
        log_error(f"🚨 Unauthorized settings input by {user_id} on clone")
        return

    try:
        if context.user_data.get("awaiting_channel"):
            action = context.user_data["awaiting_channel"]
            channel = update.message.text.strip()
            channels = get_setting("channels", [])
            if action == "add":
                if channel not in channels:
                    channels.append(channel)
                    set_setting("channels", channels)
                    update.message.reply_text(f"📺 Channel {channel} added! 🎉")
                    logger.info(f"✅ Admin {user_id} added channel {channel}! 🌟")
                else:
                    update.message.reply_text(f"⚠️ Channel {channel} already added! 😅")
            elif action == "remove":
                if channel in channels:
                    channels.remove(channel)
                    set_setting("channels", channels)
                    update.message.reply_text(f"🗑️ Channel {channel} removed! 🎉")
                    logger.info(f"✅ Admin {user_id} removed channel {channel}! 🌟")
                else:
                    update.message.reply_text(f"⚠️ Channel {channel} not found! 😅")
            context.user_data["awaiting_channel"] = None
        elif context.user_data.get("awaiting_group_link"):
            group_link = update.message.text.strip()
            if not group_link.startswith("https://t.me/"):
                update.message.reply_text("⚠️ Invalid group link! Must start with https://t.me/ 😅")
                log_error(f"🚨 Invalid group link input by {user_id}")
                return
            set_setting("group_link", group_link)
            update.message.reply_text("🔗 Group link set! 🎉")
            logger.info(f"✅ Admin {user_id} set group link! 🌟")
            context.user_data["awaiting_group_link"] = None
        else:
            update.message.reply_text("⚠️ No setting input expected! Use the menu! 😅")
    except Exception as e:
        update.message.reply_text("⚠️ Failed to process input! Try again! 😅")
        log_error(f"🚨 Settings input error for {user_id}: {str(e)}")
