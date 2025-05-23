import logging
from telegram import Update
from telegram.ext import CallbackContext
from handlers.start import shortener_menu
from utils.db_channel import set_setting

logger = logging.getLogger(__name__)

# Dictionary to store shortener settings (in-memory for now; consider saving to DB in production)
SHORTENER_SETTINGS = {}

def handle_settings(update: Update, context: CallbackContext):
    """Handle settings callbacks for admins."""
    query = update.callback_query
    user_id = str(update.effective_user.id)
    if user_id not in context.bot_data.get("admin_ids", []):
        query.answer("🚫 Admins only!")
        logger.info(f"🚫 Unauthorized settings callback by user {user_id}: {query.data}")
        return

    callback_data = query.data

    if callback_data == "shortener":
        shortener_menu(update, context)
        return

    elif callback_data == "set_shortener_api":
        query.message.reply_text("🔗 Please send the URL Shortener API URL (e.g., https://api.shortener.com/shorten):")
        context.user_data["awaiting_input"] = "shortener_api"
        logger.info(f"ℹ️ Awaiting shortener API URL from admin {user_id}")

    elif callback_data == "set_shortener_key":
        query.message.reply_text("🔑 Please send the API key for the URL Shortener:")
        context.user_data["awaiting_input"] = "shortener_key"
        logger.info(f"ℹ️ Awaiting shortener API key from admin {user_id}")

    elif callback_data == "disable_shortener":
        if "shortener" in SHORTENER_SETTINGS:
            del SHORTENER_SETTINGS["shortener"]
            query.message.reply_text("✅ URL Shortener disabled! 🚫")
            logger.info(f"✅ Shortener disabled by admin {user_id}")
        else:
            query.message.reply_text("ℹ️ URL Shortener is already disabled! 🚫")
            logger.info(f"ℹ️ Shortener already disabled for admin {user_id}")
        return

    elif callback_data == "set_db_channel":
        query.message.reply_text("📂 Please send the chat ID of the database channel (e.g., -1001234567890):")
        context.user_data["awaiting_input"] = "db_channel_id"
        logger.info(f"ℹ️ Awaiting DB channel ID from admin {user_id}")

    elif callback_data == "set_log_channel":
        query.message.reply_text("📜 Please send the chat ID of the log channel (e.g., -1000987654321):")
        context.user_data["awaiting_input"] = "log_id"
        logger.info(f"ℹ️ Awaiting log channel ID from admin {user_id}")

    # Placeholder for other settings handlers
    elif callback_data in ["add_channel", "remove_channel", "set_force_sub", "set_group_link", "welcome_message", "auto_delete", "banner", "set_webhook", "anti_ban", "enable_redis"]:
        query.message.reply_text(f"⚙️ Feature '{callback_data}' is not yet implemented. Stay tuned! 🚀")
        logger.info(f"ℹ️ Unimplemented settings callback by admin {user_id}: {callback_data}")
        return

    query.answer()
    logger.info(f"✅ Handled settings callback for admin {user_id}: {callback_data}")

def handle_settings_input(update: Update, context: CallbackContext):
    """Handle text input for settings configuration."""
    user_id = str(update.effective_user.id)
    if user_id not in context.bot_data.get("admin_ids", []):
        update.message.reply_text("🚫 Admins only!")
        logger.info(f"🚫 Unauthorized settings input by user {user_id}")
        return

    if "awaiting_input" not in context.user_data:
        update.message.reply_text("⚠️ No settings input expected! Please use the settings menu to configure options. ⚙️")
        logger.info(f"⚠️ Unexpected settings input from admin {user_id}")
        return

    input_type = context.user_data["awaiting_input"]
    text = update.message.text.strip()

    if input_type == "shortener_api":
        SHORTENER_SETTINGS["shortener_api"] = text
        update.message.reply_text(f"✅ Shortener API set to: {text} 🔗")
        logger.info(f"✅ Set shortener API to {text} by admin {user_id}")
    elif input_type == "shortener_key":
        SHORTENER_SETTINGS["shortener_key"] = text
        update.message.reply_text(f"✅ Shortener API key set! 🔑")
        logger.info(f"✅ Set shortener API key by admin {user_id}")
    elif input_type == "db_channel_id":
        try:
            # Validate the chat ID format (should start with -100 for channels)
            if not text.startswith("-100") or not text[1:].isdigit():
                update.message.reply_text("❌ Invalid chat ID format! It should look like -1001234567890. Please try again.")
                logger.warning(f"⚠️ Invalid DB channel ID format provided by admin {user_id}: {text}")
                return
            set_setting("db_channel_id", text)
            update.message.reply_text(f"✅ Database channel ID set to: {text} 📂")
            logger.info(f"✅ Set DB channel ID to {text} by admin {user_id}")
        except Exception as e:
            update.message.reply_text(f"❌ Failed to set database channel ID: {str(e)}")
            logger.error(f"🚨 Failed to set DB channel ID by admin {user_id}: {str(e)}")
    elif input_type == "log_id":
        try:
            # Validate the chat ID format
            if not text.startswith("-100") or not text[1:].isdigit():
                update.message.reply_text("❌ Invalid chat ID format! It should look like -1000987654321. Please try again.")
                logger.warning(f"⚠️ Invalid log channel ID format provided by admin {user_id}: {text}")
                return
            set_setting("log_id", text)
            update.message.reply_text(f"✅ Log channel ID set to: {text} 📜")
            logger.info(f"✅ Set log channel ID to {text} by admin {user_id}")
        except Exception as e:
            update.message.reply_text(f"❌ Failed to set log channel ID: {str(e)}")
            logger.error(f"🚨 Failed to set log channel ID by admin {user_id}: {str(e)}")

    # Clear the awaiting input state
    del context.user_data["awaiting_input"]
    logger.info(f"✅ Cleared awaiting input state for admin {user_id}")
