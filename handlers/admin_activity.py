import os
import logging
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
from datetime import datetime

logger = logging.getLogger(__name__)

FILES_STORAGE_PATH = "/opt/render/project/src/data/files.json"
SETTINGS_PATH = "/opt/render/project/src/data/settings.json"

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
        with open(FILES_STORAGE_PATH, "r") as f:
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

def get_stored_files():
    """Load stored files from files.json. 📂"""
    try:
        with open(FILES_STORAGE_PATH, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"🚨 Failed to load stored files: {str(e)}")
        return []

def get_cloned_bots():
    """Load cloned bots from cloned_bots.json. 🤖"""
    try:
        with open("/opt/render/project/src/data/cloned_bots.json", "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"🚨 Failed to load cloned bots: {str(e)}")
        return []

def get_settings():
    """Load bot settings from settings.json. ⚙️"""
    try:
        with open(SETTINGS_PATH, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"🚨 Failed to load settings: {str(e)}")
        return {"force_subscription": False, "search_caption": "🔍 Search Result", "delete_timer": "0m", "forcesub_channels": ["@bot_paiyan_official"]}

def is_admin(user_id: str) -> bool:
    """Check if the user is an admin. 🔑"""
    settings = get_settings()
    admin_id = settings.get("admin_id")
    return str(user_id) == str(admin_id)

def stats(update: Update, context: CallbackContext):
    """Show bot statistics to the admin. 📈"""
    user_id = str(update.effective_user.id)
    username = update.effective_user.username or "Unknown"

    if not is_admin(user_id):
        update.message.reply_text("🚫 You are not authorized to use this command. 😓")
        send_log_to_channel(context, f"User {user_id} tried to access /stats but is not an admin. 🚫")
        log_user_activity(context, user_id, username, "Tried to Access /stats (Unauthorized)")
        return

    users = get_users()
    files = get_stored_files()
    cloned_bots = get_cloned_bots()

    stats_message = (
        "📊 **Bot Statistics** 📊\n\n"
        f"👥 **Total Users**: {len(users)}\n"
        f"📁 **Total Files**: {len(files)}\n"
        f"🤖 **Total Cloned Bots**: {len(cloned_bots)}\n"
        f"🕒 **Last Updated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )
    update.message.reply_text(stats_message, parse_mode="Markdown")
    send_log_to_channel(context, f"Admin {user_id} viewed bot statistics. 📈")
    log_user_activity(context, user_id, username, "Viewed Bot Statistics")

def logs(update: Update, context: CallbackContext):
    """Show recent logs to the admin. 📜"""
    user_id = str(update.effective_user.id)
    username = update.effective_user.username or "Unknown"

    if not is_admin(user_id):
        update.message.reply_text("🚫 You are not authorized to use this command. 😓")
        send_log_to_channel(context, f"User {user_id} tried to access /logs but is not an admin. 🚫")
        log_user_activity(context, user_id, username, "Tried to Access /logs (Unauthorized)")
        return

    LOG_CHANNEL_ID = os.getenv("LOG_CHANNEL_ID")
    if not LOG_CHANNEL_ID:
        update.message.reply_text("🚫 Log channel ID not set. 😓")
        return

    try:
        messages = context.bot.get_chat_history(chat_id=LOG_CHANNEL_ID, limit=5)
        if not messages:
            update.message.reply_text("📜 No recent logs found. 😢")
            return

        log_message = "📜 **Recent Logs** 📜\n\n"
        for msg in messages:
            log_message += f"🕒 {msg.date.strftime('%Y-%m-%d %H:%M:%S')}\n{msg.text}\n\n"
        update.message.reply_text(log_message, parse_mode="Markdown")
        send_log_to_channel(context, f"Admin {user_id} viewed recent logs. 📜")
        log_user_activity(context, user_id, username, "Viewed Recent Logs")
    except Exception as e:
        update.message.reply_text(f"🚫 Failed to fetch logs: {str(e)} 😓")
        send_log_to_channel(context, f"Admin {user_id} failed to fetch logs: {str(e)} 🚫")
        log_user_activity(context, user_id, username, f"Failed to Fetch Logs: {str(e)}")

def broadcast(update: Update, context: CallbackContext):
    """Broadcast a message to all users. 📢"""
    user_id = str(update.effective_user.id)
    username = update.effective_user.username or "Unknown"

    if not is_admin(user_id):
        update.message.reply_text("🚫 You are not authorized to use this command. 😓")
        send_log_to_channel(context, f"User {user_id} tried to access /broadcast but is not an admin. 🚫")
        log_user_activity(context, user_id, username, "Tried to Access /broadcast (Unauthorized)")
        return

    args = context.args
    if not args:
        update.message.reply_text("🚫 Please provide a message to broadcast.\nExample: /broadcast Hello everyone! 😄")
        return

    message = " ".join(args)
    users = get_users()
    success_count = 0
    fail_count = 0

    for user in users:
        try:
            context.bot.send_message(chat_id=user, text=f"📢 **Broadcast Message** 📢\n\n{message}", parse_mode="Markdown")
            success_count += 1
        except Exception as e:
            fail_count += 1
            send_log_to_channel(context, f"Failed to broadcast to user {user}: {str(e)} 🚫")

    update.message.reply_text(
        f"📢 **Broadcast Report** 📢\n\n"
        f"✅ Sent to {success_count} users\n"
        f"🚫 Failed for {fail_count} users",
        parse_mode="Markdown"
    )
    send_log_to_channel(context, f"Admin {user_id} broadcasted message: {message} 📢")
    log_user_activity(context, user_id, username, f"Broadcasted Message: {message}")

def users(update: Update, context: CallbackContext):
    """List all users of the bot. 👥"""
    user_id = str(update.effective_user.id)
    username = update.effective_user.username or "Unknown"

    if not is_admin(user_id):
        update.message.reply_text("🚫 You are not authorized to use this command. 😓")
        send_log_to_channel(context, f"User {user_id} tried to access /users but is not an admin. 🚫")
        log_user_activity(context, user_id, username, "Tried to Access /users (Unauthorized)")
        return

    users = get_users()
    if not users:
        update.message.reply_text("🚫 No users found. 😢")
        return

    user_list = "👥 **User List** 👥\n\n"
    for idx, user in enumerate(users, 1):
        user_list += f"{idx}. User ID: {user}\n"
    update.message.reply_text(user_list, parse_mode="Markdown")
    send_log_to_channel(context, f"Admin {user_id} viewed user list. 👥")
    log_user_activity(context, user_id, username, "Viewed User List")
