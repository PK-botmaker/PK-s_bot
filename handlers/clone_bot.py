import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Bot
from telegram.ext import CallbackContext
from utils.db_channel import save_cloned_bot, get_cloned_bots

logger = logging.getLogger(__name__)

def create_clone_bot(update: Update, context: CallbackContext):
    """Initiate the bot cloning process for admins."""
    user_id = str(update.effective_user.id)
    if user_id not in context.bot_data.get("admin_ids", []):
        update.callback_query.answer("🚫 Admins only!")
        logger.info(f"🚫 Unauthorized clone bot attempt by user {user_id}")
        return

    keyboard = [
        [
            InlineKeyboardButton("🔒 Private", callback_data="visibility_private"),
            InlineKeyboardButton("🌐 Public", callback_data="visibility_public")
        ],
        [
            InlineKeyboardButton("❌ Cancel", callback_data="cancel_clone")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    update.callback_query.message.reply_text(
        "🔒 Choose the visibility for the cloned bot:\n- **Private**: Only you can use it.\n- **Public**: Anyone can use it.",
        reply_markup=reply_markup
    )
    logger.info(f"✅ Sent visibility selection to admin {user_id}")

def handle_visibility_selection(update: Update, context: CallbackContext):
    """Handle visibility selection for the cloned bot."""
    query = update.callback_query
    user_id = str(update.effective_user.id)
    if user_id not in context.bot_data.get("admin_ids", []):
        query.answer("🚫 Admins only!")
        logger.info(f"🚫 Unauthorized visibility selection by user {user_id}")
        return

    callback_data = query.data
    if callback_data == "cancel_clone":
        query.message.reply_text("❌ Cloning canceled! 🚫")
        logger.info(f"✅ Cloning canceled by admin {user_id}")
        return

    visibility = "private" if callback_data == "visibility_private" else "public"
    context.user_data["clone_visibility"] = visibility

    keyboard = [
        [
            InlineKeyboardButton("🛠️ Search Bot", callback_data="usage_searchbot"),
            InlineKeyboardButton("📦 File Store", callback_data="usage_filestore")
        ],
        [
            InlineKeyboardButton("❌ Cancel", callback_data="cancel_clone")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    query.message.reply_text(
        "🛠️ Choose the usage type for the cloned bot:\n- **Search Bot**: For searching content.\n- **File Store**: For storing and sharing files.",
        reply_markup=reply_markup
    )
    logger.info(f"✅ Sent usage selection to admin {user_id} with visibility {visibility}")

def handle_usage_selection(update: Update, context: CallbackContext):
    """Handle usage selection for the cloned bot."""
    query = update.callback_query
    user_id = str(update.effective_user.id)
    if user_id not in context.bot_data.get("admin_ids", []):
        query.answer("🚫 Admins only!")
        logger.info(f"🚫 Unauthorized usage selection by user {user_id}")
        return

    callback_data = query.data
    if callback_data == "cancel_clone":
        query.message.reply_text("❌ Cloning canceled! 🚫")
        logger.info(f"✅ Cloning canceled by admin {user_id}")
        return

    usage = "searchbot" if callback_data == "usage_searchbot" else "filestore"
    context.user_data["clone_usage"] = usage

    query.message.reply_text("🔑 Please send the Telegram Bot Token for the bot you want to clone:")
    context.user_data["awaiting_token"] = True
    logger.info(f"ℹ️ Awaiting bot token from admin {user_id} with visibility {context.user_data['clone_visibility']} and usage {usage}")

def handle_clone_input(update: Update, context: CallbackContext):
    """Handle the bot token input and clone the bot."""
    user_id = str(update.effective_user.id)
    if user_id not in context.bot_data.get("admin_ids", []):
        update.message.reply_text("🚫 Admins only!")
        logger.info(f"🚫 Unauthorized token input by user {user_id}")
        return

    if not context.user_data.get("awaiting_token"):
        update.message.reply_text("⚠️ Please start the cloning process first by selecting 'Clone Bots' from the menu! 🤖")
        logger.info(f"⚠️ Unexpected token input from admin {user_id}")
        return

    token = update.message.text.strip()
    logger.info(f"ℹ️ Received token from admin {user_id}: {token[-4:]}")

    # Validate token format (basic check)
    if not token or ":" not in token or len(token.split(":")) != 2:
        update.message.reply_text("❌ Invalid token format! Please send a valid Telegram Bot Token (e.g., 123456:ABC-DEF). 🔑")
        logger.warning(f"⚠️ Invalid token format provided by admin {user_id}: {token[-4:]}")
        return

    # Verify the token by attempting to use it
    try:
        bot = Bot(token)
        bot_info = bot.get_me()
        bot_username = bot_info.username
        logger.info(f"✅ Token verified for bot @{bot_username} with token ending {token[-4:]}")
    except Exception as e:
        update.message.reply_text(f"❌ Failed to verify the token! Error: {str(e)}\nPlease ensure the token is valid and try again. 🔑")
        logger.error(f"🚨 Token verification failed for admin {user_id}: {str(e)} (token ending {token[-4:]})")
        return

    # Save the cloned bot data
    visibility = context.user_data.get("clone_visibility", "public")
    usage = context.user_data.get("clone_usage", "searchbot")
    try:
        save_cloned_bot(user_id, bot_username, token, visibility, usage)
        logger.info(f"✅ Saved cloned bot @{bot_username} for admin {user_id} with visibility {visibility} and usage {usage}")
    except Exception as e:
        update.message.reply_text(f"❌ Failed to save the cloned bot! Error: {str(e)}\nPlease try again later. 🚫")
        logger.error(f"🚨 Failed to save cloned bot for admin {user_id}: {str(e)}")
        return

    # Register the cloned bot
    from bot import start_cloned_bot
    admin_ids = context.bot_data.get("admin_ids", [])
    success = start_cloned_bot(token, admin_ids)
    if not success:
        update.message.reply_text(f"❌ Failed to register the cloned bot! Please try again later. 🚫")
        logger.error(f"🚨 Failed to register cloned bot @{bot_username} for admin {user_id}")
        return

    # Notify the user
    keyboard = [[InlineKeyboardButton(f"🚀 Start @{bot_username}", url=f"https://t.me/{bot_username}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(
        f"✅ Your bot build for @{update.effective_user.username} is successful! 🎉\n"
        f"Cloned bot: @{bot_username}\n"
        f"Visibility: {visibility.upper()} 🔒 | Usage: {usage.upper()} 🛠️",
        reply_markup=reply_markup
    )
    logger.info(f"✅ Successfully cloned bot @{bot_username} for admin {user_id}")

    # Clear the cloning state
    context.user_data.pop("awaiting_token", None)
    context.user_data.pop("clone_visibility", None)
    context.user_data.pop("clone_usage", None)
    logger.info(f"✅ Cleared cloning state for admin {user_id}")

def view_clone_bots(update: Update, context: CallbackContext):
    """Show a list of cloned bots for the admin."""
    user_id = str(update.effective_user.id)
    if user_id not in context.bot_data.get("admin_ids", []):
        update.callback_query.answer("🚫 Admins only!")
        logger.info(f"🚫 Unauthorized view cloned bots attempt by user {user_id}")
        return

    cloned_bots = get_cloned_bots()
    if not cloned_bots:
        update.callback_query.message.reply_text("ℹ️ No cloned bots found! Start by creating a new clone. 🤖")
        logger.info(f"ℹ️ No cloned bots found for admin {user_id}")
        return

    message = "📋 **Cloned Bots List** 📋\n\n"
    for bot in cloned_bots:
        message += (
            f"🤖 Bot: @{bot['username']}\n"
            f"👤 Owner ID: {bot['owner_id']}\n"
            f"🔒 Visibility: {bot['visibility'].upper()}\n"
            f"🛠️ Usage: {bot['usage'].upper()}\n"
            f"📅 Created: {bot.get('created_at', 'N/A')}\n\n"
        )
    update.callback_query.message.reply_text(message)
    logger.info(f"✅ Sent cloned bots list to admin {user_id}")
