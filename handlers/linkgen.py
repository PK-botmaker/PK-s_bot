import os
import logging
import json
import requests
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

def save_files(files):
    """Save files to files.json. 💾"""
    try:
        with open(FILES_STORAGE_PATH, "w") as f:
            json.dump(files, f, indent=4)
    except Exception as e:
        logger.error(f"🚨 Failed to save files: {str(e)}")

def get_settings():
    """Load bot settings from settings.json. ⚙️"""
    try:
        with open(SETTINGS_PATH, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"🚨 Failed to load settings: {str(e)}")
        return {"shortener": "GPLinks"}

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

def upload_to_gdtot(file_path: str, file_name: str) -> str:
    """Placeholder for uploading to GDToT. 📤"""
    try:
        logger.info(f"ℹ️ Uploading {file_name} to GDToT 📦")
        gdtot_link = f"https://new.gdtot.com/file/{hash(file_name)}"
        return gdtot_link
    except Exception as e:
        logger.error(f"🚨 Failed to upload to GDToT: {str(e)}")
        return ""

def upload(update: Update, context: CallbackContext):
    """Handle /upload command to upload a file to GDToT. 📤"""
    user_id = str(update.effective_user.id)
    username = update.effective_user.username or "Unknown"

    if not update.message.document:
        update.message.reply_text("🚫 Please send a file to upload. 📁")
        return

    file = update.message.document
    file_name = file.file_name
    file_id = file.file_id

    files = get_stored_files()
    start_id = str(len(files) + 1)

    file_info = {
        "start_id": start_id,
        "filename": file_name,
        "size": f"{file.file_size / (1024 * 1024):.2f} MB",
        "file_id": file_id,
        "uploaded_at": datetime.now().isoformat()
    }

    gdtot_link = upload_to_gdtot(None, file_name)
    if not gdtot_link:
        update.message.reply_text("🚫 Failed to upload to GDToT. 😓")
        return

    file_info["gdtot_link"] = gdtot_link
    files.append(file_info)
    save_files(files)

    shortened_url = shorten_url(gdtot_link)
    update.message.reply_text(f"✅ File uploaded successfully! 🎉\nStart ID: {start_id}\nLink: {shortened_url}")
    send_log_to_channel(context, f"User {user_id} uploaded file with start_id {start_id}: {file_name} 📤")
    log_user_activity(context, user_id, username, f"Uploaded File (start_id: {start_id})")

def get_file(update: Update, context: CallbackContext):
    """Handle /get command to retrieve a file by start_id. 📁"""
    user_id = str(update.effective_user.id)
    username = update.effective_user.username or "Unknown"
    args = context.args

    if not args:
        update.message.reply_text("🚫 Please provide a start_id.\nExample: /get 1 😅")
        return

    start_id = args[0]
    files = get_stored_files()
    file = next((f for f in files if f["start_id"] == start_id), None)

    if not file:
        update.message.reply_text(f"🚫 File with start_id {start_id} not found. 😓")
        return

    gdtot_link = file.get("gdtot_link")
    if not gdtot_link:
        update.message.reply_text("🚫 No GDToT link available for this file. 😓")
        return

    shortened_url = shorten_url(gdtot_link)
    response = f"📁 File: {file['filename']}\n📏 Size: {file['size']}\n🔗 Link: {shortened_url}"
    update.message.reply_text(response)
    send_log_to_channel(context, f"User {user_id} retrieved file with start_id {start_id} 📁")
    log_user_activity(context, user_id, username, f"Retrieved File (start_id: {start_id})")

def batch(update: Update, context: CallbackContext):
    """Handle /batch command to retrieve a range of files. 📦"""
    user_id = str(update.effective_user.id)
    username = update.effective_user.username or "Unknown"
    args = context.args

    if len(args) != 2:
        update.message.reply_text("🚫 Please provide start_id and end_id.\nExample: /batch 1 5 😅")
        return

    try:
        start_id, end_id = map(int, args)
    except ValueError:
        update.message.reply_text("🚫 Start_id and end_id must be numbers. 😅")
        return

    files = get_stored_files()
    batch_files = [f for f in files if start_id <= int(f["start_id"]) <= end_id]

    if not batch_files:
        update.message.reply_text(f"🚫 No files found between start_id {start_id} and end_id {end_id}. 😓")
        return

    response = "📦 Batch Files:\n\n"
    for file in batch_files:
        gdtot_link = file.get("gdtot_link")
        if gdtot_link:
            shortened_url = shorten_url(gdtot_link)
            response += f"📁 File: {file['filename']}\n📏 Size: {file['size']}\n🔗 Link: {shortened_url}\n\n"
        else:
            response += f"📁 File: {file['filename']} (No link available)\n"

    update.message.reply_text(response)
    send_log_to_channel(context, f"User {user_id} retrieved batch files from start_id {start_id} to {end_id} 📦")
    log_user_activity(context, user_id, username, f"Retrieved Batch Files (start_id: {start_id} to {end_id})")

def genlink(update: Update, context: CallbackContext):
    """Handle /genlink command to generate a link for a specific file. 🔗"""
    user_id = str(update.effective_user.id)
    username = update.effective_user.username or "Unknown"
    args = context.args

    if not args:
        update.message.reply_text("🚫 Please provide a start_id.\nExample: /genlink 1 😅")
        return

    start_id = args[0]
    files = get_stored_files()
    file = next((f for f in files if f["start_id"] == start_id), None)

    if not file:
        update.message.reply_text(f"🚫 File with start_id {start_id} not found. 😓")
        return

    gdtot_link = file.get("gdtot_link")
    if not gdtot_link:
        update.message.reply_text("🚫 No GDToT link available for this file. 😓")
        return

    shortened_url = shorten_url(gdtot_link)
    update.message.reply_text(f"🔗 Generated Link: {shortened_url} 🎉")
    send_log_to_channel(context, f"User {user_id} generated link for file with start_id {start_id} 🔗")
    log_user_activity(context, user_id, username, f"Generated Link for File (start_id: {start_id})")

def batchgen(update: Update, context: CallbackContext):
    """Handle /batchgen command to generate links for a range of files. 🔗"""
    user_id = str(update.effective_user.id)
    username = update.effective_user.username or "Unknown"
    args = context.args

    if len(args) != 2:
        update.message.reply_text("🚫 Please provide start_id and end_id.\nExample: /batchgen 1 5 😅")
        return

    try:
        start_id, end_id = map(int, args)
    except ValueError:
        update.message.reply_text("🚫 Start_id and end_id must be numbers. 😅")
        return

    files = get_stored_files()
    batch_files = [f for f in files if start_id <= int(f["start_id"]) <= end_id]

    if not batch_files:
        update.message.reply_text(f"🚫 No files found between start_id {start_id} and end_id {end_id}. 😓")
        return

    response = "🔗 Batch Generated Links:\n\n"
    for file in batch_files:
        gdtot_link = file.get("gdtot_link")
        if gdtot_link:
            shortened_url = shorten_url(gdtot_link)
            response += f"📁 File: {file['filename']}\n📏 Size: {file['size']}\n🔗 Link: {shortened_url}\n\n"
        else:
            response += f"📁 File: {file['filename']} (No link available)\n"

    update.message.reply_text(response)
    send_log_to_channel(context, f"User {user_id} generated batch links from start_id {start_id} to {end_id} 🔗")
    log_user_activity(context, user_id, username, f"Generated Batch Links (start_id: {start_id} to {end_id})")