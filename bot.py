import os
import logging
from telegram.ext import Updater, CommandHandler, MessageHandler, CallbackQueryHandler, Filters, Dispatcher
from telegram import Bot, Update as TelegramUpdate
from handlers.start import start, settings_menu, batch_menu, bot_stats, shortener_menu
from handlers.file_handler import handle_file
from handlers.clone_bot import create_clone_bot, view_clone_bots, handle_clone_input, handle_visibility_selection, handle_usage_selection
from handlers.custom_caption import set_custom_caption, set_custom_buttons, handle_caption_input, handle_buttons_input
from handlers.error import error_handler
from handlers.search import search
from handlers.request import handle_request
from handlers.tutorial import tutorial
from handlers.settings import handle_settings, handle_settings_input
from handlers.broadcast import broadcast, handle_broadcast_input, cancel_broadcast
from handlers.batch import batch, handle_batch_input, handle_batch_edit, cancel_batch
from handlers.filestore import store_file, genlink, batchgen, handle_genlink_selection, handle_batchgen_selection, handle_filestore_link
from werkzeug.wrappers import Request, Response
import json

# 🌟 Logging setup for Render
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Global dictionary to map tokens to their respective bots and dispatchers
bot_registry = {}

# Main updater and dispatcher (shared across all bots)
main_updater = None
main_dispatcher = None

# Flag to ensure setup() is called only once
_setup_completed = False

def start_cloned_bot(token, admin_ids):
    """🤖 Register a cloned bot's handlers on the main dispatcher with visibility restrictions."""
    global main_dispatcher
    try:
        # Fetch cloned bots to get visibility and standalone status
        from utils.db_channel import get_cloned_bots
        cloned_bots = get_cloned_bots()
        bot_info = next((bot for bot in cloned_bots if bot["token"] == token), None)
        if not bot_info:
            raise ValueError("Bot not found in cloned_bots")

        # Skip if the bot is marked as standalone
        if bot_info.get("standalone", False):
            logger.info(f"ℹ️ Skipped registering cloned bot with token ending {token[-4:]} - marked as standalone! 🤖")
            return None

        visibility = bot_info.get("visibility", "public")
        usage = bot_info.get("usage", "searchbot")  # Default to searchbot if not set
        owner_id = bot_info.get("owner_id", None)

        # Create a Bot instance for this cloned bot
        bot = Bot(token)
        bot_info = bot.get_me()
        bot_username = bot_info.username
        logger.info(f"ℹ️ Registering cloned bot @{bot_username} with token ending {token[-4:]} (visibility: {visibility}, usage: {usage})")

        # Store the bot in the registry
        bot_registry[token] = {
            "bot": bot,
            "context_data": {"admin_ids": admin_ids, "is_main_bot": False, "visibility": visibility, "owner_id": owner_id}
        }

        # Access restriction for private bots
        def restrict_access(handler_func):
            def wrapper(update: TelegramUpdate, context):
                user_id = str(update.effective_user.id)
                if context.bot_data.get("visibility") == "private" and user_id != context.bot_data.get("owner_id"):
                    update.message.reply_text("🚫 This bot is private! Only the owner can use it! 🔒")
                    logger.info(f"🚫 User {user_id} denied access to private bot with token ending {token[-4:]}")
                    return
                return handler_func(update, context)
            return wrapper

        # Create a group for this bot's handlers to avoid conflicts
        group = len(bot_registry)  # Unique group number for each bot
        logger.info(f"ℹ️ Assigning handler group {group} for bot @{bot_username}")

        # Handlers based on usage type
        main_dispatcher.add_handler(CommandHandler("start", restrict_access(start), filters=Filters.chat_type.private), group=group)
        if usage == "searchbot":
            main_dispatcher.add_handler(CommandHandler("search", restrict_access(search), filters=Filters.chat_type.private), group=group)
            main_dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, restrict_access(handle_request)), group=group)
            main_dispatcher.add_handler(CommandHandler("start", handle_request, pass_args=True, filters=Filters.chat_type.private), group=group)
            logger.info(f"✅ Added searchbot handlers for bot @{bot_username}")
        elif usage == "filestore":
            main_dispatcher.add_handler(MessageHandler(Filters.document | Filters.photo | Filters.video | Filters.audio, restrict_access(store_file)), group=group)
            main_dispatcher.add_handler(CommandHandler("genlink", restrict_access(genlink), filters=Filters.chat_type.private), group=group)
            main_dispatcher.add_handler(CommandHandler("batchgen", restrict_access(batchgen), filters=Filters.chat_type.private), group=group)
            main_dispatcher.add_handler(CallbackQueryHandler(handle_genlink_selection, pattern="^(genlink_|cancel_genlink)"), group=group)
            main_dispatcher.add_handler(CallbackQueryHandler(handle_batchgen_selection, pattern="^(batch_select_|batch_done|cancel_batchgen)"), group=group)
            main_dispatcher.add_handler(CommandHandler("start", handle_filestore_link, pass_args=True, filters=Filters.chat_type.private), group=group)
            logger.info(f"✅ Added filestore handlers for bot @{bot_username}")

        # Add error handler for this bot
        main_dispatcher.add_error_handler(error_handler)
        logger.info(f"✅ Added error handler for bot @{bot_username}")

        # Set webhook for the cloned bot
        RENDER_EXTERNAL_HOSTNAME = os.getenv("RENDER_EXTERNAL_HOSTNAME")
        if not RENDER_EXTERNAL_HOSTNAME:
            raise ValueError("RENDER_EXTERNAL_HOSTNAME not set")
        webhook_url = f"https://{RENDER_EXTERNAL_HOSTNAME}/webhook/{token}"
        try:
            bot.set_webhook(url=webhook_url)
            logger.info(f"✅ Set webhook for bot @{bot_username}: {webhook_url}")
        except Exception as e:
            logger.warning(f"⚠️ Failed to set webhook for cloned bot @{bot_username}: {str(e)}")

        logger.info(f"✅ Successfully registered cloned bot @{bot_username} with token ending {token[-4:]} and visibility {visibility} and usage {usage}! 🤖")
        return True  # Indicate success
    except Exception as e:
        error_msg = f"🚨 Failed to register cloned bot with token ending {token[-4:]}: {str(e)}"
        logger.error(error_msg)
        from utils.logging_utils import log_error
        log_error(error_msg)
        return None

def webhook_handler(environ, start_response):
    """Handle incoming webhook requests and route them to the appropriate bot."""
    global bot_registry, main_updater, main_dispatcher

    # Create a Request object from the WSGI environ
    request = Request(environ)

    # Extract the token from the URL path (e.g., /webhook/{token})
    path = request.path
    if not path.startswith("/webhook/"):
        response = Response("Invalid webhook path", status=400)
        return response(environ, start_response)

    token = path[len("/webhook/"):]
    if token not in bot_registry:
        logger.warning(f"⚠️ Received webhook request for unknown token: {token}")
        response = Response("Unknown bot token", status=404)
        return response(environ, start_response)

    bot_info = bot_registry[token]
    bot = bot_info["bot"]
    context_data = bot_info["context_data"]

    if request.method == "POST":
        try:
            update_data = request.get_json()
            if not update_data:
                logger.warning(f"⚠️ Empty update received for token ending {token[-4:]}")
                response = Response("Empty update", status=400)
                return response(environ, start_response)

            # Create an Update object
            update = TelegramUpdate.de_json(update_data, bot)
            if not update:
                logger.warning(f"⚠️ Invalid update received for token ending {token[-4:]}")
                response = Response("Invalid update", status=400)
                return response(environ, start_response)

            # Update the bot instance in the dispatcher
            main_dispatcher.bot = bot
            main_dispatcher.bot_data.clear()
            main_dispatcher.bot_data.update(context_data)

            # Process the update using the main dispatcher
            main_dispatcher.process_update(update)
            logger.info(f"✅ Processed update for bot with token ending {token[-4:]}")
            response = Response("OK", status=200)
            return response(environ, start_response)

        except Exception as e:
            logger.error(f"🚨 Error processing webhook update for token ending {token[-4:]}: {str(e)}")
            response = Response("Error processing update", status=500)
            return response(environ, start_response)

    response = Response("Method not allowed", status=405)
    return response(environ, start_response)

def setup():
    """🚀 Initialize the bot with cloned bots and custom captions/buttons."""
    global main_updater, main_dispatcher, bot_registry, _setup_completed

    # Prevent multiple setup calls
    if _setup_completed:
        logger.info("ℹ️ Setup already completed, skipping redundant call.")
        return

    logger.info("ℹ️ Starting setup process...")

    # 🔑 Load static env vars
    TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
    ADMIN_IDS = os.getenv("ADMIN_IDS")
    RENDER_EXTERNAL_HOSTNAME = os.getenv("RENDER_EXTERNAL_HOSTNAME")
    PORT = os.getenv("PORT", "10000")

    logger.info(f"ℹ️ Loaded environment variables:")
    logger.info(f"ℹ️ TELEGRAM_TOKEN: {'Set' if TELEGRAM_TOKEN else 'Not set'}")
    logger.info(f"ℹ️ ADMIN_IDS: {ADMIN_IDS}")
    logger.info(f"ℹ️ RENDER_EXTERNAL_HOSTNAME: {RENDER_EXTERNAL_HOSTNAME}")
    logger.info(f"ℹ️ PORT: {PORT}")

    if not TELEGRAM_TOKEN or not ADMIN_IDS:
        error_msg = "🚨 Missing TELEGRAM_TOKEN or ADMIN_IDS"
        logger.error(error_msg)
        from utils.logging_utils import log_error
        log_error(error_msg)
        raise ValueError(error_msg)

    if not RENDER_EXTERNAL_HOSTNAME:
        error_msg = "🚨 Missing RENDER_EXTERNAL_HOSTNAME"
        logger.error(error_msg)
        from utils.logging_utils import log_error
        log_error(error_msg)
        raise ValueError(error_msg)

    logger.info("ℹ️ Environment variables validated successfully.")

    try:
        admin_ids = [str(id.strip()) for id in ADMIN_IDS.split(",")]
        logger.info(f"✅ Loaded admin IDs: {admin_ids}")
    except ValueError:
        error_msg = "🚨 Invalid ADMIN_IDS format"
        logger.error(error_msg)
        from utils.logging_utils import log_error
        log_error(error_msg)
        raise ValueError(error_msg)

    context_data = {"admin_ids": admin_ids, "is_main_bot": True}

    # 🤖 Initialize main bot
    try:
        logger.info("ℹ️ Initializing main bot...")
        main_updater = Updater(TELEGRAM_TOKEN, use_context=True)
        main_dispatcher = main_updater.dispatcher
        main_dispatcher.bot_data.update(context_data)
        bot_username = main_updater.bot.get_me().username
        logger.info(f"✅ Main bot initialized! 🎉 Bot username: @{bot_username}")
        from utils.logging_utils import set_log_bot
        set_log_bot(Bot(TELEGRAM_TOKEN))
    except Exception as e:
        error_msg = f"🚨 Failed to initialize main bot: {str(e)}"
        logger.error(error_msg)
        from utils.logging_utils import log_error
        log_error(error_msg)
        raise

    # Register the main bot in the registry
    bot_registry[TELEGRAM_TOKEN] = {
        "bot": main_updater.bot,
        "context_data": context_data
    }

    logger.info("ℹ️ Main bot registered in bot_registry.")

    # 📡 Add handlers for main bot (full admin features)
    main_dispatcher.add_handler(CommandHandler("start", start, filters=Filters.chat_type.private), group=0)
    main_dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_clone_input), group=0)
    main_dispatcher.add_handler(CommandHandler("search", search, filters=Filters.chat_type.private), group=0)
    main_dispatcher.add_handler(MessageHandler(Filters.document | Filters.photo | Filters.video | Filters.audio, handle_file), group=0)
    main_dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_caption_input), group=0)
    main_dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_buttons_input), group=0)
    main_dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_request), group=0)
    main_dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_broadcast_input), group=0)
    main_dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_batch_input), group=0)
    main_dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_settings_input), group=0)
    main_dispatcher.add_handler(CallbackQueryHandler(create_clone_bot, pattern="^create_clone_bot$"), group=0)
    main_dispatcher.add_handler(CallbackQueryHandler(view_clone_bots, pattern="^view_clone_bots$"), group=0)
    main_dispatcher.add_handler(CallbackQueryHandler(handle_visibility_selection, pattern="^(visibility_private|visibility_public|cancel_clone)$"), group=0)
    main_dispatcher.add_handler(CallbackQueryHandler(handle_usage_selection, pattern="^(usage_filestore|usage_searchbot|cancel_clone)$"), group=0)
    main_dispatcher.add_handler(CallbackQueryHandler(set_custom_caption, pattern="^set_custom_caption$"), group=0)
    main_dispatcher.add_handler(CallbackQueryHandler(set_custom_buttons, pattern="^set_custom_buttons$"), group=0)
    main_dispatcher.add_handler(CallbackQueryHandler(tutorial, pattern="^tutorial$"), group=0)
    main_dispatcher.add_handler(CallbackQueryHandler(settings_menu, pattern="^settings$"), group=0)
    main_dispatcher.add_handler(CallbackQueryHandler(shortener_menu, pattern="^shortener$"), group=0)
    main_dispatcher.add_handler(CallbackQueryHandler(batch_menu, pattern="^batch_menu$"), group=0)
    main_dispatcher.add_handler(CallbackQueryHandler(bot_stats, pattern="^bot_stats$"), group=0)
    main_dispatcher.add_handler(CallbackQueryHandler(handle_settings, pattern="^(add_channel|remove_channel|set_force_sub|set_group_link|set_db_channel|set_log_channel|shortener|set_shortener_api|set_shortener_key|disable_shortener|welcome_message|auto_delete|banner|set_webhook|anti_ban|enable_redis)$"), group=0)
    main_dispatcher.add_handler(CallbackQueryHandler(broadcast, pattern="^broadcast$"), group=0)
    main_dispatcher.add_handler(CallbackQueryHandler(cancel_broadcast, pattern="^cancel_broadcast$"), group=0)
    main_dispatcher.add_handler(CallbackQueryHandler(batch, pattern="^(generate_batch|edit_batch)$"), group=0)
    main_dispatcher.add_handler(CallbackQueryHandler(handle_batch_edit, pattern="^edit_batch_"), group=0)
    main_dispatcher.add_handler(CallbackQueryHandler(cancel_batch, pattern="^cancel_batch$"), group=0)
    main_dispatcher.add_handler(MessageHandler(Filters.document | Filters.photo | Filters.video | Filters.audio, store_file), group=0)
    main_dispatcher.add_handler(CommandHandler("genlink", genlink, filters=Filters.chat_type.private), group=0)
    main_dispatcher.add_handler(CommandHandler("batchgen", batchgen, filters=Filters.chat_type.private), group=0)
    main_dispatcher.add_handler(CallbackQueryHandler(handle_genlink_selection, pattern="^(genlink_|cancel_genlink)"), group=0)
    main_dispatcher.add_handler(CallbackQueryHandler(handle_batchgen_selection, pattern="^(batch_select_|batch_done|cancel_batchgen)"), group=0)
    main_dispatcher.add_handler(CommandHandler("start", handle_filestore_link, pass_args=True, filters=Filters.chat_type.private), group=0)

    # Add error handler for the main dispatcher
    main_dispatcher.add_error_handler(error_handler)

    logger.info("ℹ️ Handlers added for main bot.")

    # 🗄️ Load cloned bots from DB channel
    try:
        logger.info("ℹ️ Loading cloned bots...")
        from utils.db_channel import get_cloned_bots
        cloned_bots = get_cloned_bots()
        logger.info(f"✅ Loaded {len(cloned_bots)} cloned bots! 🌟")
        for bot in cloned_bots:
            logger.info(f"ℹ️ Cloned bot: token ending {bot['token'][-4:]} | Visibility: {bot['visibility']} | Usage: {bot['usage']} | Standalone: {bot.get('standalone', False)}")
    except Exception as e:
        error_msg = f"🚨 Failed to load cloned bots: {str(e)}"
        logger.error(error_msg)
        from utils.logging_utils import log_error
        log_error(error_msg)
        cloned_bots = []
        logger.info("ℹ️ Continuing bot setup despite failure to load cloned bots.")

    # Register cloned bots initially
    logger.info("ℹ️ Registering cloned bots...")
    for bot in cloned_bots:
        success = start_cloned_bot(bot["token"], admin_ids)
        if success:
            logger.info(f"✅ Successfully registered cloned bot with token ending {bot['token'][-4:]}")
        else:
            logger.error(f"⚠️ Failed to register cloned bot with token ending {bot['token'][-4:]}")

    # 🌍 Set webhook for all bots in the registry
    try:
        logger.info("ℹ️ Setting up webhooks...")
        try:
            main_updater.bot.delete_webhook()
            logger.info(f"✅ Deleted existing webhook for main bot @{bot_username}")
        except Exception as e:
            logger.warning(f"⚠️ Failed to delete existing webhook for main bot: {str(e)}. Continuing...")

        for token in bot_registry:
            bot_info = bot_registry[token]
            bot = bot_info["bot"]
            webhook_url = f"https://{RENDER_EXTERNAL_HOSTNAME}/webhook/{token}"
            try:
                bot.set_webhook(url=webhook_url)
                logger.info(f"✅ Set webhook for bot with token ending {token[-4:]}: {webhook_url}")
            except Exception as e:
                logger.warning(f"⚠️ Failed to set webhook for bot with token ending {token[-4:]}: {str(e)}. Bot may not receive updates.")
    except Exception as e:
        error_msg = f"🚨 Critical failure during webhook setup: {str(e)}. Bot may not respond to updates."
        logger.error(error_msg)
        from utils.logging_utils import log_error
        log_error(error_msg)
        logger.info("ℹ️ Continuing setup despite webhook setup failure.")

    logger.info(f"✅ Setup completed, Gunicorn should now bind to port {PORT}")
    _setup_completed = True  # Mark setup as completed

# Expose the WSGI application for Gunicorn
application = webhook_handler

if __name__ == "__main__":
    # Fallback for local testing (optional, not used on Render)
    import os
    if os.getenv("RENDER_EXTERNAL_HOSTNAME") is None:
        from werkzeug.serving import run_simple
        logger.warning("⚠️ Running in local development mode with Werkzeug server. Do not use this in production!")
        setup()
        run_simple("0.0.0.0", 8443, webhook_handler, use_reloader=False, use_debugger=False)
    else:
        logger.info("ℹ️ Running on Render, Gunicorn should handle the server. Skipping direct execution.")
