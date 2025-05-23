import os
import logging
from datetime import datetime
from telegram import Bot

logger = logging.getLogger(__name__)

# Default values from environment variables
DEFAULT_DB_CHANNEL_ID = os.getenv("DB_CHANNEL_ID", None)
DEFAULT_LOG_ID = os.getenv("LOG_ID", None)

# Log the loaded environment variables for debugging
logger.info(f"ℹ️ Loaded DB_CHANNEL_ID from env: {DEFAULT_DB_CHANNEL_ID}")
logger.info(f"ℹ️ Loaded LOG_ID from env: {DEFAULT_LOG_ID}")

# Placeholder for the bot instance (set via utils.logging_utils)
log_bot = None

# Cached settings (loaded on demand)
SETTINGS = {
    "db_channel_id": DEFAULT_DB_CHANNEL_ID,
    "log_id": DEFAULT_LOG_ID
}

def set_db_bot(bot: Bot):
    """Set the bot instance for database operations."""
    global log_bot
    log_bot = bot
    logger.info("✅ Database bot instance set for utils/db_channel")

def get_setting(key: str) -> str:
    """Retrieve a setting from the database channel, falling back to environment variables."""
    global log_bot, SETTINGS
    if not log_bot:
        logger.error("🚨 Log bot not set in utils/db_channel")
        return SETTINGS.get(key, None)

    # If already cached, return the cached value
    if SETTINGS.get(key) and key in ["db_channel_id", "log_id"]:
        return SETTINGS[key]

    # Use db_channel_id to fetch settings (avoid circular dependency for db_channel_id itself)
    db_channel_id = SETTINGS["db_channel_id"] if key != "db_channel_id" else DEFAULT_DB_CHANNEL_ID
    if not db_channel_id:
        logger.warning(f"⚠️ DB_CHANNEL_ID not set for fetching setting {key}. Please set it via the admin settings menu.")
        return SETTINGS.get(key, None)

    # TODO: Implement a proper way to fetch settings from the database channel
    logger.warning(f"⚠️ Fetching settings from DB channel not implemented in this version. Returning default for {key}.")
    return SETTINGS.get(key, None)

def set_setting(key: str, value: str):
    """Save a setting to the database channel and update the cached value."""
    global log_bot, SETTINGS
    if not log_bot:
        logger.error("🚨 Log bot not set in utils/db_channel")
        raise ValueError("Log bot not set")

    db_channel_id = SETTINGS["db_channel_id"] if key != "db_channel_id" else DEFAULT_DB_CHANNEL_ID
    if not db_channel_id:
        error_msg = f"🚨 DB_CHANNEL_ID must be set to save settings. Please set it via the admin settings menu."
        logger.error(error_msg)
        from utils.logging_utils import log_error
        log_error(error_msg)
        raise ValueError(error_msg)

    try:
        setting_data = f"SETTING:{key}:{value}"
        log_bot.send_message(chat_id=db_channel_id, text=setting_data)
        logger.info(f"✅ Saved setting {key} = {value} to DB channel")
        SETTINGS[key] = value
        logger.info(f"✅ Updated cached setting {key} = {value}")
    except Exception as e:
        logger.error(f"🚨 Failed to save setting {key}: {str(e)}")
        raise

def get_cloned_bots():
    """Retrieve the list of cloned bots from the database channel."""
    global log_bot
    db_channel_id = get_setting("db_channel_id")
    if not log_bot:
        logger.error("🚨 Log bot not set in utils/db_channel")
        return []
    if not db_channel_id:
        logger.warning("⚠️ DB_CHANNEL_ID not set. Cloned bots cannot be loaded until set via the admin settings menu.")
        return []

    # TODO: Implement a proper way to fetch cloned bots (e.g., via updates or a file)
    logger.warning("⚠️ Fetching cloned bots not implemented in this version. Please upgrade python-telegram-bot or use an alternative storage method.")
    return []

def save_cloned_bot(owner_id: str, username: str, token: str, visibility: str, usage: str):
    """Save a cloned bot's details to the database channel and update the log channel."""
    global log_bot
    db_channel_id = get_setting("db_channel_id")
    log_id = get_setting("log_id")
    if not log_bot:
        logger.error("🚨 Log bot not set in utils/db_channel")
        raise ValueError("Log bot not set")
    if not db_channel_id:
        error_msg = "🚨 DB_CHANNEL_ID must be set to save cloned bots. Please set it via the admin settings menu."
        logger.error(error_msg)
        from utils.logging_utils import log_error
        log_error(error_msg)
        raise ValueError(error_msg)
    if not log_id:
        error_msg = "🚨 LOG_ID must be set to save cloned bots. Please set it via the admin settings menu."
        logger.error(error_msg)
        from utils.logging_utils import log_error
        log_error(error_msg)
        raise ValueError(error_msg)

    try:
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        bot_data = f"CLONED_BOT:{owner_id}|{username}|{token}|{visibility}|{usage}|{created_at}"
        log_bot.send_message(chat_id=db_channel_id, text=bot_data)
        logger.info(f"✅ Saved cloned bot @{username} to DB channel for owner {owner_id}")

        cloned_bots = get_cloned_bots()
        bots_by_owner = {}
        for bot in cloned_bots:
            owner = bot["owner_id"]
            if owner not in bots_by_owner:
                bots_by_owner[owner] = []
            bots_by_owner[owner].append(bot)

        table_msg = "📊 **Cloned Bots Table** 📊\n\n"
        table_msg += "| Username | Bots Cloned | Cloned Bots (with Mention) | Creation Date |\n"
        table_msg += "|----------|-------------|---------------------------|---------------|\n"
        for owner, bots in bots_by_owner.items():
            bot_usernames = ", ".join([f"@{bot['username']}" for bot in bots])
            creation_dates = ", ".join([bot["created_at"] for bot in bots])
            table_msg += f"| {owner} (ID: {owner}) | {len(bots)} | {bot_usernames} | {creation_dates} |\n"

        try:
            log_bot.send_message(chat_id=log_id, text=table_msg)
            logger.info(f"✅ Updated cloned bots table in log channel for owner {owner_id}")
        except Exception as e:
            logger.error(f"🚨 Failed to update cloned bots table in log channel: {str(e)}")
            raise

    except Exception as e:
        logger.error(f"🚨 Failed to save cloned bot @{username}: {str(e)}")
        raise
