import os
import logging
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext

logger = logging.getLogger(__name__)

TOKEN_STORAGE_PATH = "/opt/render/project/src/data/tokens.json"

def send_log_to_channel(context: CallbackContext, message: str):
    """Send a log message to the Telegram log channel. 📜"""
    LOG_CHANNEL_ID = os.getenv("LOG_CHANNEL_ID")
    if not LOG_CHANNEL_ID:
        logger.error("🚨 LOG_CHANNEL_ID not set in environment variables")
        return

    try:
        context.bot.send_message(chat_id=LOG_CHANNEL_ID, text=f"📝 {message}")
        logger.info(f"✅ Log sent to channel {LOG_CHANNEL_ID}: {message}")
    except Exception as e:
        logger.error(f"🚨 Failed to send log to channel {LOG_CHANNEL_ID}: {str(e)}")

def log_user_activity(context: CallbackContext, user_id: str, username: str, action: str):
    """Log user activity in a table format to the log channel. 📊"""
    cloned_bots = []
    try:
        with open("/opt/render/project/src/data/cloned_bots.json", "r") as f:
            cloned_bots = json.load(f)
    except:
        cloned_bots = []
    user_bots = [bot for bot in cloned_bots if bot["owner_id"] == user_id]
    num_bots = len(user_bots)
    files = []
    try:
        with open("/opt/render/project/src/data/files.json", "r") as f:
            files = json.load(f)
    except:
        files = []
    total_users = len(get_users())
    
    table = (
        "📊 **User Activity Log** 📊\n\n"
        "┌───────────────────────────────┐\n"
        f"│ 🆔 **User ID**: {user_id}\n"
        f"│ 👤 **Username**: @{username}\n"
        f"│ 🛠️ **Action**: {action}\n"
        f"│ 🤖 **Created Bots**: {num_bots}\n"
        f"│ 📁 **Total Files in Bot**: {len(files)}\n"
        f"│ 👥 **Total Users**: {total_users}\n"
        "└───────────────────────────────┘"
    )
    send_log_to_channel(context, table)

def get_users():
    """Load user IDs from users.json. 👥"""
    try:
        with open("/opt/render/project/src/data/users.json", "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"🚨 Failed to load users: {str(e)}")
        return []

def get_tokens():
    """Load one-time link tokens from tokens.json. 🔗"""
    try:
        with open(TOKEN_STORAGE_PATH, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"🚨 Failed to load tokens: {str(e)}")
        return {}

def save_tokens(tokens):
    """Save one-time link tokens to tokens.json. 💾"""
    try:
        with open(TOKEN_STORAGE_PATH, "w") as f:
            json.dump(tokens, f, indent=4)
    except Exception as e:
        logger.error(f"🚨 Failed to save tokens: {str(e)}")

def redirect_handler(token: str):
    """
    Handle redirect for one-time download links and invalidate the token after use. 🔗
    """
    tokens = get_tokens()
    gdtot_link = tokens.get(token)

    if not gdtot_link:
        logger.error(f"🚨 Invalid or expired token: {token}")
        return None

    # Invalidate the token after use (one-time link) 🗑️
    tokens.pop(token, None)
    save_tokens(tokens)
    logger.info(f"ℹ️ Token {token} used and invalidated")

    return gdtot_link
