from telegram import Update
from telegram.ext import CallbackContext
from utils.db_channel import get_setting
from utils.logging_utils import log_error
import logging

logger = logging.getLogger(__name__)

def search(update: Update, context: CallbackContext):
    """🔍 Search for files based on user query."""
    user_id = update.effective_user.id
    query = update.message.text.replace("/search", "").strip()

    try:
        if not query:
            update.message.reply_text("🔍 Please provide a search term! (e.g., /search movie)")
            logger.info(f"⚠️ User {user_id} sent empty search query")
            return

        files = get_setting("files", {})
        matching_files = [name for name, data in files.items() if query.lower() in name.lower()]
        
        if not matching_files:
            update.message.reply_text("⚠️ No files found for your search! Try another term! 😅")
            logger.info(f"✅ User {user_id} searched for '{query}' - no results")
            return

        response = "🔍 Search Results:\n\n" + "\n".join([f"📄 {file}" for file in matching_files])
        update.message.reply_text(response)
        logger.info(f"✅ User {user_id} searched for '{query}' - found {len(matching_files)} results! 🌟")
    except Exception as e:
        update.message.reply_text("⚠️ Failed to search files! Try again! 😅")
        log_error(f"🚨 Search error for user {user_id}: {str(e)}")
