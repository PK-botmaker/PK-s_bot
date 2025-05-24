import os
import logging
import json
import requests
import uuid
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext, JobQueue
from utils.search_utils import search_files
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

FILES_STORAGE_PATH = "/opt/render/project/src/data/files.json"
TOKEN_STORAGE_PATH = "/opt/render/project/src/data/tokens.json"
SETTINGS_PATH = "/opt/render/project/src/data/settings.json"

HOW_TO_DOWNLOAD_LINK = "https://t.me/c/2323164776/7"

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

def get_settings():
    """Load bot settings from settings.json. ⚙️"""
    try:
        with open(SETTINGS_PATH, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"🚨 Failed to load settings: {str(e)}")
        return {"force_subscription": False, "search_caption": "🔍 Search Result", "delete_timer": "0m", "forcesub_channels": ["@bot_paiyan_official"]}

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

def search(update: Update, context: CallbackContext):
    """
    Handle search command or group message to search for files with AI-like logic. 🔍
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

    files = get_stored_files()
    if not files:
        message = update.message.reply_text("🚫 No files found in the database. 😢")
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
    tokens = get_tokens()
    RENDER_EXTERNAL_HOSTNAME = os.getenv("RENDER_EXTERNAL_HOSTNAME")

    for idx, file in enumerate(matching_files, 1):
        gdtot_link = file.get("gdtot_link")
        if not gdtot_link:
            continue

        token = str(uuid.uuid4())
        tokens[token] = gdtot_link
        context.bot_data["token_for_" + file.get("start_id")] = token
        save_tokens(tokens)

        redirect_url = f"https://{RENDER_EXTERNAL_HOSTNAME}/redirect/{token}"
        shortened_url = shorten_url(redirect_url)

        group_response = f"{caption}\n\n{idx}. {file.get('filename')} ({file.get('size', 'Unknown size')})"
        keyboard = [[InlineKeyboardButton("☁️ Get Download Link 📥", callback_data=f"download_{file.get('start_id')}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        group_message = update.message.reply_text(group_response, reply_markup=reply_markup)
        send_log_to_channel(context, f"User {user_id} received search result: {file.get('filename')} 🔍")

        delete_timer = parse_delete_timer(settings.get("delete_timer", "0m"))
        schedule_message_deletion(context, update.message.chat_id, group_message.message_id, delete_timer)

def handle_link_click(update: Update, context: CallbackContext):
    """
    Handle the click on a download button to send the link to the user in DM. 📥
    """
    query = update.callback_query
    user_id = str(query.from_user.id)
    username = query.from_user.username or "Unknown"
    start_id = query.data.split("_")[-1]
    token_key = f"token_for_{start_id}"
    token = context.bot_data.get(token_key)

    if not token:
        query.message.edit_text("🚫 Link expired or invalid. 😓")
        send_log_to_channel(context, f"User {user_id} tried to access expired/invalid link for start_id {start_id} 🚫")
        log_user_activity(context, user_id, username, f"Tried to Access Expired/Invalid Link (start_id: {start_id})")
        return

    tokens = get_tokens()
    gdtot_link = tokens.get(token)
    if not gdtot_link:
        query.message.edit_text("🚫 Link expired or invalid. 😓")
        send_log_to_channel(context, f"User {user_id} tried to access expired/invalid link for start_id {start_id} 🚫")
        log_user_activity(context, user_id, username, f"Tried to Access Expired/Invalid Link (start_id: {start_id})")
        return

    # Parse file size to determine if it's greater than 2 GB 📏
    file_size_str = query.message.text.split('(')[1].split(')')[0]
    file_size_gb = parse_file_size(file_size_str)
    is_large_file = file_size_gb > 2

    # Shorten the cloud link 🔗
    shortened_url = shorten_url(gdtot_link)

    # Prepare DM message based on file size 💬
    if is_large_file:
        dm_text = (
            "✨ **Download Your File!** ✨\n\n"
            f"📁 **File**: {query.message.text.split('\n\n')[-1].split('(')[0].strip()}\n"
            f"📏 **Size**: {file_size_str}\n"
            "⚠️ **Note**: This file is larger than 2 GB. A cloud link has been provided for download. ☁️\n\n"
            "👇 **Choose an Option Below** 👇"
        )
    else:
        dm_text = (
            "✨ **Download Your File!** ✨\n\n"
            f"📁 **File**: {query.message.text.split('\n\n')[-1].split('(')[0].strip()}\n"
            f"📏 **Size**: {file_size_str}\n\n"
            "👇 **Choose an Option Below** 👇"
        )

    keyboard = [
        [
            InlineKeyboardButton("📩 Telegram Download", url=shortened_url, callback_data=f"download_{token}"),
            InlineKeyboardButton("❓ How to Download", callback_data="how_to_download")
        ],
        [
            InlineKeyboardButton("⚡ Gen Fast Download", url=shortened_url, callback_data=f"download_{token}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        dm_message = context.bot.send_message(
            chat_id=user_id,
            text=dm_text,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        send_log_to_channel(context, f"User {user_id} received download link for file with start_id {start_id} 📥")
        log_user_activity(context, user_id, username, f"Received Download Link for File (start_id: {start_id})")

        # Schedule message deletion ⏳
        settings = get_settings()
        delete_timer = parse_delete_timer(settings.get("delete_timer", "0m"))
        schedule_message_deletion(context, dm_message.chat_id, dm_message.message_id, delete_timer)

        # Delete the token after use (one-time link) 🔗
        tokens.pop(token, None)
        save_tokens(tokens)
        context.bot_data.pop(token_key, None)

        query.message.edit_text(f"✅ Link sent to your DM! Check your messages. 📩")
    except Exception as e:
        query.message.edit_text("🚫 Failed to send the link to your DM. Please allow DMs from this bot. 😓")
        send_log_to_channel(context, f"User {user_id} failed to receive DM for file with start_id {start_id}: {str(e)} 🚫")
        log_user_activity(context, user_id, username, f"Failed to Receive DM for File (start_id: {start_id})")

def handle_button_click(update: Update, context: CallbackContext):
    """
    Handle button clicks in the private DM. 🔄
    """
    query = update.callback_query
    user_id = str(query.from_user.id)
    username = query.from_user.username or "Unknown"
    data = query.data

    if data.startswith("download_"):
        context.bot.delete_message(chat_id=user_id, message_id=query.message.message_id)
        send_log_to_channel(context, f"User {user_id} downloaded file via button. 📥")
        log_user_activity(context, user_id, username, "Downloaded File via Button")
    elif data == "how_to_download":
        keyboard = [[InlineKeyboardButton("🔙 Back to Download 🔄", callback_data="back_to_download")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.message.edit_text(f"📚 Follow this guide to download your file! 📖\n{HOW_TO_DOWNLOAD_LINK}", reply_markup=reply_markup)
        send_log_to_channel(context, f"User {user_id} viewed How to Download guide. 📚")
        log_user_activity(context, user_id, username, "Viewed How to Download Guide")
    elif data == "back_to_download":
        # Restore the original download link message
        query.message.edit_text(query.message.text, reply_markup=query.message.reply_markup)
        send_log_to_channel(context, f"User {user_id} returned to download link. 🔄")
        log_user_activity(context, user_id, username, "Returned to Download Link")

def handle_group_message(update: Update, context: CallbackContext):
    """Handle all group messages as search queries. 💬"""
    search(update, context)
