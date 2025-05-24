import os
import logging
import json
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext

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
        return {"force_subscription": False, "search_caption": "🔍 Search Result", "delete_timer": "0m", "forcesub_channels": ["@bot_paiyan_official"]}

def upload_to_gdtot(file_url):
    """Upload a file to GDToT and return the download link. 📤"""
    GDTOT_API_KEY = os.getenv("GDTOT_API_KEY")
    if not GDTOT_API_KEY:
        logger.error("🚨 GDTOT_API_KEY not set in environment variables")
        return None

    try:
        api_url = f"https://gdtot.com/api/upload?api_key={GDTOT_API_KEY}&url={file_url}"
        response = requests.get(api_url)
        data = response.json()
        if data.get("status") == "success":
            return data.get("download_link")
        logger.error(f"🚨 Failed to upload to GDToT: {data.get('message')}")
        return None
    except Exception as e:
        logger.error(f"🚨 Error uploading to GDToT: {str(e)}")
        return None

def upload(update: Update, context: CallbackContext):
    """Handle file upload to GDToT and store metadata. 📤"""
    user_id = str(update.effective_user.id)
    username = update.effective_user.username or "Unknown"
    args = context.args

    if not args:
        update.message.reply_text("🚫 Please provide a file URL to upload.\nExample: /upload https://example.com/file.mp4 😅")
        return

    file_url = args[0]
    logger.info(f"ℹ️ User {user_id} uploading file: {file_url}")
    send_log_to_channel(context, f"User {user_id} initiated file upload: {file_url} 📤")
    log_user_activity(context, user_id, username, f"Initiated File Upload: {file_url}")

    gdtot_link = upload_to_gdtot(file_url)
    if not gdtot_link:
        update.message.reply_text("🚫 Failed to upload the file to GDToT. 😓")
        send_log_to_channel(context, f"User {user_id} failed to upload file: {file_url} 🚫")
        log_user_activity(context, user_id, username, f"Failed File Upload: {file_url}")
        return

    files = get_stored_files()
    file_id = str(len(files) + 1)
    file_metadata = {
        "id": file_id,
        "start_id": file_id,
        "filename": file_url.split("/")[-1],
        "size": "Unknown size",  # GDToT API would need to provide this
        "gdtot_link": gdtot_link
    }
    files.append(file_metadata)
    save_files(files)

    update.message.reply_text(
        f"✅ File uploaded successfully! 🎉\n\n"
        f"📁 **File ID**: {file_id}\n"
        f"🔗 **Download Link**: {gdtot_link}",
        parse_mode="Markdown"
    )
    send_log_to_channel(context, f"User {user_id} uploaded file with ID {file_id} 📤")
    log_user_activity(context, user_id, username, f"Uploaded File with ID: {file_id}")

def get_file(update: Update, context: CallbackContext):
    """Retrieve a file by ID. 📁"""
    user_id = str(update.effective_user.id)
    username = update.effective_user.username or "Unknown"
    args = context.args

    if not args:
        update.message.reply_text("🚫 Please provide a file ID.\nExample: /get 1 😅")
        return

    file_id = args[0]
    logger.info(f"ℹ️ User {user_id} retrieving file with ID: {file_id}")
    send_log_to_channel(context, f"User {user_id} requested file with ID: {file_id} 📁")
    log_user_activity(context, user_id, username, f"Requested File with ID: {file_id}")

    files = get_stored_files()
    file = next((f for f in files if f["id"] == file_id), None)
    if not file:
        update.message.reply_text(f"🚫 File with ID {file_id} not found. 😓")
        send_log_to_channel(context, f"User {user_id} requested non-existent file ID: {file_id} 🚫")
        log_user_activity(context, user_id, username, f"Requested Non-Existent File ID: {file_id}")
        return

    response = (
        f"📁 **File Details** 📁\n\n"
        f"🆔 **ID**: {file['id']}\n"
        f"📄 **Name**: {file['filename']}\n"
        f"📏 **Size**: {file.get('size', 'Unknown size')}\n"
        f"🔗 **Download Link**: {file['gdtot_link']}"
    )
    update.message.reply_text(response, parse_mode="Markdown")
    send_log_to_channel(context, f"User {user_id} retrieved file with ID: {file_id} 📁")
    log_user_activity(context, user_id, username, f"Retrieved File with ID: {file_id}")

def batch(update: Update, context: CallbackContext):
    """Retrieve a range of files by ID. 📦"""
    user_id = str(update.effective_user.id)
    username = update.effective_user.username or "Unknown"
    args = context.args

    if len(args) != 2:
        update.message.reply_text("🚫 Please provide a start and end ID.\nExample: /batch 1 5 😅")
        return

    try:
        start_id = int(args[0])
        end_id = int(args[1])
    except ValueError:
        update.message.reply_text("🚫 IDs must be numbers.\nExample: /batch 1 5 😅")
        return

    logger.info(f"ℹ️ User {user_id} retrieving batch files from ID {start_id} to {end_id}")
    send_log_to_channel(context, f"User {user_id} requested batch files from ID {start_id} to {end_id} 📦")
    log_user_activity(context, user_id, username, f"Requested Batch Files from ID {start_id} to {end_id}")

    files = get_stored_files()
    batch_files = [f for f in files if start_id <= int(f["id"]) <= end_id]
    if not batch_files:
        update.message.reply_text(f"🚫 No files found between IDs {start_id} and {end_id}. 😓")
        send_log_to_channel(context, f"User {user_id} found no files between IDs {start_id} and {end_id} 🚫")
        log_user_activity(context, user_id, username, f"Found No Files between IDs {start_id} to {end_id}")
        return

    response = f"📦 **Batch Files (IDs {start_id} to {end_id})** 📦\n\n"
    for file in batch_files:
        response += (
            f"🆔 **ID**: {file['id']}\n"
            f"📄 **Name**: {file['filename']}\n"
            f"📏 **Size**: {file.get('size', 'Unknown size')}\n"
            f"🔗 **Download Link**: {file['gdtot_link']}\n\n"
        )
    update.message.reply_text(response, parse_mode="Markdown")
    send_log_to_channel(context, f"User {user_id} retrieved batch files from ID {start_id} to {end_id} 📦")
    log_user_activity(context, user_id, username, f"Retrieved Batch Files from ID {start_id} to {end_id}")

def genlink(update: Update, context: CallbackContext):
    """Generate a download link for a file by ID. 🔗"""
    user_id = str(update.effective_user.id)
    username = update.effective_user.username or "Unknown"
    args = context.args

    if not args:
        update.message.reply_text("🚫 Please provide a file ID.\nExample: /genlink 1 😅")
        return

    file_id = args[0]
    logger.info(f"ℹ️ User {user_id} generating link for file with ID: {file_id}")
    send_log_to_channel(context, f"User {user_id} requested link generation for file with ID: {file_id} 🔗")
    log_user_activity(context, user_id, username, f"Requested Link Generation for File ID: {file_id}")

    files = get_stored_files()
    file = next((f for f in files if f["id"] == file_id), None)
    if not file:
        update.message.reply_text(f"🚫 File with ID {file_id} not found. 😓")
        send_log_to_channel(context, f"User {user_id} requested link for non-existent file ID: {file_id} 🚫")
        log_user_activity(context, user_id, username, f"Requested Link for Non-Existent File ID: {file_id}")
        return

    update.message.reply_text(
        f"🔗 **Generated Link** 🔗\n\n"
        f"📁 **File ID**: {file_id}\n"
        f"🔗 **Download Link**: {file['gdtot_link']}",
        parse_mode="Markdown"
    )
    send_log_to_channel(context, f"User {user_id} generated link for file with ID: {file_id} 🔗")
    log_user_activity(context, user_id, username, f"Generated Link for File ID: {file_id}")

def batchgen(update: Update, context: CallbackContext):
    """Generate download links for a range of files by ID. 📢"""
    user_id = str(update.effective_user.id)
    username = update.effective_user.username or "Unknown"
    args = context.args

    if len(args) != 2:
        update.message.reply_text("🚫 Please provide a start and end ID.\nExample: /batchgen 1 5 😅")
        return

    try:
        start_id = int(args[0])
        end_id = int(args[1])
    except ValueError:
        update.message.reply_text("🚫 IDs must be numbers.\nExample: /batchgen 1 5 😅")
        return

    logger.info(f"ℹ️ User {user_id} generating batch links from ID {start_id} to {end_id}")
    send_log_to_channel(context, f"User {user_id} requested batch link generation from ID {start_id} to {end_id} 📢")
    log_user_activity(context, user_id, username, f"Requested Batch Link Generation from ID {start_id} to {end_id}")

    files = get_stored_files()
    batch_files = [f for f in files if start_id <= int(f["id"]) <= end_id]
    if not batch_files:
        update.message.reply_text(f"🚫 No files found between IDs {start_id} and {end_id}. 😓")
        send_log_to_channel(context, f"User {user_id} found no files for batch link generation between IDs {start_id} and {end_id} 🚫")
        log_user_activity(context, user_id, username, f"Found No Files for Batch Link Generation between IDs {start_id} to {end_id}")
        return

    response = f"📢 **Batch Generated Links (IDs {start_id} to {end_id})** 📢\n\n"
    for file in batch_files:
        response += (
            f"🆔 **ID**: {file['id']}\n"
            f"📄 **Name**: {file['filename']}\n"
            f"🔗 **Download Link**: {file['gdtot_link']}\n\n"
        )
    update.message.reply_text(response, parse_mode="Markdown")
    send_log_to_channel(context, f"User {user_id} generated batch links from ID {start_id} to {end_id} 📢")
    log_user_activity(context, user_id, username, f"Generated Batch Links from ID {start_id} to {end_id}")
