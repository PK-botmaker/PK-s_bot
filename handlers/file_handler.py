from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
from utils.db_channel import get_setting, set_setting
from utils.logging_utils import log_error
import logging

logger = logging.getLogger(__name__)

def handle_file(update: Update, context: CallbackContext):
    """📤 Handle file uploads and store metadata."""
    user_id = update.effective_user.id
    message = update.message
    file = message.document or message.photo[-1] if message.photo else message.video or message.audio

    try:
        file_id = file.file_id
        file_name = getattr(file, "file_name", f"File_{file_id}")
        files = get_setting("files", {})
        files[file_name] = {"file_id": file_id, "uploader": user_id}
        set_setting("files", files)

        # Check if user is in batch edit mode
        batch_id = context.user_data.get("awaiting_batch_edit")
        if batch_id:
            batches = get_setting("batches", [])
            batch = next((b for b in batches if b["id"] == batch_id), None)
            if batch:
                batch["files"].append(file_id)
                set_setting("batches", batches)
                update.message.reply_text(f"✅ File added to batch '{batch['name']}'! 🎉")
                logger.info(f"✅ User {user_id} added file {file_id} to batch {batch_id}! 🌟")
                return

        # Apply custom caption and buttons
        custom_caption = get_setting("custom_caption", "")
        custom_buttons = get_setting("custom_buttons", [])
        reply_markup = None
        if custom_buttons:
            buttons = [[InlineKeyboardButton(btn["text"], url=btn["url"]) for btn in custom_buttons]]
            reply_markup = InlineKeyboardMarkup(buttons)

        update.message.reply_text(
            f"✅ File uploaded: {file_name}\n{custom_caption}" if custom_caption else f"✅ File uploaded: {file_name}",
            reply_markup=reply_markup
        )
        logger.info(f"✅ User {user_id} uploaded file {file_id}! 🌟")
    except Exception as e:
        update.message.reply_text("⚠️ Failed to upload file! Try again! 😅")
        log_error(f"🚨 File upload error for user {user_id}: {str(e)}")
