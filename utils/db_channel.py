import os
import logging
from datetime import datetime
from telegram import Bot

logger = logging.getLogger(__name__)

# Placeholder for the database channel ID (should be set via env or settings)
DB_CHANNEL_ID = os.getenv("DB_CHANNEL_ID", None)  # e.g., "-1001234567890"
LOG_ID = os.getenv("LOG_ID", None)  # e.g., "-1000987654321"

# Placeholder for the bot instance (set via utils.logging_utils)
log_bot = None

def set_db_bot(bot: Bot):
    """Set the bot instance for database operations."""
    global log_bot
    log_bot = bot
    logger.info("✅ Database bot instance set for utils/db_channel")

def get_cloned_bots():
    """Retrieve the list of cloned bots from the database channel."""
    global log_bot, DB_CHANNEL_ID
    if not log_bot:
        logger.error("🚨 Log bot not set in utils/db_channel")
        return []
    if not DB_CHANNEL_ID:
        logger.error("🚨 DB_CHANNEL_ID not set")
        return []

    try:
        # Fetch messages from the database channel
        messages = []
        # Telegram API limits fetching messages, so we might need to paginate in a real setup
        # For simplicity, assume we fetch recent messages (up to 100)
        chat_messages = log_bot.get_chat_history(chat_id=DB_CHANNEL_ID, limit=100)
        for message in chat_messages:
            if message.text and message.text.startswith("CLONED_BOT:"):
                # Parse the message text (format: "CLONED_BOT:owner_id|username|token|visibility|usage|created_at")
                try:
                    data = message.text.split("CLONED_BOT:")[1].split("|")
                    if len(data) != 6:
                        continue
                    bot_data = {
                        "owner_id": data[0],
                        "username": data[1],
                        "token": data[2],
                        "visibility": data[3],
                        "usage": data[4],
                        "created_at": data[5]
                    }
                    messages.append(bot_data)
                except Exception as e:
                    logger.error(f"🚨 Error parsing cloned bot message: {str(e)}")
                    continue
        logger.info(f"✅ Retrieved {len(messages)} cloned bots from DB channel")
        return messages
    except Exception as e:
        logger.error(f"🚨 Failed to retrieve cloned bots: {str(e)}")
        return []

def save_cloned_bot(owner_id: str, username: str, token: str, visibility: str, usage: str):
    """Save a cloned bot's details to the database channel and update the log channel."""
    global log_bot, DB_CHANNEL_ID, LOG_ID
    if not log_bot:
        logger.error("🚨 Log bot not set in utils/db_channel")
        raise ValueError("Log bot not set")
    if not DB_CHANNEL_ID:
        logger.error("🚨 DB_CHANNEL_ID not set")
        raise ValueError("DB_CHANNEL_ID not set")
    if not LOG_ID:
        logger.error("🚨 LOG_ID not set")
        raise ValueError("LOG_ID not set")

    try:
        # Format the bot data as a message
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        bot_data = f"CLONED_BOT:{owner_id}|{username}|{token}|{visibility}|{usage}|{created_at}"
        
        # Save the bot data to the database channel
        log_bot.send_message(chat_id=DB_CHANNEL_ID, text=bot_data)
        logger.info(f"✅ Saved cloned bot @{username} to DB channel for owner {owner_id}")

        # Fetch all cloned bots to update the table
        cloned_bots = get_cloned_bots()
        
        # Group bots by owner for the table
        bots_by_owner = {}
        for bot in cloned_bots:
            owner = bot["owner_id"]
            if owner not in bots_by_owner:
                bots_by_owner[owner] = []
            bots_by_owner[owner].append(bot)

        # Build the table message
        table_msg = "📊 **Cloned Bots Table** 📊\n\n"
        table_msg += "| Username | Bots Cloned | Cloned Bots (with Mention) | Creation Date |\n"
        table_msg += "|----------|-------------|---------------------------|---------------|\n"
        for owner, bots in bots_by_owner.items():
            bot_usernames = ", ".join([f"@{bot['username']}" for bot in bots])
            creation_dates = ", ".join([bot["created_at"] for bot in bots])
            table_msg += f"| {owner} (ID: {owner}) | {len(bots)} | {bot_usernames} | {creation_dates} |\n"

        # Send or update the table in the log channel
        try:
            # For simplicity, we send a new message each time
            # In a real setup, you might want to edit an existing message (requires storing the message ID)
            log_bot.send_message(chat_id=LOG_ID, text=table_msg)
            logger.info(f"✅ Updated cloned bots table in log channel for owner {owner_id}")
        except Exception as e:
            logger.error(f"🚨 Failed to update cloned bots table in log channel: {str(e)}")
            raise

    except Exception as e:
        logger.error(f"🚨 Failed to save cloned bot @{username}: {str(e)}")
        raise
