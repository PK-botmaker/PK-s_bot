import os
import logging
import json
import requests
from telegram import Update, Bot
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
)
from handlers.admin import (
    start,
    clone_bot_menu,
    create_clone_bot,
    handle_clone_input,
    handle_visibility_selection,
    handle_usage_selection,
    view_clone_bots,
    delete_clone_bot,
    confirm_delete_bot,
    toggle_force_subscription,
    set_caption,
    handle_caption_input,
    broadcast,
    handle_broadcast_input,
    bot_stats,
    settings_menu,
    batch_menu,
    shortener_menu,
    set_shortener,
    tutorial,
    back_to_main,
    set_delete_timer,
    handle_delete_timer_input,
    forcesub_menu,
    add_forcesub_channel,
    handle_forcesub_input,
    about_cloned_bot,
)
from handlers.search import search, handle_group_message, handle_link_click, handle_button_click
from handlers.linkgen import upload, get_file, batch, genlink, batchgen
from handlers.redirect import redirect_handler
from handlers.error import error_handler
from utils.logging_utils import setup_logging

# Setup logging 📜
setup_logging()
logger = logging.getLogger(__name__)

# Paths 📂
CLONED_BOTS_PATH = "/opt/render/project/src/data/cloned_bots.json"
FILES_STORAGE_PATH = "/opt/render/project/src/data/files.json"
ADMINS_PATH = "/opt/render/project/src/data/admins.json"

# Initialize admins file 🔒
if not os.path.exists(ADMINS_PATH):
    with open(ADMINS_PATH, "w") as f:
        json.dump([], f)

def get_admins():
    """Load admin IDs from admins.json. 🔑"""
    try:
        with open(ADMINS_PATH, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"🚨 Failed to load admins: {str(e)}")
        return []

def save_admins(admins):
    """Save admin IDs to admins.json. 💾"""
    try:
        with open(ADMINS_PATH, "w") as f:
            json.dump(admins, f, indent=4)
    except Exception as e:
        logger.error(f"🚨 Failed to save admins: {str(e)}")

def get_cloned_bots():
    """Load cloned bots from cloned_bots.json. 🤖"""
    try:
        with open(CLONED_BOTS_PATH, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"🚨 Failed to load cloned bots: {str(e)}")
        return []

def save_cloned_bots(cloned_bots):
    """Save cloned bots to cloned_bots.json. 💾"""
    try:
        with open(CLONED_BOTS_PATH, "w") as f:
            json.dump(cloned_bots, f, indent=4)
    except Exception as e:
        logger.error(f"🚨 Failed to save cloned bots: {str(e)}")

def upload_to_gdtot(file_path: str, file_name: str) -> str:
    """Placeholder for uploading to GDToT. 📤"""
    GDTOT_API_KEY = os.getenv("GDTOT_API_KEY")
    if not GDTOT_API_KEY:
        logger.error("🚨 GDTOT_API_KEY not set in environment variables")
        return ""

    try:
        logger.info(f"ℹ️ Uploading {file_name} to GDToT 📦")
        gdtot_link = f"https://new.gdtot.com/file/{hash(file_name)}"
        return gdtot_link
    except Exception as e:
        logger.error(f"🚨 Failed to upload to GDToT: {str(e)}")
        return ""

async def start_cloned_bot(token: str, admin_ids: list, bot_type: str) -> bool:
    """Start a cloned bot with the given token and type. 🚀"""
    try:
        app = Application.builder().token(token).build()

        # Add common handlers 📲
        app.add_handler(CommandHandler("start", start))
        app.add_handler(MessageHandler(filters.ChatType.GROUP & ~filters.COMMAND, handle_group_message))
        app.add_handler(MessageHandler(filters.ChatType.SUPERGROUP & ~filters.COMMAND, handle_group_message))
        app.add_handler(CallbackQueryHandler(handle_link_click, pattern="^download_"))
        app.add_handler(CallbackQueryHandler(handle_button_click, pattern="^(download_|how_to_download|back_to_download)"))
        app.add_handler(CallbackQueryHandler(about_cloned_bot, pattern="^about_cloned_bot$"))

        # Add type-specific handlers 🛠️
        if bot_type == "searchbot":
            app.add_handler(CommandHandler("search", search))
        elif bot_type == "filestorebot":
            app.add_handler(CommandHandler("upload", upload))
            app.add_handler(CommandHandler("get", get_file))
            app.add_handler(CommandHandler("batch", batch))
            app.add_handler(CommandHandler("genlink", genlink))
            app.add_handler(CommandHandler("batchgen", batchgen))

        app.run_polling(allowed_updates=Update.ALL_TYPES)
        logger.info(f"✅ Cloned bot with token ending {token[-4:]} started successfully as {bot_type} 🎉")
        return True
    except Exception as e:
        logger.error(f"🚨 Failed to start cloned bot with token ending {token[-4:]}: {str(e)}")
        return False

def pre_upload_files():
    """Pre-upload files to GDToT during bot startup. 📤"""
    files = []
    try:
        with open(FILES_STORAGE_PATH, "r") as f:
            files = json.load(f)
    except Exception as e:
        logger.error(f"🚨 Failed to load files for pre-upload: {str(e)}")
        return

    for file in files:
        if "gdtot_link" not in file:
            file_path = file.get("path")
            file_name = file.get("filename")
            gdtot_link = upload_to_gdtot(file_path, file_name)
            if gdtot_link:
                file["gdtot_link"] = gdtot_link
                logger.info(f"✅ Pre-uploaded {file_name} to GDToT: {gdtot_link} 🎉")

    try:
        with open(FILES_STORAGE_PATH, "w") as f:
            json.dump(files, f, indent=4)
    except Exception as e:
        logger.error(f"🚨 Failed to save pre-uploaded files: {str(e)}")

def main():
    """Main function to start the bot. 🚀"""
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    RENDER_EXTERNAL_HOSTNAME = os.getenv("RENDER_EXTERNAL_HOSTNAME")

    if not TELEGRAM_BOT_TOKEN:
        logger.error("🚨 TELEGRAM_BOT_TOKEN not set in environment variables")
        return

    if not RENDER_EXTERNAL_HOSTNAME:
        logger.error("🚨 RENDER_EXTERNAL_HOSTNAME not set in environment variables")
        return

    pre_upload_files()

    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Load or initialize admins 🔑
    admins = get_admins()
    app.bot_data["admin_ids"] = admins

    # Add handlers 📲
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(clone_bot_menu, pattern="^clone_bot_menu$"))
    app.add_handler(CallbackQueryHandler(create_clone_bot, pattern="^create_clone_bot$"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & filters.Regex(r"^\d+:\d+"), handle_clone_input))
    app.add_handler(CallbackQueryHandler(handle_visibility_selection, pattern="^(visibility_private|visibility_public|cancel_clone)$"))
    app.add_handler(CallbackQueryHandler(handle_usage_selection, pattern="^(usage_searchbot|usage_filestorebot)$"))
    app.add_handler(CallbackQueryHandler(view_clone_bots, pattern="^view_clone_bots$"))
    app.add_handler(CallbackQueryHandler(delete_clone_bot, pattern="^delete_clone_bot_"))
    app.add_handler(CallbackQueryHandler(confirm_delete_bot, pattern="^(confirm_delete_bot_|cancel_delete)$"))
    app.add_handler(CallbackQueryHandler(toggle_force_subscription, pattern="^toggle_force_subscription$"))
    app.add_handler(CallbackQueryHandler(set_caption, pattern="^set_caption$"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_caption_input))
    app.add_handler(CallbackQueryHandler(broadcast, pattern="^broadcast$"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_broadcast_input))
    app.add_handler(CallbackQueryHandler(bot_stats, pattern="^bot_stats$"))
    app.add_handler(CallbackQueryHandler(settings_menu, pattern="^settings_menu$"))
    app.add_handler(CallbackQueryHandler(batch_menu, pattern="^batch_menu$"))
    app.add_handler(CallbackQueryHandler(shortener_menu, pattern="^shortener_menu$"))
    app.add_handler(CallbackQueryHandler(set_shortener, pattern="^set_shortener_"))
    app.add_handler(CallbackQueryHandler(tutorial, pattern="^tutorial$"))
    app.add_handler(CallbackQueryHandler(back_to_main, pattern="^back_to_main$"))
    app.add_handler(CallbackQueryHandler(set_delete_timer, pattern="^set_delete_timer$"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_delete_timer_input))
    app.add_handler(CallbackQueryHandler(forcesub_menu, pattern="^forcesub_menu$"))
    app.add_handler(CallbackQueryHandler(add_forcesub_channel, pattern="^add_forcesub_channel_"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_forcesub_input))
    app.add_handler(CallbackQueryHandler(about_cloned_bot, pattern="^about_cloned_bot$"))
    app.add_handler(CommandHandler("search", search))
    app.add_handler(MessageHandler(filters.ChatType.GROUP & ~filters.COMMAND, handle_group_message))
    app.add_handler(MessageHandler(filters.ChatType.SUPERGROUP & ~filters.COMMAND, handle_group_message))
    app.add_handler(CallbackQueryHandler(handle_link_click, pattern="^download_"))
    app.add_handler(CallbackQueryHandler(handle_button_click, pattern="^(download_|how_to_download|back_to_download)"))
    app.add_handler(CommandHandler("upload", upload))
    app.add_handler(CommandHandler("get", get_file))
    app.add_handler(CommandHandler("batch", batch))
    app.add_handler(CommandHandler("genlink", genlink))
    app.add_handler(CommandHandler("batchgen", batchgen))
    app.add_error_handler(error_handler)

    # Start cloned bots 🤖
    cloned_bots = get_cloned_bots()
    for bot in cloned_bots:
        token = bot.get("token")
        bot_type = bot.get("type", "searchbot")
        if token:
            success = start_cloned_bot(token, admins, bot_type)
            if not success:
                logger.error(f"🚨 Failed to start cloned bot with token ending {token[-4:]}")

    webhook_url = f"https://{RENDER_EXTERNAL_HOSTNAME}/webhook"
    app.run_webhook(
        listen="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        url_path="/webhook",
        webhook_url=webhook_url
    )
    logger.info("✅ Bot started successfully 🎉")

if __name__ == "__main__":
    main()