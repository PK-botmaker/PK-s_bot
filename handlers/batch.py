from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
from utils.db_channel import get_setting, set_setting
from utils.logging_utils import log_error
import logging
import json

logger = logging.getLogger(__name__)

def batch(update: Update, context: CallbackContext):
    """📦 Handle batch generation or editing for admins (main bot only)."""
    user_id = update.effective_user.id
    if str(user_id) not in context.bot_data.get("admin_ids", []):
        update.callback_query.answer("🚫 Admins only!")
        log_error(f"🚨 Unauthorized batch access by {user_id}")
        return
    if not context.bot_data.get("is_main_bot", False):
        update.callback_query.answer("🚫 Main bot only!")
        log_error(f"🚨 Unauthorized batch access by {user_id} on clone")
        return

    try:
        callback_data = update.callback_query.data
        if callback_data == "generate_batch":
            context.user_data["awaiting_batch_name"] = "generate"
            update.callback_query.message.reply_text(
                "📦 Send a name for the new batch! (e.g., 'Movie Collection') 📋",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("Cancel 🚫", callback_data="cancel_batch")]
                ])
            )
            logger.info(f"✅ Admin {user_id} started generating batch! 🌟")
        elif callback_data == "edit_batch":
            batches = get_setting("batches", [])
            if not batches:
                update.callback_query.message.reply_text("⚠️ No batches found! Create one first! 😅")
                logger.info(f"✅ Admin {user_id} found no batches to edit! 🌟")
                return
            keyboard = [[InlineKeyboardButton(f"📦 {batch['name']}", callback_data=f"edit_batch_{batch['id']}")] for batch in batches]
            keyboard.append([InlineKeyboardButton("Cancel 🚫", callback_data="cancel_batch")])
            update.callback_query.message.reply_text(
                "📦 Choose a batch to edit! 📋",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            logger.info(f"✅ Admin {user_id} started editing batch! 🌟")
    except Exception as e:
        update.callback_query.message.reply_text("⚠️ Oops! Batch action failed! Try again! 😅")
        log_error(f"🚨 Batch action error for {user_id}: {str(e)}")

def handle_batch_input(update: Update, context: CallbackContext):
    """📝 Handle batch name input for generation."""
    user_id = update.effective_user.id
    if not context.user_data.get("awaiting_batch_name"):
        return
    if str(user_id) not in context.bot_data.get("admin_ids", []):
        update.message.reply_text("🚫 Admins only!")
        log_error(f"🚨 Unauthorized batch input by {user_id}")
        return
    if not context.bot_data.get("is_main_bot", False):
        update.message.reply_text("🚫 Main bot only!")
        log_error(f"🚨 Unauthorized batch input by {user_id} on clone")
        return

    try:
        batch_name = update.message.text.strip()
        if context.user_data["awaiting_batch_name"] == "generate":
            batches = get_setting("batches", [])
            batch_id = str(len(batches) + 1)
            new_batch = {"id": batch_id, "name": batch_name, "files": []}
            batches.append(new_batch)
            set_setting("batches", batches)
            update.message.reply_text(
                f"✅ Batch '{batch_name}' created! 🎉\n"
                "Add files via file uploads! 📤",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("Back to Settings ⚙️", callback_data="settings")]
                ])
            )
            logger.info(f"✅ Admin {user_id} created batch '{batch_name}'! 🌟")
        context.user_data["awaiting_batch_name"] = None
    except Exception as e:
        update.message.reply_text("⚠️ Failed to create batch! Try again! 😅")
        log_error(f"🚨 Batch input error for {user_id}: {str(e)}")

def handle_batch_edit(update: Update, context: CallbackContext):
    """📋 Handle batch editing selection."""
    user_id = update.effective_user.id
    if str(user_id) not in context.bot_data.get("admin_ids", []):
        update.callback_query.answer("🚫 Admins only!")
        log_error(f"🚨 Unauthorized batch edit by {user_id}")
        return
    if not context.bot_data.get("is_main_bot", False):
        update.callback_query.answer("🚫 Main bot only!")
        log_error(f"🚨 Unauthorized batch edit by {user_id} on clone")
        return

    try:
        callback_data = update.callback_query.data
        if callback_data.startswith("edit_batch_"):
            batch_id = callback_data.split("_")[2]
            batches = get_setting("batches", [])
            batch = next((b for b in batches if b["id"] == batch_id), None)
            if not batch:
                update.callback_query.message.reply_text("⚠️ Batch not found! 😅")
                log_error(f"🚨 Batch {batch_id} not found for {user_id}")
                return
            update.callback_query.message.reply_text(
                f"📦 Editing batch '{batch['name']}'! 📋\n"
                "Send a new name to update, or add/remove files via uploads! 📤",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("Back to Settings ⚙️", callback_data="settings")]
                ])
            )
            context.user_data["awaiting_batch_edit"] = batch_id
            logger.info(f"✅ Admin {user_id} started editing batch {batch_id}! 🌟")
    except Exception as e:
        update.callback_query.message.reply_text("⚠️ Failed to edit batch! Try again! 😅")
        log_error(f"🚨 Batch edit error for {user_id}: {str(e)}")

def cancel_batch(update: Update, context: CallbackContext):
    """🚫 Cancel the batch process."""
    user_id = update.effective_user.id
    if str(user_id) not in context.bot_data.get("admin_ids", []):
        update.callback_query.answer("🚫 Admins only!")
        log_error(f"🚨 Unauthorized batch cancel by {user_id}")
        return
    if not context.bot_data.get("is_main_bot", False):
        update.callback_query.answer("🚫 Main bot only!")
        log_error(f"🚨 Unauthorized batch cancel by {user_id} on clone")
        return

    try:
        if context.user_data.get("awaiting_batch_name") or context.user_data.get("awaiting_batch_edit"):
            context.user_data["awaiting_batch_name"] = None
            context.user_data["awaiting_batch_edit"] = None
            update.callback_query.message.reply_text("✅ Batch action cancelled! 🎉")
            logger.info(f"✅ Admin {user_id} cancelled batch action! 🌟")
        else:
            update.callback_query.message.reply_text("⚠️ No batch action to cancel! 😅")
    except Exception as e:
        update.callback_query.message.reply_text("⚠️ Failed to cancel batch! Try again! 😅")
        log_error(f"🚨 Batch cancel error for {user_id}: {str(e)}")
