import os
import logging
import json
import telegram  # Add this to check the version
print(f"python-telegram-bot version: {telegram.__version__}")  # Debug statement
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    CallbackContext,
)
from handlers.search import search, handle_link_click, handle_button_click, handle_group_message
from handlers.linkgen import upload, get_file, batch, genlink, batchgen
from handlers.redirect import redirect_handler
from handlers.error import error_handler
from handlers.admin_activity import stats, logs, broadcast, users
from handlers.admin_management import clone, settings_menu, settings_callback, handle_channel_input  # Add imports for admin_management
from utils.logging_utils import setup_logging

logger = logging.getLogger(__name__)

SETTINGS_PATH = "/opt/render/project/src/data/settings.json"

def load_settings():
    """Load bot settings from settings.json. ⚙️"""
    try:
        with open(SETTINGS_PATH, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"🚨 Failed to load settings: {str(e)}")
        return {"force_subscription": False, "search_caption": "🔍 Search Result", "delete_timer": "0m", "forcesub_channels": ["@bot_paiyan_official"]}

def save_settings(settings):
    """Save bot settings to settings.json. 💾"""
    try:
        with open(SETTINGS_PATH, "w") as f:
            json.dump(settings, f, indent=4)
    except Exception as e:
        logger.error(f"🚨 Failed to save settings: {str(e)}")

def load_users():
    """Load user IDs from users.json. 👥"""
    try:
        with open("/opt/render/project/src/data/users.json", "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"🚨 Failed to load users: {str(e)}")
        return []

def save_users(users):
    """Save user IDs to users.json. 💾"""
    try:
        with open("/opt/render/project/src/data/users.json", "w") as f:
            json.dump(users, f, indent=4)
    except Exception as e:
        logger.error(f"🚨 Failed to save users: {str(e)}")

async def start(update: Update, context: CallbackContext):
    """Handle the /start command and set the first user as admin. 🚀"""
    user_id = str(update.effective_user.id)
    username = update.effective_user.username or "Unknown"
    users = load_users()
    settings = load_settings()

    # Set the first user as admin 🔑
    if not settings.get("admin_id") and not users:
        settings["admin_id"] = user_id
        save_settings(settings)
        logger.info(f"ℹ️ User {user_id} set as admin")

    # Add user to users.json if not already present 👥
    if user_id not in users:
        users.append(user_id)
        save_users(users)
        logger.info(f"ℹ️ New user added: {user_id}")

    # Prepare welcome message with buttons 🎉
    keyboard = [
        [InlineKeyboardButton("🔍 Search Files", callback_data="search_info")],
        [InlineKeyboardButton("ℹ️ About Bot", callback_data="about_bot")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    welcome_message = (
        "🎉 **Welcome to TamilSender Bot!** 🎉\n\n"
        "🔍 Use /search to find files\n"
        "📤 Use /upload to upload files\n"
        "📁 Use /get to retrieve a file by ID\n"
        "📦 Use /batch to get a range of files\n"
        "🔗 Use /genlink to generate a link\n"
        "📢 Use /batchgen for batch links\n\n"
        "👇 **Choose an option below** 👇"
    )
    await update.message.reply_text(welcome_message, reply_markup=reply_markup, parse_mode="Markdown")

async def button_callback(update: Update, context: CallbackContext):
    """Handle button callbacks in the /start command. 🔄"""
    query = update.callback_query
    await query.answer()
    user_id = str(query.from_user.id)
    username = query.from_user.username or "Unknown"

    if query.data == "search_info":
        await query.message.edit_text(
            "🔍 **Search Files** 🔍\n\n"
            "Use /search followed by a keyword to find files.\n"
            "Example: /search Avengers 😅\n\n"
            "Or type your query directly in a group chat! 💬",
            parse_mode="Markdown"
        )
    elif query.data == "about_bot":
        settings = load_settings()
        creation_date = settings.get("creation_date", "2025-05-01")
        about_message = (
            "ℹ️ **About TamilSender Bot** ℹ️\n\n"
            "👤 **Owner**: @Dhileep_S\n"
            "🤖 **Developer**: @Dhileep_S\n"
            "📜 **Cloned From**: @tamilsender_bot\n"
            "🌐 **Language**: Tamil\n"
            "📌 **Bot Type**: File Sharing\n"
            "🔒 **Visibility**: Public\n"
            f"🕒 **Created On**: {creation_date}"
        )
        await query.message.edit_text(about_message, parse_mode="Markdown")

def main():
    """Start the bot. 🚀"""
    setup_logging()
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    if not TELEGRAM_BOT_TOKEN:
        logger.error("🚨 TELEGRAM_BOT_TOKEN not set in environment variables")
        return

    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("search", search))
    application.add_handler(CommandHandler("upload", upload))
    application.add_handler(CommandHandler("get", get_file))
    application.add_handler(CommandHandler("batch", batch))
    application.add_handler(CommandHandler("genlink", genlink))
    application.add_handler(CommandHandler("batchgen", batchgen))
    application.add_handler(CommandHandler("stats", stats))
    application.add_handler(CommandHandler("logs", logs))
    application.add_handler(CommandHandler("broadcast", broadcast))
    application.add_handler(CommandHandler("users", users))
    application.add_handler(CommandHandler("clone", clone))  # Add clone handler
    application.add_handler(CommandHandler("settings", settings_menu))  # Add settings handler

    # Message and callback handlers
    application.add_handler(MessageHandler(filters.TEXT & (filters.ChatType.GROUPS | filters.ChatType.SUPERGROUP), handle_group_message))
    application.add_handler(MessageHandler(filters.TEXT & filters.ChatType.PRIVATE, handle_channel_input))  # Add handler for channel input
    application.add_handler(CallbackQueryHandler(handle_link_click, pattern="^download_"))
    application.add_handler(CallbackQueryHandler(handle_button_click, pattern="^(how_to_download|back_to_download)$"))
    application.add_handler(CallbackQueryHandler(settings_callback, pattern="^(toggle_force_sub|set_delete_timer|set_timer_|manage_force_sub_channels|add_force_sub_channel|remove_force_sub_channel|set_shortener_|back_to_settings|back_to_main)$"))  # Add settings callback handler
    application.add_handler(CallbackQueryHandler(button_callback))

    # Error handler
    application.add_error_handler(error_handler)

    logger.info("✅ Bot started successfully")
    application.run_polling()

if __name__ == "__main__":
    main()
