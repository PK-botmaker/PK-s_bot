import os
import logging
import json
import requests
import uuid
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext, JobQueue
from utils.search_utils import search_files, get_related_keywords
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

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
    total_users = len(get_users())
    
    table = (
        "📊 **User Activity Log** 📊\n\n"
        "┌───────────────────────────────┐\n"
        f"│ 🆔 **User ID**: {user_id}\n"
        f"│ 👤 **Username**: @{username}\n"
        f"│ 🛠️ **Action**: {action}\n"
        f"│ 🤖 **Created Bots**: {num_bots}\n"
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

def get_settings():
    """Load bot settings from settings.json. ⚙️"""
    try:
        with open(SETTINGS_PATH, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"🚨 Failed to load settings: {str(e)}")
        return {"force_subscription": False, "search_caption": "🔍 Search Result", "delete_timer": "0m", "forcesub_channels": ["@bot_paiyan_official"]}

def can_shorten_url():
    """Check if URL shortening is enabled and possible. 🔗"""
    GPLINKS_API_KEY = os.getenv("GPLINKS_API_KEY")
    settings = get_settings()
    shortener = settings.get("shortener", "GPLinks")
    return shortener != "None" and GPLINKS_API_KEY is not None

def shorten_url(url):
    """Shorten a URL using GPLinks API if available, else return the raw URL. 🔗"""
    GPLINKS_API_KEY = os.getenv("GPLINKS_API_KEY")
    settings = get_settings()
    shortener = settings.get("shortener", "GPLinks")

    if shortener == "None" or not GPLINKS_API_KEY:
        logger.info("ℹ️ GPLinks API key not set or shortener disabled, using raw URL")
        return url

    try:
        api_url = f"https://gplinks.co/api?api={GPLINKS_API_KEY}&url={url}"
        response = requests.get(api_url)
        data = response.json()
        if data.get("status") == "success":
            return data.get("shortenedUrl")
        logger.error(f"🚨 Failed to shorten URL: {data.get('message')}")
        return url
    except Exception as e:
        logger.error(f"🚨 Error shortening URL: {str(e)}")
        return url

def parse_delete_timer(timer_str):
    """Parse delete timer string (e.g., '10m', '10h') into seconds. ⏳"""
    try:
        unit = timer_str[-1].lower()
        value = int(timer_str[:-1])
        if unit == "m":
            return value * 60  # Minutes to seconds
        elif unit == "h":
            return value * 3600  # Hours to seconds
        return 0
    except (ValueError, IndexError):
        return 0

def schedule_message_deletion(context: CallbackContext, chat_id, message_id, delay_seconds):
    """Schedule a message for deletion after a delay. 🗑️"""
    if delay_seconds > 0:
        context.job_queue.run_once(
            lambda ctx: ctx.bot.delete_message(chat_id=chat_id, message_id=message_id),
            delay_seconds,
            context=(chat_id, message_id)
        )

def parse_file_size(size_str):
    """Parse file size string (e.g., '2.5 MB') and convert to GB. 📏"""
    try:
        size, unit = size_str.split()
        size = float(size)
        if unit.lower() == "mb":
            size = size / 1024  # Convert MB to GB
        elif unit.lower() == "gb":
            pass  # Already in GB
        else:
            return 0  # Unknown unit
        return size
    except (ValueError, IndexError):
        return 0

def fetch_files_from_channel(context: CallbackContext):
    """
    Fetch files from the database channel by reading recent messages. 📂
    Assumes each message in the channel has the format:
    Filename: <name>
    Size: <size>
    Link: <gdtot_link>
    """
    DB_CHANNEL_ID = os.getenv("DB_CHANNEL_ID")
    if not DB_CHANNEL_ID:
        logger.error("🚨 DB_CHANNEL_ID not set in environment variables")
        return []

    try:
        # Fetch recent messages from the channel (limit to 100 for now)
        messages = context.bot.get_chat_history(chat_id=DB_CHANNEL_ID, limit=100)
        files = []
        for idx, msg in enumerate(messages, 1):
            if not msg.text:
                continue

            # Parse the message text to extract file metadata
            lines = msg.text.split("\n")
            file_data = {}
            for line in lines:
                if line.startswith("Filename:"):
                    file_data["filename"] = line.replace("Filename:", "").strip()
                elif line.startswith("Size:"):
                    file_data["size"] = line.replace("Size:", "").strip()
                elif line.startswith("Link:"):
                    file_data["gdtot_link"] = line.replace("Link:", "").strip()

            # Ensure all required fields are present
            if all(key in file_data for key in ["filename", "size", "gdtot_link"]):
                file_data["id"] = str(idx)  # Use message index as a unique ID
                file_data["start_id"] = str(idx)  # Same as ID for consistency
                file_data["upload_date"] = msg.date.strftime("%Y-%m-%d")  # Add upload date
                files.append(file_data)

        logger.info(f"ℹ️ Fetched {len(files)} files from database channel {DB_CHANNEL_ID}")
        return files
    except Exception as e:
        logger.error(f"🚨 Failed to fetch files from channel {DB_CHANNEL_ID}: {str(e)}")
        return []

def search(update: Update, context: CallbackContext):
    """
    Handle search command or group message to search for files in the database channel. 🔍
    """
    user_id = str(update.effective_user.id)
    username = update.effective_user.username or "Unknown"
    query = None

    # Check subscription to all force subscription channels 🔒
    settings = get_settings()
    forcesub_channels = settings.get("forcesub_channels", ["@bot_paiyan_official"])
    if settings.get("force_subscription", False):
        keyboard = []
        for channel in forcesub_channels:
            try:
                chat_id = channel if channel.startswith("@") else f"@{channel}"
                member = context.bot.get_chat_member(chat_id=chat_id, user_id=user_id)
                if member.status in ["left", "kicked"]:
                    keyboard.append([InlineKeyboardButton(f"🔗 Join {chat_id} 🌟", url=f"https://t.me/{chat_id[1:]}")])
            except Exception as e:
                message = update.message.reply_text(f"🚫 Error checking membership for {chat_id}. Please try again. 😓")
                delete_timer = parse_delete_timer(settings.get("delete_timer", "0m"))
                schedule_message_deletion(context, update.message.chat_id, message.message_id, delete_timer)
                send_log_to_channel(context, f"Error checking membership for user {user_id} in {chat_id}: {str(e)} 🚫")
                log_user_activity(context, user_id, username, f"Failed Membership Check for {chat_id}")
                return

        if keyboard:
            reply_markup = InlineKeyboardMarkup(keyboard)
            message = update.message.reply_text("🚫 You must join the following channels to use this bot! 🔗", reply_markup=reply_markup)
            delete_timer = parse_delete_timer(settings.get("delete_timer", "0m"))
            schedule_message_deletion(context, update.message.chat_id, message.message_id, delete_timer)
            send_log_to_channel(context, f"User {user_id} denied access - not subscribed to required channels. 🚫")
            log_user_activity(context, user_id, username, "Denied Access - Not Subscribed")
            return

    if update.message.chat.type in ["group", "supergroup"]:
        query = update.message.text
    else:
        args = context.args
        if not args:
            message = update.message.reply_text("🚫 Please provide a search query.\nExample: /search Avengers 😅")
            delete_timer = parse_delete_timer(settings.get("delete_timer", "0m"))
            schedule_message_deletion(context, update.message.chat_id, message.message_id, delete_timer)
            return
        query = " ".join(args)

    logger.info(f"ℹ️ User {user_id} searching for: {query}")
    send_log_to_channel(context, f"User {user_id} searched for: {query} 🔍")
    log_user_activity(context, user_id, username, f"Searched for: {query}")

    # Fetch files from the database channel
    files = fetch_files_from_channel(context)
    if not files:
        message = update.message.reply_text("🚫 No files found in the database channel. 😢")
        delete_timer = parse_delete_timer(settings.get("delete_timer", "0m"))
        schedule_message_deletion(context, update.message.chat_id, message.message_id, delete_timer)
        return

    matching_files = search_files(query, files, limit=5)
    if not matching_files:
        message = update.message.reply_text(f"🚫 No results found for '{query}'. 😓")
        delete_timer = parse_delete_timer(settings.get("delete_timer", "0m"))
        schedule_message_deletion(context, update.message.chat_id, message.message_id, delete_timer)
        return

    settings = get_settings()
    caption = settings.get("search_caption", "🔍 Search Result")
    can_shorten = can_shorten_url()  # Check if we can shorten URLs

    # Display search results
    for idx, file in enumerate(matching_files, 1):
        gdtot_link = file.get("gdtot_link")
        if not gdtot_link:
            continue

        # Shorten the link only if we can (will be displayed if shortened)
        display_url = None
        if can_shorten:
            display_url = shorten_url(gdtot_link)

        # Prepare the search result message
        group_response = (
            f"{caption}\n\n"
            f"{idx}. **{file.get('filename')}** ({file.get('size', 'Unknown size')})\n"
            f"📅 **Uploaded**: {file.get('upload_date', 'Unknown')}\n"
        )
        if display_url:
            group_response += f"🔗 **Download Link**: {display_url}\n"

        keyboard = [[InlineKeyboardButton("📥 Download Now", callback_data=f"download_{file.get('start_id')}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        group_message = update.message.reply_text(group_response, reply_markup=reply_markup, parse_mode="Markdown")
        send_log_to_channel(context, f"User {user_id} received search result: {file.get('filename')} 🔍")

        delete_timer = parse_delete_timer(settings.get("delete_timer", "0m"))
        schedule_message_deletion(context, update.message.chat_id, group_message.message_id, delete_timer)

def handle_link_click(update: Update, context: CallbackContext):
    """
    Handle the click on a download button to redirect the user directly to the file. 📥
    """
    query = update.callback_query
    user_id = str(query.from_user.id)
    username = query.from_user.username or "Unknown"
    start_id = query.data.split("_")[-1]

    # Fetch files again to find the matching file
    files = fetch_files_from_channel(context)
    file = next((f for f in files if f["start_id"] == start_id), None)
    if not file:
        query.message.edit_text("🚫 File not found or link expired. 😓")
        send_log_to_channel(context, f"User {user_id} tried to access non-existent file with start_id {start_id} 🚫")
        log_user_activity(context, user_id, username, f"Tried to Access Non-Existent File (start_id: {start_id})")
        return

    gdtot_link = file.get("gdtot_link")
    if not gdtot_link:
        query.message.edit_text("🚫 Download link not available. 😓")
        send_log_to_channel(context, f"User {user_id} tried to access invalid link for start_id {start_id} 🚫")
        log_user_activity(context, user_id, username, f"Tried to Access Invalid Link (start_id: {start_id})")
        return

    # Shorten the link if possible (for the redirect)
    final_url = shorten_url(gdtot_link)

    # Redirect the user directly to the download link
    keyboard = [[InlineKeyboardButton("📥 Download File", url=final_url)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.message.edit_text(
        f"✅ Redirecting to your file: **{file.get('filename')}** 🎉\n"
        f"Click below to start the download! 📩",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    send_log_to_channel(context, f"User {user_id} redirected to download file with start_id {start_id} 📥")
    log_user_activity(context, user_id, username, f"Redirected to Download File (start_id: {start_id})")

def handle_group_message(update: Update, context: CallbackContext):
    """Handle all group messages as search queries. 💬"""
    search(update, context)
