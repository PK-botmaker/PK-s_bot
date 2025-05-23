# ... (previous imports and code remain the same)

def setup():
    """🚀 Initialize the bot with cloned bots and custom captions/buttons."""
    global main_updater, main_dispatcher, bot_registry

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

    # 📡 Add handlers for main bot (full admin features)
    # ... (handlers remain the same)

    # 🗄️ Load cloned bots from DB channel
    try:
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
    for bot in cloned_bots:
        success = start_cloned_bot(bot["token"], admin_ids)
        if success:
            logger.info(f"✅ Successfully registered cloned bot with token ending {bot['token'][-4:]}")
        else:
            logger.error(f"⚠️ Failed to register cloned bot with token ending {bot['token'][-4:]}")

    # 🌍 Set webhook for all bots in the registry
    try:
        main_updater.bot.delete_webhook()
        logger.info(f"✅ Deleted existing webhook for main bot @{bot_username}")

        for token in bot_registry:
            bot_info = bot_registry[token]
            bot = bot_info["bot"]
            webhook_url = f"https://{RENDER_EXTERNAL_HOSTNAME}/webhook/{token}"
            bot.set_webhook(url=webhook_url)
            logger.info(f"✅ Set webhook for bot with token ending {token[-4:]}: {webhook_url}")
    except Exception as e:
        error_msg = f"🚨 Failed to set webhooks: {str(e)}"
        logger.error(error_msg)
        from utils.logging_utils import log_error
        log_error(error_msg)
        raise

    logger.info(f"✅ Setup completed, Gunicorn should now bind to port {PORT}")

# ... (rest of the code remains the same)
