import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
from utils.db_channel import get_cloned_bots

logger = logging.getLogger(__name__)

def start(update: Update, context: CallbackContext):
    """Start command handler with admin features for main bot."""
    logger.info(f"ℹ️ Start command received from user {update.effective_user.id} for bot {context.bot.username}")

    user_id = str(update.effective_user.id)
    is_admin = user_id in context.bot_data.get("admin_ids", [])
    is_main_bot = context.bot_data.get("is_main_bot", False)

    if not is_main_bot and not is_admin:
        # Non-admin user on a cloned bot
        welcome_msg = (
            "👋 Welcome to the Bot! 🤖\n\n"
            "I can help you with the following:\n"
            "- Use /search to search for content (if enabled).\n"
            "- Upload files to store and generate links (if enabled).\n"
            "- Use /genlink to generate a link for a file.\n"
            "- Use /batchgen to generate links for multiple files.\n"
            "Let's get started! 🚀"
        )
        update.message.reply_text(welcome_msg)
        logger.info(f"✅ Sent welcome message to non-admin user {user_id} on bot {context.bot.username}")
        return

    # Admin user or main bot
    keyboard = [
        [
            InlineKeyboardButton("🤖 Clone Bots", callback_data="create_clone_bot"),
            InlineKeyboardButton("📋 View Cloned Bots", callback_data="view_clone_bots")
        ],
        [
            InlineKeyboardButton("✏️ Custom Caption", callback_data="set_custom_caption"),
            InlineKeyboardButton("🔳 Custom Buttons", callback_data="set_custom_buttons")
        ],
        [
            InlineKeyboardButton("📚 Tutorial", callback_data="tutorial"),
            InlineKeyboardButton("⚙️ Settings", callback_data="settings")
        ],
        [
            InlineKeyboardButton("📦 Batch Menu", callback_data="batch_menu"),
            InlineKeyboardButton("📊 Bot Stats", callback_data="bot_stats")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    welcome_msg = (
        "👋 Welcome to the Cloner Bot Admin Panel! 🤖\n\n"
        "Here’s what you can do:\n"
        "- 🤖 **Clone Bots**: Create a new bot by cloning.\n"
        "- 📋 **View Cloned Bots**: See all your cloned bots.\n"
        "- ✏️ **Custom Caption**: Set a custom caption for shared content.\n"
        "- 🔳 **Custom Buttons**: Add custom inline buttons.\n"
        "- 📚 **Tutorial**: Learn how to use the bot.\n"
        "- ⚙️ **Settings**: Configure bot settings.\n"
        "- 📦 **Batch Menu**: Manage batch file operations.\n"
        "- 📊 **Bot Stats**: Check bot usage statistics.\n"
        "Choose an option below to get started! 🚀"
    )
    update.message.reply_text(welcome_msg, reply_markup=reply_markup)
    logger.info(f"✅ Sent admin panel to user {user_id} on bot {context.bot.username}")

def settings_menu(update: Update, context: CallbackContext):
    """Show settings menu for admins."""
    user_id = str(update.effective_user.id)
    if user_id not in context.bot_data.get("admin_ids", []):
        update.callback_query.answer("🚫 Admins only!")
        logger.info(f"🚫 Unauthorized settings access attempt by user {user_id}")
        return

    keyboard = [
        [
            InlineKeyboardButton("➕ Add Channel", callback_data="add_channel"),
            InlineKeyboardButton("➖ Remove Channel", callback_data="remove_channel")
        ],
        [
            InlineKeyboardButton("🔗 Set Force Sub", callback_data="set_force_sub"),
            InlineKeyboardButton("🌐 Set Group Link", callback_data="set_group_link")
        ],
        [
            InlineKeyboardButton("📂 Set DB Channel", callback_data="set_db_channel"),
            InlineKeyboardButton("📜 Set Log Channel", callback_data="set_log_channel")
        ],
        [
            InlineKeyboardButton("🔗 Shortener", callback_data="shortener"),
            InlineKeyboardButton("💬 Welcome Message", callback_data="welcome_message")
        ],
        [
            InlineKeyboardButton("🗑️ Auto Delete", callback_data="auto_delete"),
            InlineKeyboardButton("🖼️ Banner", callback_data="banner")
        ],
        [
            InlineKeyboardButton("🌐 Set Webhook", callback_data="set_webhook"),
            InlineKeyboardButton("🛡️ Anti-Ban", callback_data="anti_ban")
        ],
        [
            InlineKeyboardButton("🗄️ Enable Redis", callback_data="enable_redis")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    update.callback_query.message.reply_text(
        "⚙️ Settings Menu:\nChoose an option to configure the bot! 🚀",
        reply_markup=reply_markup
    )
    logger.info(f"✅ Sent settings menu to admin {user_id}")

def shortener_menu(update: Update, context: CallbackContext):
    """Show URL shortener settings menu for admins."""
    user_id = str(update.effective_user.id)
    if user_id not in context.bot_data.get("admin_ids", []):
        update.callback_query.answer("🚫 Admins only!")
        logger.info(f"🚫 Unauthorized shortener menu access attempt by user {user_id}")
        return

    keyboard = [
        [
            InlineKeyboardButton("🔗 Set Shortener API", callback_data="set_shortener_api"),
            InlineKeyboardButton("🔑 Set API Key", callback_data="set_shortener_key")
        ],
        [
            InlineKeyboardButton("❌ Disable Shortener", callback_data="disable_shortener")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    update.callback_query.message.reply_text(
        "🔗 URL Shortener Settings:\nChoose an option to configure the shortener! 🚀",
        reply_markup=reply_markup
    )
    logger.info(f"✅ Sent shortener menu to admin {user_id}")

def batch_menu(update: Update, context: CallbackContext):
    """Show batch menu for admins."""
    user_id = str(update.effective_user.id)
    if user_id not in context.bot_data.get("admin_ids", []):
        update.callback_query.answer("🚫 Admins only!")
        logger.info(f"🚫 Unauthorized batch menu access attempt by user {user_id}")
        return

    keyboard = [
        [
            InlineKeyboardButton("📦 Generate Batch", callback_data="generate_batch"),
            InlineKeyboardButton("✏️ Edit Batch", callback_data="edit_batch")
        ],
        [
            InlineKeyboardButton("📣 Broadcast", callback_data="broadcast")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    update.callback_query.message.reply_text(
        "📦 Batch Menu:\nChoose an option to manage batch operations! 🚀",
        reply_markup=reply_markup
    )
    logger.info(f"✅ Sent batch menu to admin {user_id}")

def bot_stats(update: Update, context: CallbackContext):
    """Show bot statistics for admins."""
    user_id = str(update.effective_user.id)
    if user_id not in context.bot_data.get("admin_ids", []):
        update.callback_query.answer("🚫 Admins only!")
        logger.info(f"🚫 Unauthorized bot stats access attempt by user {user_id}")
        return

    cloned_bots = get_cloned_bots()
    stats_msg = (
        "📊 Bot Statistics:\n\n"
        f"🤖 Total Cloned Bots: {len(cloned_bots)}\n"
        f"👑 Admin ID: {user_id}\n"
        "More stats coming soon! 🚀"
    )
    update.callback_query.message.reply_text(stats_msg)
    logger.info(f"✅ Sent bot stats to admin {user_id}")
