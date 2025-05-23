from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
import logging

logger = logging.getLogger(__name__)

def start(update: Update, context: CallbackContext):
    """Handle the /start command with admin and user menus."""
    user_id = str(update.effective_user.id)
    chat_id = update.effective_chat.id
    admin_ids = context.bot_data.get("admin_ids", [])
    is_main_bot = context.bot_data.get("is_main_bot", False)

    # Check if db_channel_id is set
    from utils.db_channel import get_setting
    db_channel_id = get_setting("db_channel_id")

    if user_id in admin_ids and is_main_bot:
        # Admin menu for the main bot
        keyboard = [
            [InlineKeyboardButton("🤖 Clone Bot", callback_data="create_clone_bot"),
             InlineKeyboardButton("📋 View Cloned Bots", callback_data="view_clone_bots")],
            [InlineKeyboardButton("📝 Set Custom Caption", callback_data="set_custom_caption"),
             InlineKeyboardButton("🔳 Set Custom Buttons", callback_data="set_custom_buttons")],
            [InlineKeyboardButton("⚙️ Settings", callback_data="settings"),
             InlineKeyboardButton("📊 Bot Stats", callback_data="bot_stats")],
            [InlineKeyboardButton("📣 Broadcast", callback_data="broadcast"),
             InlineKeyboardButton("📦 Batch Menu", callback_data="batch_menu")],
            [InlineKeyboardButton("📖 Tutorial", callback_data="tutorial"),
             InlineKeyboardButton("🔗 Shortener", callback_data="shortener")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        welcome_msg = "👋 Welcome to the Admin Panel! 🌟\n\nChoose an option below to manage your bot:"
        if not db_channel_id:
            welcome_msg += "\n\n⚠️ **Important**: The Database Channel ID is not set. Please set it in the Settings menu to enable cloned bots!"
        update.message.reply_text(welcome_msg, reply_markup=reply_markup)
        logger.info(f"✅ Admin menu sent to user {user_id} in chat {chat_id}")
    else:
        # User menu for non-admins or cloned bots
        keyboard = [
            [InlineKeyboardButton("📖 Tutorial", callback_data="tutorial")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text(
            "👋 Welcome to the Bot! 🌟\n\nI can help you search or store files. Use the commands below to get started!",
            reply_markup=reply_markup
        )
        logger.info(f"✅ User menu sent to user {user_id} in chat {chat_id}")

# ... (rest of the file remains the same)
