from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Bot
from telegram.ext import CallbackContext
from telegram.error import TelegramError, Unauthorized, NetworkError, RetryAfter
from utils.db_channel import get_setting, set_setting
from utils.logging_utils import log_error, log_clone_bot
import logging
import os
import time
import re
from datetime import datetime

logger = logging.getLogger(__name__)

def create_clone_bot(update: Update, context: CallbackContext):
    """🤖 Prompt for bot type visibility before creating a new cloned bot (main bot only)."""
    user_id = str(update.effective_user.id)
    if user_id not in context.bot_data.get("admin_ids", []):
        update.callback_query.answer("🚫 Admins only!")
        log_error(f"🚨 Unauthorized clone bot creation by {user_id}")
        return
    if not context.bot_data.get("is_main_bot", False):
        update.callback_query.answer("🚫 Main bot only!")
        log_error(f"🚨 Unauthorized clone bot creation by {user_id} on clone")
        return

    try:
        # Step 1: Prompt for visibility type
        message = update.callback_query.message.reply_text(
            "🤖 Step 1: Choose the visibility for the new cloned bot! 🔒",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔒 Private (Only You)", callback_data="visibility_private")],
                [InlineKeyboardButton("🌍 Public (Everyone)", callback_data="visibility_public")],
                [InlineKeyboardButton("Cancel 🚫", callback_data="cancel_clone")]
            ])
        )
        context.user_data["last_message_id"] = message.message_id
        logger.info(f"✅ Admin {user_id} started cloning bot - selecting visibility! 🌟")
    except Exception as e:
        update.callback_query.message.reply_text("⚠️ Failed to start cloning! Try again! 😅")
        log_error(f"🚨 Clone bot error for {user_id}: {str(e)}")

def handle_visibility_selection(update: Update, context: CallbackContext):
    """🔒 Handle visibility selection and prompt for bot usage."""
    user_id = str(update.effective_user.id)
    if user_id not in context.bot_data.get("admin_ids", []):
        update.callback_query.answer("🚫 Admins only!")
        log_error(f"🚨 Unauthorized visibility selection by {user_id}")
        return
    if not context.bot_data.get("is_main_bot", False):
        update.callback_query.answer("🚫 Main bot only!")
        log_error(f"🚨 Unauthorized visibility selection by {user_id} on clone")
        return

    try:
        callback_data = update.callback_query.data
        if callback_data == "cancel_clone":
            update.callback_query.message.reply_text("🚫 Cloning cancelled! 😅")
            # Delete the prompt message
            if context.user_data.get("last_message_id"):
                context.bot.delete_message(
                    chat_id=update.callback_query.message.chat_id,
                    message_id=context.user_data["last_message_id"]
                )
            logger.info(f"✅ Admin {user_id} cancelled cloning! 🌟")
            return

        # Store visibility selection
        visibility = "private" if callback_data == "visibility_private" else "public"
        context.user_data["new_bot_visibility"] = visibility

        # Delete the previous prompt message
        if context.user_data.get("last_message_id"):
            context.bot.delete_message(
                chat_id=update.callback_query.message.chat_id,
                message_id=context.user_data["last_message_id"]
            )

        # Step 2: Prompt for bot usage with a clearer message
        message = update.callback_query.message.reply_text(
            f"✅ Visibility set to {visibility.upper()}! 🔒\n"
            "🤖 Step 2: Choose the usage for the new cloned bot! 🛠️\n"
            "📦 File Store: Store files and generate links with /genlink and /batchgen\n"
            "🔍 Search Bot: Search content with /search",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📦 File Store (GenLink/Batch)", callback_data="usage_filestore")],
                [InlineKeyboardButton("🔍 Search Bot", callback_data="usage_searchbot")],
                [InlineKeyboardButton("⬅️ Back to Visibility", callback_data="back_to_visibility")],
                [InlineKeyboardButton("Cancel 🚫", callback_data="cancel_clone")]
            ])
        )
        context.user_data["last_message_id"] = message.message_id
        logger.info(f"✅ Admin {user_id} set visibility to {visibility} and awaiting usage selection! 🌟")
    except Exception as e:
        update.callback_query.message.reply_text("⚠️ Failed to set visibility! Try again! 😅")
        log_error(f"🚨 Visibility selection error for {user_id}: {str(e)}")

def handle_usage_selection(update: Update, context: CallbackContext):
    """🛠️ Handle bot usage selection and prompt for bot token."""
    user_id = str(update.effective_user.id)
    if user_id not in context.bot_data.get("admin_ids", []):
        update.callback_query.answer("🚫 Admins only!")
        log_error(f"🚨 Unauthorized usage selection by {user_id}")
        return
    if not context.bot_data.get("is_main_bot", False):
        update.callback_query.answer("🚫 Main bot only!")
        log_error(f"🚨 Unauthorized usage selection by {user_id} on clone")
        return

    try:
        callback_data = update.callback_query.data
        if callback_data == "cancel_clone":
            update.callback_query.message.reply_text("🚫 Cloning cancelled! 😅")
            # Delete the prompt message
            if context.user_data.get("last_message_id"):
                context.bot.delete_message(
                    chat_id=update.callback_query.message.chat_id,
                    message_id=context.user_data["last_message_id"]
                )
            logger.info(f"✅ Admin {user_id} cancelled cloning! 🌟")
            return
        elif callback_data == "back_to_visibility":
            # Go back to visibility selection
            message = update.callback_query.message.reply_text(
                "🤖 Step 1: Choose the visibility for the new cloned bot! 🔒",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔒 Private (Only You)", callback_data="visibility_private")],
                    [InlineKeyboardButton("🌍 Public (Everyone)", callback_data="visibility_public")],
                    [InlineKeyboardButton("Cancel 🚫", callback_data="cancel_clone")]
                ])
            )
            # Delete the previous prompt message
            if context.user_data.get("last_message_id"):
                context.bot.delete_message(
                    chat_id=update.callback_query.message.chat_id,
                    message_id=context.user_data["last_message_id"]
                )
            context.user_data["last_message_id"] = message.message_id
            logger.info(f"✅ Admin {user_id} went back to visibility selection! 🌟")
            return

        # Store usage selection
        usage = "filestore" if callback_data == "usage_filestore" else "searchbot"
        context.user_data["new_bot_usage"] = usage
        context.user_data["awaiting_clone_token"] = True

        # Delete the previous prompt message
        if context.user_data.get("last_message_id"):
            context.bot.delete_message(
                chat_id=update.callback_query.message.chat_id,
                message_id=context.user_data["last_message_id"]
            )

        # Step 3: Prompt for bot token
        message = update.callback_query.message.reply_text(
            f"✅ Usage set to {usage.upper()}! 🛠️\n"
            "🤖 Step 3: Send the Telegram Bot Token for the new cloned bot! 🔑\n"
            "Example: 123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11\n"
            "⚠️ Ensure the bot is started in BotFather (send /start to the bot)!",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⬅️ Back to Usage", callback_data="back_to_usage")],
                [InlineKeyboardButton("Cancel 🚫", callback_data="cancel_clone")]
            ])
        )
        context.user_data["last_message_id"] = message.message_id
        logger.info(f"✅ Admin {user_id} set usage to {usage} and awaiting token! 🌟")
    except Exception as e:
        update.callback_query.message.reply_text("⚠️ Failed to set usage! Try again! 😅")
        log_error(f"🚨 Usage selection error for {user_id}: {str(e)}")

def view_clone_bots(update: Update, context: CallbackContext):
    """🤖 View all cloned bots (main bot only)."""
    user_id = str(update.effective_user.id)
    if user_id not in context.bot_data.get("admin_ids", []):
        update.callback_query.answer("🚫 Admins only!")
        log_error(f"🚨 Unauthorized view clone bots by {user_id}")
        return
    if not context.bot_data.get("is_main_bot", False):
        update.callback_query.answer("🚫 Main bot only!")
        log_error(f"🚨 Unauthorized view clone bots by {user_id} on clone")
        return

    try:
        cloned_bots = get_setting("cloned_bots", [])
        if not cloned_bots:
            update.callback_query.message.reply_text("⚠️ No cloned bots found! Create one first! 😅")
            logger.info(f"✅ Admin {user_id} viewed clone bots - none found! 🌟")
            return
        response = "🤖 Cloned Bots:\n\n" + "\n".join([f"🔑 Token ending: {bot['token'][-4:]} | Visibility: {bot['visibility'].upper()} | Usage: {bot['usage'].upper()} | Standalone: {bot.get('standalone', False)}" for bot in cloned_bots])
        update.callback_query.message.reply_text(response)
        logger.info(f"✅ Admin {user_id} viewed {len(cloned_bots)} cloned bots! 🌟")
    except Exception as e:
        update.callback_query.message.reply_text("⚠️ Failed to view cloned bots! Try again! 😅")
        log_error(f"🚨 View clone bots error for {user_id}: {str(e)}")

def handle_clone_input(update: Update, context: CallbackContext):
    """🤖 Handle bot token input for cloning and start the bot dynamically."""
    from bot import start_cloned_bot, bot_instances  # Moved import inside function to avoid circular import

    user_id = str(update.effective_user.id)
    logger.info(f"ℹ️ Received message from user {user_id}, checking if awaiting token... 🌟")

    # Debug: Log the current state of user_data
    logger.info(f"ℹ️ User data for {user_id}: {context.user_data}")

    if not context.user_data.get("awaiting_clone_token"):
        logger.info(f"⚠️ Admin {user_id} sent message but not in awaiting_clone_token state: {update.message.text}")
        update.message.reply_text("⚠️ Not expecting a token right now! Start the cloning process again with /start! 😅")
        return

    if user_id not in context.bot_data.get("admin_ids", []):
        logger.info(f"🚨 Unauthorized clone input attempt by user {user_id}")
        update.message.reply_text("🚫 Admins only!")
        log_error(f"🚨 Unauthorized clone input by {user_id}")
        return

    if not context.bot_data.get("is_main_bot", False):
        logger.info(f"🚨 Unauthorized clone input attempt by user {user_id} on clone bot")
        update.message.reply_text("🚫 Main bot only!")
        log_error(f"🚨 Unauthorized clone input by {user_id} on clone")
        return

    try:
        token = update.message.text.strip()
        logger.info(f"ℹ️ Token received from user {user_id}: {token[:10]}...{token[-4:]}")

        visibility = context.user_data.get("new_bot_visibility", "public")  # Default to public if not set
        usage = context.user_data.get("new_bot_usage", "searchbot")  # Default to searchbot if not set
        logger.info(f"ℹ️ Visibility: {visibility}, Usage: {usage} for user {user_id}")

        # Enhanced token format validation with regex
        token_pattern = r"^\d+:[A-Za-z0-9_-]+$"
        if not re.match(token_pattern, token):
            logger.info(f"⚠️ Invalid token format provided by user {user_id}: {token}")
            update.message.reply_text(
                "⚠️ Invalid token format! It should look like '123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11'. "
                "Ensure it starts with numbers, followed by a colon, then letters, numbers, or -/_ only. Try again! 😅"
            )
            # Delete the user's message
            context.bot.delete_message(
                chat_id=update.message.chat_id,
                message_id=update.message.message_id
            )
            return

        # Verify token with Telegram API (with enhanced retries and logging)
        max_retries = 3
        base_delay = 2  # Initial retry delay in seconds
        bot_username = None
        logger.info(f"ℹ️ Starting token verification for user {user_id}...")
        bot = Bot(token)
        for attempt in range(max_retries):
            try:
                # Use get_me() to verify the token
                bot_info = bot.get_me()
                bot_username = bot_info.username
                logger.info(f"✅ Token verification successful for bot @{bot_username} with token ending {token[-4:]}")
                break
            except Unauthorized:
                logger.error(f"🚨 Token verification failed for user {user_id}: Unauthorized")
                update.message.reply_text(
                    "⚠️ Token is invalid or revoked! Please check:\n"
                    "1. Did you copy the token correctly from BotFather?\n"
                    "2. Have you sent /start to the bot in Telegram after creating it?\n"
                    "Get a new token from BotFather if needed and try again! 😅"
                )
                log_error(f"🚨 Token verification failed for user {user_id}: Unauthorized - Token may be invalid or bot not started in BotFather")
                # Delete the user's message and prompt
                context.bot.delete_message(
                    chat_id=update.message.chat_id,
                    message_id=update.message.message_id
                )
                if context.user_data.get("last_message_id"):
                    context.bot.delete_message(
                        chat_id=update.message.chat_id,
                        message_id=context.user_data["last_message_id"]
                    )
                return
            except NetworkError as e:
                if attempt == max_retries - 1:
                    logger.error(f"🚨 Token verification failed for user {user_id}: NetworkError after {max_retries} attempts: {str(e)}")
                    update.message.reply_text("⚠️ Network error while verifying token! Check your internet connection or Render environment, then try again! 😅")
                    log_error(f"🚨 Token verification failed for user {user_id}: NetworkError after {max_retries} attempts: {str(e)}")
                    # Delete the user's message and prompt
                    context.bot.delete_message(
                        chat_id=update.message.chat_id,
                        message_id=update.message.message_id
                    )
                    if context.user_data.get("last_message_id"):
                        context.bot.delete_message(
                            chat_id=update.message.chat_id,
                            message_id=context.user_data["last_message_id"]
                        )
                    return
                retry_delay = base_delay * (2 ** attempt)  # Exponential backoff
                logger.warning(f"⚠️ Network error on attempt {attempt + 1} for user {user_id}: {str(e)}, retrying after {retry_delay} seconds...")
                time.sleep(retry_delay)
            except RetryAfter as e:
                delay = e.retry_after + 1
                logger.warning(f"🚨 Rate limit hit for user {user_id}, retrying after {delay} seconds: {str(e)}")
                update.message.reply_text(f"⚠️ Rate limit hit! Retrying after {delay} seconds... ⏳")
                log_error(f"🚨 Rate limit hit for user {user_id}, retrying after {delay} seconds: {str(e)}")
                time.sleep(delay)
            except TelegramError as e:
                logger.error(f"🚨 Token verification failed for user {user_id}: TelegramError: {str(e)}")
                update.message.reply_text(f"⚠️ Telegram error while verifying token: {str(e)}! Try again! 😅")
                log_error(f"🚨 Token verification failed for user {user_id}: TelegramError: {str(e)}")
                # Delete the user's message and prompt
                context.bot.delete_message(
                    chat_id=update.message.chat_id,
                    message_id=update.message.message_id
                )
                if context.user_data.get("last_message_id"):
                    context.bot.delete_message(
                        chat_id=update.message.chat_id,
                        message_id=context.user_data["last_message_id"]
                    )
                return
            except Exceptionraak as e:
                logger.error(f"🚨 Token verification failed for user {user_id}: Unexpected error: {str(e)}")
                update.message.reply_text(f"⚠️ Unexpected error while verifying token: {str(e)}! Try again! 😅")
                log_error(f"🚨 Token verification failed for user {user_id}: Unexpected error: {str(e)}")
                # Delete the user's message and prompt
                context.bot.delete_message(
                    chat_id=update.message.chat_id,
                    message_id=update.message.message_id
                )
                if context.user_data.get("last_message_id"):
                    context.bot.delete_message(
                        chat_id=update.message.chat_id,
                        message_id=context.user_data["last_message_id"]
                    )
                return
        else:
            logger.error(f"🚨 Token verification failed for user {user_id} after {max_retries} attempts")
            update.message.reply_text("⚠️ Failed to verify token after multiple attempts! Check the logs in the Telegram chat (LOG_ID) for details and try again! 😅")
            log_error(f"🚨 Token verification failed for user {user_id} after {max_retries} attempts")
            # Delete the user's message and prompt
            context.bot.delete_message(
                chat_id=update.message.chat_id,
                message_id=update.message.message_id
            )
            if context.user_data.get("last_message_id"):
                context.bot.delete_message(
                    chat_id=update.message.chat_id,
                    message_id=context.user_data["last_message_id"]
                )
            return

        logger.info(f"ℹ️ Token verified, proceeding to clone bot @{bot_username} for user {user_id}...")

        cloned_bots = get_setting("cloned_bots", [])
        # Check if token already exists
        existing_bot = next((bot for bot in cloned_bots if bot["token"] == token), None)
        if existing_bot:
            standalone_status = "running independently" if existing_bot.get("standalone", False) else "managed by Cloner Bot"
            logger.info(f"⚠️ Duplicate token detected for user {user_id}: Bot @{bot_username} already exists ({standalone_status})")
            update.message.reply_text(f"⚠️ This bot token is already added! It’s @{bot_username} ({standalone_status}). Try a different token! 😅")
            # Delete the user's message and prompt
            context.bot.delete_message(
                chat_id=update.message.chat_id,
                message_id=update.message.message_id
            )
            if context.user_data.get("last_message_id"):
                context.bot.delete_message(
                    chat_id=update.message.chat_id,
                    message_id=context.user_data["last_message_id"]
                )
            return

        # Check if this token matches FILESTORE_TOKEN and verify it
        filestore_token = os.getenv("FILESTORE_TOKEN")
        is_standalone = token == filestore_token
        if is_standalone and usage != "filestore":
            logger.info(f"⚠️ FILESTORE_TOKEN mismatch for user {user_id}: Usage {usage} does not match required 'filestore'")
            update.message.reply_text("⚠️ The token matches FILESTORE_TOKEN but usage is not set to File Store! Please set usage to File Store for this token! 😅")
            # Delete the user's message and prompt
            context.bot.delete_message(
                chat_id=update.message.chat_id,
                message_id=update.message.message_id
            )
            if context.user_data.get("last_message_id"):
                context.bot.delete_message(
                    chat_id=update.message.chat_id,
                    message_id=context.user_data["last_message_id"]
                )
            return

        # Store bot with visibility, usage, and standalone status
        cloned_bots.append({
            "token": token,
            "visibility": visibility,
            "usage": usage,
            "owner_id": user_id,
            "standalone": is_standalone
        })
        set_setting("cloned_bots", cloned_bots)
        logger.info(f"ℹ️ Cloned bot stored in database for user {user_id}: @{bot_username}")

        # Get creator's username
        creator_username = update.effective_user.username if update.effective_user.username else "NoUsername"
        logger.info(f"ℹ️ Creator username for user {user_id}: @{creator_username}")

        # Log success to LOG_ID in table format
        creation_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logger.info(f"ℹ️ Logging clone bot success for user {user_id}...")
        log_clone_bot(
            username=creator_username,
            bot_username=bot_username,
            creator_id=user_id,
            creation_date=creation_date,
            visibility=visibility,
            usage=usage
        )

        # Create inline button with the cloned bot's Telegram address
        bot_address = f"https://t.me/{bot_username}"
        inline_button = InlineKeyboardButton(
            text=f"Start @{bot_username} 🚀",
            url=bot_address
        )
        reply_markup = InlineKeyboardMarkup([[inline_button]])

        # Dynamically start the cloned bot (if not standalone)
        if not is_standalone:
            admin_ids = context.bot_data.get("admin_ids", [])
            logger.info(f"ℹ️ Starting cloned bot @{bot_username} for user {user_id}...")
            instance = start_cloned_bot(token, admin_ids)
            if instance:
                bot_instances.append(instance)
                logger.info(f"✅ Cloned bot @{bot_username} started successfully for user {user_id}")
                update.message.reply_text(
                    f"✅ Your bot build for @{creator_username} is successful! 🎉\n"
                    f"Cloned bot: @{bot_username}\n"
                    f"Visibility: {visibility.upper()} 🔒 | Usage: {usage.upper()} 🛠️",
                    reply_markup=reply_markup
                )
            else:
                logger.error(f"⚠️ Failed to start cloned bot @{bot_username} for user {user_id}")
                update.message.reply_text(f"⚠️ Cloned bot @{bot_username} added but failed to start! Check the token or logs in the Telegram chat (LOG_ID)! 😅")
                log_error(f"⚠️ Admin {user_id} added cloned bot @{bot_username} but failed to start, token ending {token[-4:]}")
        else:
            logger.info(f"✅ Cloned bot @{bot_username} added as standalone for user {user_id}")
            update.message.reply_text(
                f"✅ Your bot build for @{creator_username} is successful! 🎉\n"
                f"Cloned bot: @{bot_username} (running independently)\n"
                f"Visibility: {visibility.upper()} 🔒 | Usage: {usage.upper()} 🛠️",
                reply_markup=reply_markup
            )

        # Delete the user's message and prompt
        logger.info(f"ℹ️ Cleaning up messages for user {user_id}...")
        context.bot.delete_message(
            chat_id=update.message.chat_id,
            message_id=update.message.message_id
        )
        if context.user_data.get("last_message_id"):
            context.bot.delete_message(
                chat_id=update.message.chat_id,
                message_id=context.user_data["last_message_id"]
            )

        # Reset user data
        context.user_data["awaiting_clone_token"] = None
        context.user_data["new_bot_visibility"] = None
        context.user_data["new_bot_usage"] = None
        context.user_data["last_message_id"] = None
        logger.info(f"✅ Clone process completed for user {user_id}! 🌟")

    except Exception as e:
        logger.error(f"🚨 Unexpected error in handle_clone_input for user {user_id}: {str(e)}")
        update.message.reply_text("⚠️ Failed to add cloned bot! Check the logs in the Telegram chat (LOG_ID) for details! 😅")
        log_error(f"🚨 Clone input error for {user_id}: {str(e)}")
        # Delete the user's message and prompt
        context.bot.delete_message(
            chat_id=update.message.chat_id,
            message_id=update.message.message_id
        )
        if context.user_data.get("last_message_id"):
            context.bot.delete_message(
                chat_id=update.message.chat_id,
                message_id=context.user_data["last_message_id"]
            )
        # Reset user data in case of error
        context.user_data["awaiting_clone_token"] = None
        context.user_data["new_bot_visibility"] = None
        context.user_data["new_bot_usage"] = None
        context.user_data["last_message_id"] = None
