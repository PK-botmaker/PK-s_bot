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

def settings_menu(update: Update, context: CallbackContext):
    """Display the settings menu for the admin."""
    query = update.callback_query
    query.answer()

    keyboard = [
        [InlineKeyboardButton("📢 Add Channel", callback_data="add_channel"),
         InlineKeyboardButton("🚫 Remove Channel", callback_data="remove_channel")],
        [InlineKeyboardButton("🔗 Set Group Link", callback_data="set_group_link"),
         InlineKeyboardButton("📜 Set DB Channel", callback_data="set_db_channel")],
        [InlineKeyboardButton("📋 Set Log Channel", callback_data="set_log_channel"),
         InlineKeyboardButton("🔒 Set Force Sub", callback_data="set_force_sub")],
        [InlineKeyboardButton("🖼️ Set Banner", callback_data="banner"),
         InlineKeyboardButton("🕒 Auto Delete", callback_data="auto_delete")],
        [InlineKeyboardButton("👋 Welcome Message", callback_data="welcome_message"),
         InlineKeyboardButton("🔗 Shortener", callback_data="shortener")],
        [InlineKeyboardButton("🚫 Anti-Ban", callback_data="anti_ban"),
         InlineKeyboardButton("🔄 Enable Redis", callback_data="enable_redis")],
        [InlineKeyboardButton("⬅️ Back", callback_data="start")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(
        text="⚙️ **Settings Menu** ⚙️\n\nChoose an option to configure your bot:",
        reply_markup=reply_markup
    )
    logger.info("✅ Settings menu displayed for admin")

def batch_menu(update: Update, context: CallbackContext):
    """Display the batch menu for the admin."""
    query = update.callback_query
    query.answer()

    keyboard = [
        [InlineKeyboardButton("📦 Generate Batch", callback_data="generate_batch"),
         InlineKeyboardButton("✏️ Edit Batch", callback_data="edit_batch")],
        [InlineKeyboardButton("⬅️ Back", callback_data="start")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(
        text="📦 **Batch Menu** 📦\n\nChoose an option to manage batches:",
        reply_markup=reply_markup
    )
    logger.info("✅ Batch menu displayed for admin")

def bot_stats(update: Update, context: CallbackContext):
    """Display bot statistics for the admin."""
    query = update.callback_query
    query.answer()

    # Placeholder for bot stats (you can expand this with actual stats)
    stats_msg = (
        "📊 **Bot Statistics** 📊\n\n"
        "👥 Total Users: Not implemented\n"
        "📂 Files Stored: Not implemented\n"
        "🤖 Cloned Bots: Not implemented\n\n"
        "More stats coming soon! 🚀"
    )
    keyboard = [
        [InlineKeyboardButton("⬅️ Back", callback_data="start")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(
        text=stats_msg,
        reply_markup=reply_markup
    )
    logger.info("✅ Bot stats displayed for admin")

def shortener_menu(update: Update, context: CallbackContext):
    """Display the URL shortener settings menu for the admin."""
    query = update.callback_query
    query.answer()

    keyboard = [
        [InlineKeyboardButton("🔗 Set Shortener", callback_data="set_shortener_api"),
         InlineKeyboardButton("🔑 Set Shortener Key", callback_data="set_shortener_key")],
        [InlineKeyboardButton("🚫 Disable Shortener", callback_data="disable_shortener")],
        [InlineKeyboardButton("⬅️ Back", callback_data="start")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(
        text="🔗 **URL Shortener Settings** 🔗\n\nChoose an option to manage the URL shortener:",
        reply_markup=reply_markup
    )
    logger.info("✅ Shortener menu displayed for admin")
