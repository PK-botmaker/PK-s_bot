from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
import logging

logger = logging.getLogger(__name__)

def start(update: Update, context: CallbackContext) -> None:
    """Handle the /start command and display the appropriate menu."""
    user_id = str(update.effective_user.id)
    admin_ids = context.bot_data.get("admin_ids", [])
    is_main_bot = context.bot_data.get("is_main_bot", False)

    logger.info(f"ℹ️ /start command received from user {user_id} on bot {context.bot.username} (is_main_bot: {is_main_bot})")

    # Check if the user is an admin and if this is the main bot
    if user_id in admin_ids and is_main_bot:
        logger.info(f"ℹ️ User {user_id} identified as admin on main bot. Showing admin menu.")
        keyboard = [
            [
                InlineKeyboardButton("🤖 Clone Bot", callback_data="create_clone_bot"),
                InlineKeyboardButton("📋 View Cloned Bots", callback_data="view_clone_bots"),
            ],
            [
                InlineKeyboardButton("✏️ Set Caption", callback_data="set_custom_caption"),
                InlineKeyboardButton("🔘 Set Buttons", callback_data="set_custom_buttons"),
            ],
            [
                InlineKeyboardButton("📊 Bot Stats", callback_data="bot_stats"),
                InlineKeyboardButton("⚙️ Settings", callback_data="settings"),
            ],
            [
                InlineKeyboardButton("📣 Broadcast", callback_data="broadcast"),
                InlineKeyboardButton("📂 Batch Menu", callback_data="batch_menu"),
            ],
            [
                InlineKeyboardButton("🔗 Shortener", callback_data="shortener"),
                InlineKeyboardButton("📚 Tutorial", callback_data="tutorial"),
            ],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text(
            f"👋 Welcome Admin! @{context.bot.username}\n\n"
            "Choose an option below to manage your bot:",
            reply_markup=reply_markup
        )
    else:
        logger.info(f"ℹ️ User {user_id} is not an admin or not on main bot. Showing user message.")
        update.message.reply_text(
            f"👋 Hello! I'm @{context.bot.username}.\n"
            "I can help you search or store files, depending on my configuration.\n"
            "Use /search to search for content or upload a file to store it."
        )

def settings_menu(update: Update, context: CallbackContext) -> None:
    """Display the settings menu for admins."""
    query = update.callback_query
    query.answer()
    keyboard = [
        [
            InlineKeyboardButton("📢 Add Channel", callback_data="add_channel"),
            InlineKeyboardButton("🚫 Remove Channel", callback_data="remove_channel"),
        ],
        [
            InlineKeyboardButton("🔗 Set Group Link", callback_data="set_group_link"),
            InlineKeyboardButton("📌 Set DB Channel", callback_data="set_db_channel"),
        ],
        [
            InlineKeyboardButton("📋 Set Log Channel", callback_data="set_log_channel"),
            InlineKeyboardButton("🔐 Set Force Sub", callback_data="set_force_sub"),
        ],
        [
            InlineKeyboardButton("💬 Welcome Message", callback_data="welcome_message"),
            InlineKeyboardButton("🗑️ Auto Delete", callback_data="auto_delete"),
        ],
        [
            InlineKeyboardButton("🖼️ Banner", callback_data="banner"),
            InlineKeyboardButton("🌐 Set Webhook", callback_data="set_webhook"),
        ],
        [
            InlineKeyboardButton("🛡️ Anti-Ban", callback_data="anti_ban"),
            InlineKeyboardButton("📦 Enable Redis", callback_data="enable_redis"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(
        text="⚙️ Settings Menu\nChoose an option to configure the bot:",
        reply_markup=reply_markup
    )

def batch_menu(update: Update, context: CallbackContext) -> None:
    """Display the batch menu for admins."""
    query = update.callback_query
    query.answer()
    keyboard = [
        [
            InlineKeyboardButton("📦 Generate Batch", callback_data="generate_batch"),
            InlineKeyboardButton("✏️ Edit Batch", callback_data="edit_batch"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(
        text="📂 Batch Menu\nChoose an option to manage batches:",
        reply_markup=reply_markup
    )

def bot_stats(update: Update, context: CallbackContext) -> None:
    """Display bot statistics for admins."""
    query = update.callback_query
    query.answer()
    stats_message = (
        "📊 Bot Statistics\n\n"
        "🚀 Bot is running smoothly!\n"
        "More stats coming soon..."
    )
    query.edit_message_text(text=stats_message)

def shortener_menu(update: Update, context: CallbackContext) -> None:
    """Display the shortener menu for admins."""
    query = update.callback_query
    query.answer()
    keyboard = [
        [
            InlineKeyboardButton("🔗 Set Shortener", callback_data="shortener"),
            InlineKeyboardButton("🔑 Set API Key", callback_data="set_shortener_api"),
        ],
        [
            InlineKeyboardButton("🗝️ Set Shortener Key", callback_data="set_shortener_key"),
            InlineKeyboardButton("🚫 Disable Shortener", callback_data="disable_shortener"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(
        text="🔗 Shortener Menu\nChoose an option to manage URL shortening:",
        reply_markup=reply_markup
    )
