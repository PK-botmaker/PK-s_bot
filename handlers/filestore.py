import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
from telegram.error import TelegramError, Unauthorized, BadRequest
from utils.db_channel import get_setting, set_setting
from utils.logging_utils import log_error

logger = logging.getLogger(__name__)

# File Store configuration
CHANNEL_ID = os.getenv("FILESTORE_CHANNEL_ID")  # Private channel ID for storing files

def store_file(update: Update, context: CallbackContext):
    """📦 Store files in the private channel and save metadata."""
    user_id = str(update.effective_user.id)
    try:
        if not CHANNEL_ID:
            update.message.reply_text("⚠️ File Store Channel not configured! Contact the admin! 😅")
            logger.error("🚨 FILESTORE_CHANNEL_ID not set")
            return

        # Handle different file types
        file_message = update.message
        file_id = None
        file_name = "Unknown File"
        if file_message.document:
            file_id = file_message.document.file_id
            file_name = file_message.document.file_name or "Document"
        elif file_message.photo:
            file_id = file_message.photo[-1].file_id  # Get the highest resolution photo
            file_name = "Photo"
        elif file_message.video:
            file_id = file_message.video.file_id
            file_name = file_message.video.file_name or "Video"
        elif file_message.audio:
            file_id = file_message.audio.file_id
            file_name = file_message.audio.file_name or "Audio"

        if not file_id:
            update.message.reply_text("⚠️ Unsupported file type! Send a document, photo, video, or audio! 😅")
            return

        # Forward the file to the private channel
        try:
            forwarded_message = context.bot.forward_message(
                chat_id=CHANNEL_ID,
                from_chat_id=update.message.chat_id,
                message_id=update.message.message_id
            )
        except Unauthorized:
            update.message.reply_text("⚠️ Bot lacks permission to forward messages to the channel! Contact the admin! 😅")
            logger.error(f"🚨 Unauthorized error: Bot cannot forward messages to channel {CHANNEL_ID} for user {user_id}")
            return
        except BadRequest as e:
            update.message.reply_text("⚠️ Failed to forward file: Invalid channel ID or message! Check the channel setup! 😅")
            logger.error(f"🚨 BadRequest error while forwarding to channel {CHANNEL_ID} for user {user_id}: {str(e)}")
            return
        except TelegramError as e:
            update.message.reply_text(f"⚠️ Telegram error while forwarding file: {str(e)}! Try again! 😅")
            logger.error(f"🚨 Telegram error while forwarding to channel {CHANNEL_ID} for user {user_id}: {str(e)}")
            return

        # Save file metadata
        stored_files = get_setting("stored_files", [])
        file_entry = {
            "file_id": file_id,
            "file_name": file_name,
            "message_id": forwarded_message.message_id,
            "chat_id": CHANNEL_ID,
            "user_id": user_id
        }
        stored_files.append(file_entry)
        set_setting("stored_files", stored_files)

        update.message.reply_text(
            f"✅ File '{file_name}' stored successfully! 📦\n"
            "Use /genlink to create a shareable link for this file, or /batchgen for multiple files! 🔗"
        )
        logger.info(f"✅ User {user_id} stored file '{file_name}'! 🌟")
    except Exception as e:
        update.message.reply_text("⚠️ Failed to store file! Try again! 😅")
        log_error(f"🚨 File store error for user {user_id}: {str(e)}")

def genlink(update: Update, context: CallbackContext):
    """🔗 Generate a shareable link for a single file (GenLink)."""
    user_id = str(update.effective_user.id)
    try:
        stored_files = get_setting("stored_files", [])
        if not stored_files:
            update.message.reply_text("⚠️ No files stored yet! Send a file first! 😅")
            return

        # Show the last 5 stored files by this user
        user_files = [f for f in stored_files if f["user_id"] == user_id][-5:]
        if not user_files:
            update.message.reply_text("⚠️ You haven’t stored any files yet! Send a file first! 😅")
            return

        buttons = [
            [InlineKeyboardButton(f"{f['file_name']}", callback_data=f"genlink_{i}")]
            for i, f in enumerate(user_files)
        ]
        buttons.append([InlineKeyboardButton("Cancel 🚫", callback_data="cancel_genlink")])

        update.message.reply_text(
            "🔗 Choose a file to generate a shareable link! 📦",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        logger.info(f"✅ User {user_id} requested to generate a link! 🌟")
    except Exception as e:
        update.message.reply_text("⚠️ Failed to generate link! Try again! 😅")
        log_error(f"🚨 GenLink error for user {user_id}: {str(e)}")

def handle_genlink_selection(update: Update, context: CallbackContext):
    """🔗 Handle file selection and generate the link (GenLink)."""
    user_id = str(update.effective_user.id)
    try:
        callback_data = update.callback_query.data
        if callback_data == "cancel_genlink":
            update.callback_query.message.reply_text("🚫 Link generation cancelled! 😅")
            return

        file_index = int(callback_data.split("_")[1])
        stored_files = get_setting("stored_files", [])
        user_files = [f for f in stored_files if f["user_id"] == user_id][-5:]
        selected_file = user_files[file_index]

        # Generate a shareable link
        bot_username = context.bot.get_me().username
        link = f"https://t.me/{bot_username}?start=file_{selected_file['message_id']}"

        update.callback_query.message.reply_text(
            f"✅ Shareable link for '{selected_file['file_name']}':\n{link} 🔗"
        )
        logger.info(f"✅ User {user_id} generated link for file '{selected_file['file_name']}'! 🌟")
    except Exception as e:
        update.callback_query.message.reply_text("⚠️ Failed to generate link! Try again! 😅")
        log_error(f"🚨 GenLink selection error for user {user_id}: {str(e)}")

def batchgen(update: Update, context: CallbackContext):
    """📦 Generate a shareable link for multiple files (BatchGen)."""
    user_id = str(update.effective_user.id)
    try:
        stored_files = get_setting("stored_files", [])
        if not stored_files:
            update.message.reply_text("⚠️ No files stored yet! Send a file first! 😅")
            return

        # Show the last 5 stored files by this user
        user_files = [f for f in stored_files if f["user_id"] == user_id][-5:]
        if len(user_files) < 2:
            update.message.reply_text("⚠️ You need at least 2 files to create a batch! Send more files! 😅")
            return

        context.user_data["batch_selection"] = []
        buttons = [
            [InlineKeyboardButton(f"{f['file_name']}", callback_data=f"batch_select_{i}")]
            for i, f in enumerate(user_files)
        ]
        buttons.append([InlineKeyboardButton("Done ✅", callback_data="batch_done")])
        buttons.append([InlineKeyboardButton("Cancel 🚫", callback_data="cancel_batchgen")])

        update.message.reply_text(
            "📦 Select files to include in the batch! Tap 'Done' when finished! ✅",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        logger.info(f"✅ User {user_id} started batch creation! 🌟")
    except Exception as e:
        update.message.reply_text("⚠️ Failed to create batch! Try again! 😅")
        log_error(f"🚨 BatchGen error for user {user_id}: {str(e)}")

def handle_batchgen_selection(update: Update, context: CallbackContext):
    """📦 Handle batch file selection and generate the link (BatchGen)."""
    user_id = str(update.effective_user.id)
    try:
        callback_data = update.callback_query.data
        if callback_data == "cancel_batchgen":
            update.callback_query.message.reply_text("🚫 Batch creation cancelled! 😅")
            context.user_data["batch_selection"] = []
            return

        if callback_data == "batch_done":
            if not context.user_data.get("batch_selection"):
                update.callback_query.message.reply_text("⚠️ No files selected for the batch! 😅")
                return

            stored_files = get_setting("stored_files", [])
            user_files = [f for f in stored_files if f["user_id"] == user_id][-5:]
            selected_indices = context.user_data["batch_selection"]
            selected_files = [user_files[i] for i in selected_indices]

            # Generate a batch ID and save the batch
            batch_id = str(len(get_setting("batches", [])) + 1)
            batch_entry = {"batch_id": batch_id, "files": [f["message_id"] for f in selected_files]}
            batches = get_setting("batches", [])
            batches.append(batch_entry)
            set_setting("batches", batches)

            # Generate a shareable link for the batch
            bot_username = context.bot.get_me().username
            link = f"https://t.me/{bot_username}?start=batch_{batch_id}"

            file_names = [f["file_name"] for f in selected_files]
            update.callback_query.message.reply_text(
                f"✅ Batch link created for files: {', '.join(file_names)} 📦\n{link} 🔗"
            )
            logger.info(f"✅ User {user_id} created batch link for {len(selected_files)} files! 🌟")
            context.user_data["batch_selection"] = []
            return

        # Add file to batch selection
        file_index = int(callback_data.split("_")[2])
        if file_index not in context.user_data["batch_selection"]:
            context.user_data["batch_selection"].append(file_index)
            update.callback_query.answer("✅ File added to batch!")
        else:
            context.user_data["batch_selection"].remove(file_index)
            update.callback_query.answer("✅ File removed from batch!")
    except Exception as e:
        update.callback_query.message.reply_text("⚠️ Failed to create batch! Try again! 😅")
        log_error(f"🚨 BatchGen selection error for user {user_id}: {str(e)}")

def handle_filestore_link(update: Update, context: CallbackContext):
    """🔗 Handle deep links to share files or batches."""
    user_id = str(update.effective_user.id)
    try:
        args = context.args
        if not args:
            return

        link_type, identifier = args[0].split("_", 1)
        if link_type == "file":
            stored_files = get_setting("stored_files", [])
            file_entry = next((f for f in stored_files if str(f["message_id"]) == identifier), None)
            if not file_entry:
                update.message.reply_text("⚠️ File not found! It may have been deleted! 😅")
                return

            context.bot.forward_message(
                chat_id=update.message.chat_id,
                from_chat_id=file_entry["chat_id"],
                message_id=file_entry["message_id"]
            )
            update.message.reply_text(f"✅ Here’s your file: {file_entry['file_name']} 📦")
            logger.info(f"✅ User {user_id} accessed file '{file_entry['file_name']}' via link! 🌟")

        elif link_type == "batch":
            batches = get_setting("batches", [])
            batch_entry = next((b for b in batches if b["batch_id"] == identifier), None)
            if not batch_entry:
                update.message.reply_text("⚠️ Batch not found! It may have been deleted! 😅")
                return

            stored_files = get_setting("stored_files", [])
            for message_id in batch_entry["files"]:
                file_entry = next((f for f in stored_files if str(f["message_id"]) == str(message_id)), None)
                if file_entry:
                    context.bot.forward_message(
                        chat_id=update.message.chat_id,
                        from_chat_id=file_entry["chat_id"],
                        message_id=file_entry["message_id"]
                    )
            update.message.reply_text("✅ Here are your batch files! 📦")
            logger.info(f"✅ User {user_id} accessed batch {identifier} via link! 🌟")

    except Exception as e:
        update.message.reply_text("⚠️ Failed to access file/batch! Try again! 😅")
        log_error(f"🚨 File store link error for user {user_id}: {str(e)}")
