import os
import logging
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
from datetime import datetime

logger = logging.getLogger(__name__)

FILES_STORAGE_PATH = "/opt/render/project/src/data/files.json"
SETTINGS_PATH = "/opt/render/project/src/data/settings.json"
CLONED_BOTS_PATH = "/opt/render/project/src/data/cloned_bots.json"

def send_log_to_channel(context: CallbackContext, message: str):
    """Send a log message to the Telegram log channel. 📜"""
    LOG_CHANNEL_ID = os.getenv("LOG_CHANNEL_ID")
    if not LOG_CHANNEL_ID:
        logger.error("🚨 LOG_CHANNEL_ID not set in environment variables")
        return

    try:
        context.bot.send_message(chat_id=LOG_CHANNEL_ID, text=f"📝 {message}")
        logger.info(f"✅ Log sent to channel {LOG_CHANNEL_ID}: {message}")
    except Exception as e:
        logger.error(f"🚨 Failed to send log to channel {LOG_CHANNEL_ID}: {str(e)}")

def log_user_activity(context: CallbackContext, user_id: str, username: str, action: str):
    """Log user activity in a table format to the log channel. 📊"""
    cloned_bots = []
    try:
        with open(CLONED_BOTS_PATH, "r") as f:
            cloned_bots = json.load(f)
    except:
        cloned_bots = []
    user_bots = [bot for bot in cloned_bots if bot["owner_id"] == user_id]
    num_bots = len(user_bots)
    files = []
    try:
        with open(FILES_STORAGE_PATH, "r") as f:
            files = json.load(f)
    except:
        files = []
    total_users = len(get_users())
    
    table = (
        "📊 **User Activity Log** 📊\n\n"
        "┌───────────────────────────────┐\n"
        f"│ 🆔 **User ID**: {user_id}\n"
        f"│ 👤 **Username**: @{username}\n"
        f"│ 🛠️ **Action**: {action}\n"
        f"│ 🤖 **Created Bots**: {num_bots}\n"
        f"│ 📁 **Total Files in Bot**: {len(files)}\n"
        f"│ 👥 **Total Users**: {total_users}\n"
        "└───────────────────────────────┘"
    )
    send_log_to_channel(context, table)

def get_users():
    """Load user IDs from users.json. 👥"""
    try:
        with open("/opt/render/project/src/data/users.json", "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"🚨 Failed to load users: {str(e)}")
        return []

def get_settings():
    """Load bot settings from settings.json. ⚙️"""
    try:
        with open(SETTINGS_PATH, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"🚨 Failed to load settings: {str(e)}")
        return {"force_subscription": False, "search_caption": "🔍 Search Result", "delete_timer": "0m", "forcesub_channels": ["@bot_paiyan_official"]}

def save_settings(settings):
    """Save bot settings to settings.json. 💾"""
    try:
        with open(SETTINGS_PATH, "w") as f:
            json.dump(settings, f, indent=4)
    except Exception as e:
        logger.error(f"🚨 Failed to save settings: {str(e)}")

def get_cloned_bots():
    """Load cloned bots from cloned_bots.json. 🤖"""
    try:
        with open(CLONED_BOTS_PATH, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"🚨 Failed to load cloned bots: {str(e)}")
        return []

def save_cloned_bots(bots):
    """Save cloned bots to cloned_bots.json. 💾"""
    try:
        with open(CLONED_BOTS_PATH, "w") as f:
            json.dump(bots, f, indent=4)
    except Exception as e:
        logger.error(f"🚨 Failed to save cloned bots: {str(e)}")

def is_admin(user_id: str) -> bool:
    """Check if the user is an admin. 🔑"""
    settings = get_settings()
    admin_id = settings.get("admin_id")
    return str(user_id) == str(admin_id)

def clone(update: Update, context: CallbackContext):
    """Clone the bot for a user. 🤖"""
    user_id = str(update.effective_user.id)
    username = update.effective_user.username or "Unknown"

    if not is_admin(user_id):
        update.message.reply_text("🚫 You are not authorized to use this command. 😓")
        send_log_to_channel(context, f"User {user_id} tried to access /clone but is not an admin. 🚫")
        log_user_activity(context, user_id, username, "Tried to Access /clone (Unauthorized)")
        return

    args = context.args
    if len(args) != 2:
        update.message.reply_text("🚫 Please provide a bot token and owner ID.\nExample: /clone <BOT_TOKEN> <OWNER_ID> 😅")
        return

    bot_token = args[0]
    owner_id = args[1]
    logger.info(f"ℹ️ Admin {user_id} cloning bot with token: {bot_token} for owner: {owner_id}")
    send_log_to_channel(context, f"Admin {user_id} initiated bot cloning for owner {owner_id} 🤖")
    log_user_activity(context, user_id, username, f"Initiated Bot Cloning for Owner {owner_id}")

    # Simulate bot cloning (in a real scenario, this would deploy a new bot instance)
    cloned_bots = get_cloned_bots()
    cloned_bot = {
        "token": bot_token,
        "owner_id": owner_id,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    cloned_bots.append(cloned_bot)
    save_cloned_bots(cloned_bots)

    update.message.reply_text(
        f"✅ Bot cloned successfully! 🎉\n\n"
        f"🤖 **Bot Token**: {bot_token}\n"
        f"👤 **Owner ID**: {owner_id}",
        parse_mode="Markdown"
    )
    send_log_to_channel(context, f"Admin {user_id} cloned bot for owner {owner_id} 🤖")
    log_user_activity(context, user_id, username, f"Cloned Bot for Owner {owner_id}")

def settings_menu(update: Update, context: CallbackContext):
    """Display the settings menu for the admin. ⚙️"""
    user_id = str(update.effective_user.id)
    username = update.effective_user.username or "Unknown"

    if not is_admin(user_id):
        update.message.reply_text("🚫 You are not authorized to use this command. 😓")
        send_log_to_channel(context, f"User {user_id} tried to access /settings but is not an admin. 🚫")
        log_user_activity(context, user_id, username, "Tried to Access /settings (Unauthorized)")
        return

    settings = get_settings()
    keyboard = [
        [InlineKeyboardButton("🔒 Toggle Force Subscription", callback_data="toggle_force_sub")],
        [InlineKeyboardButton("⏳ Set Delete Timer", callback_data="set_delete_timer")],
        [InlineKeyboardButton("🔗 Manage Force Sub Channels", callback_data="manage_force_sub_channels")],
        [InlineKeyboardButton("🔧 Set Shortener", callback_data="set_shortener")],
        [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(
        f"⚙️ **Settings Menu** ⚙️\n\n"
        f"🔒 **Force Subscription**: {'Enabled' if settings.get('force_subscription', False) else 'Disabled'}\n"
        f"⏳ **Delete Timer**: {settings.get('delete_timer', '0m')}\n"
        f"🔗 **Force Sub Channels**: {', '.join(settings.get('forcesub_channels', ['@bot_paiyan_official']))}\n"
        f"🔧 **Shortener**: {settings.get('shortener', 'GPLinks')}",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    send_log_to_channel(context, f"Admin {user_id} accessed settings menu ⚙️")
    log_user_activity(context, user_id, username, "Accessed Settings Menu")

def settings_callback(update: Update, context: CallbackContext):
    """Handle settings menu callbacks. 🔄"""
    query = update.callback_query
    user_id = str(query.from_user.id)
    username = query.from_user.username or "Unknown"
    data = query.data

    if not is_admin(user_id):
        query.message.edit_text("🚫 You are not authorized to perform this action. 😓")
        send_log_to_channel(context, f"User {user_id} tried to modify settings but is not an admin. 🚫")
        log_user_activity(context, user_id, username, "Tried to Modify Settings (Unauthorized)")
        return

    settings = get_settings()

    if data == "toggle_force_sub":
        settings["force_subscription"] = not settings.get("force_subscription", False)
        save_settings(settings)
        query.message.edit_text(
            f"✅ Force Subscription {'Enabled' if settings['force_subscription'] else 'Disabled'}! 🎉\n\n"
            f"🔒 **Force Subscription**: {'Enabled' if settings['force_subscription'] else 'Disabled'}\n"
            f"⏳ **Delete Timer**: {settings.get('delete_timer', '0m')}\n"
            f"🔗 **Force Sub Channels**: {', '.join(settings.get('forcesub_channels', ['@bot_paiyan_official']))}\n"
            f"🔧 **Shortener**: {settings.get('shortener', 'GPLinks')}",
            reply_markup=query.message.reply_markup,
            parse_mode="Markdown"
        )
        send_log_to_channel(context, f"Admin {user_id} toggled force subscription to {settings['force_subscription']} 🔒")
        log_user_activity(context, user_id, username, f"Toggled Force Subscription to {settings['force_subscription']}")

    elif data == "set_delete_timer":
        keyboard = [
            [InlineKeyboardButton("0m ⏳", callback_data="set_timer_0m")],
            [InlineKeyboardButton("5m ⏳", callback_data="set_timer_5m")],
            [InlineKeyboardButton("10m ⏳", callback_data="set_timer_10m")],
            [InlineKeyboardButton("1h ⏳", callback_data="set_timer_1h")],
            [InlineKeyboardButton("🔙 Back to Settings", callback_data="back_to_settings")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.message.edit_text(
            "⏳ **Set Delete Timer** ⏳\n\n"
            "Choose a timer for auto-deleting messages:",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        send_log_to_channel(context, f"Admin {user_id} accessed delete timer settings ⏳")
        log_user_activity(context, user_id, username, "Accessed Delete Timer Settings")

    elif data.startswith("set_timer_"):
        timer = data.split("_")[-1]
        settings["delete_timer"] = timer
        save_settings(settings)
        keyboard = [
            [InlineKeyboardButton("🔒 Toggle Force Subscription", callback_data="toggle_force_sub")],
            [InlineKeyboardButton("⏳ Set Delete Timer", callback_data="set_delete_timer")],
            [InlineKeyboardButton("🔗 Manage Force Sub Channels", callback_data="manage_force_sub_channels")],
            [InlineKeyboardButton("🔧 Set Shortener", callback_data="set_shortener")],
            [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_to_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.message.edit_text(
            f"✅ Delete Timer set to {timer}! 🎉\n\n"
            f"🔒 **Force Subscription**: {'Enabled' if settings.get('force_subscription', False) else 'Disabled'}\n"
            f"⏳ **Delete Timer**: {timer}\n"
            f"🔗 **Force Sub Channels**: {', '.join(settings.get('forcesub_channels', ['@bot_paiyan_official']))}\n"
            f"🔧 **Shortener**: {settings.get('shortener', 'GPLinks')}",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        send_log_to_channel(context, f"Admin {user_id} set delete timer to {timer} ⏳")
        log_user_activity(context, user_id, username, f"Set Delete Timer to {timer}")

    elif data == "manage_force_sub_channels":
        keyboard = [
            [InlineKeyboardButton("➕ Add Channel", callback_data="add_force_sub_channel")],
            [InlineKeyboardButton("➖ Remove Channel", callback_data="remove_force_sub_channel")],
            [InlineKeyboardButton("🔙 Back to Settings", callback_data="back_to_settings")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.message.edit_text(
            "🔗 **Manage Force Subscription Channels** 🔗\n\n"
            f"Current Channels: {', '.join(settings.get('forcesub_channels', ['@bot_paiyan_official']))}",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        send_log_to_channel(context, f"Admin {user_id} accessed force sub channel management 🔗")
        log_user_activity(context, user_id, username, "Accessed Force Sub Channel Management")

    elif data == "add_force_sub_channel":
        context.user_data["awaiting_channel"] = "add"
        query.message.edit_text(
            "➕ **Add Force Subscription Channel** ➕\n\n"
            "Please send the channel username (e.g., @channelname):",
            parse_mode="Markdown"
        )
        send_log_to_channel(context, f"Admin {user_id} initiated adding a force sub channel ➕")
        log_user_activity(context, user_id, username, "Initiated Adding a Force Sub Channel")

    elif data == "remove_force_sub_channel":
        context.user_data["awaiting_channel"] = "remove"
        query.message.edit_text(
            "➖ **Remove Force Subscription Channel** ➖\n\n"
            "Please send the channel username to remove (e.g., @channelname):",
            parse_mode="Markdown"
        )
        send_log_to_channel(context, f"Admin {user_id} initiated removing a force sub channel ➖")
        log_user_activity(context, user_id, username, "Initiated Removing a Force Sub Channel")

    elif data == "set_shortener":
        keyboard = [
            [InlineKeyboardButton("🔗 GPLinks", callback_data="set_shortener_GPLinks")],
            [InlineKeyboardButton("❌ None", callback_data="set_shortener_None")],
            [InlineKeyboardButton("🔙 Back to Settings", callback_data="back_to_settings")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.message.edit_text(
            "🔧 **Set URL Shortener** 🔧\n\n"
            "Choose a shortener for download links:",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        send_log_to_channel(context, f"Admin {user_id} accessed shortener settings 🔧")
        log_user_activity(context, user_id, username, "Accessed Shortener Settings")

    elif data.startswith("set_shortener_"):
        shortener = data.split("_")[-1]
        settings["shortener"] = shortener
        save_settings(settings)
        keyboard = [
            [InlineKeyboardButton("🔒 Toggle Force Subscription", callback_data="toggle_force_sub")],
            [InlineKeyboardButton("⏳ Set Delete Timer", callback_data="set_delete_timer")],
            [InlineKeyboardButton("🔗 Manage Force Sub Channels", callback_data="manage_force_sub_channels")],
            [InlineKeyboardButton("🔧 Set Shortener", callback_data="set_shortener")],
            [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_to_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.message.edit_text(
            f"✅ Shortener set to {shortener}! 🎉\n\n"
            f"🔒 **Force Subscription**: {'Enabled' if settings.get('force_subscription', False) else 'Disabled'}\n"
            f"⏳ **Delete Timer**: {settings.get('delete_timer', '0m')}\n"
            f"🔗 **Force Sub Channels**: {', '.join(settings.get('forcesub_channels', ['@bot_paiyan_official']))}\n"
            f"🔧 **Shortener**: {shortener}",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        send_log_to_channel(context, f"Admin {user_id} set shortener to {shortener} 🔧")
        log_user_activity(context, user_id, username, f"Set Shortener to {shortener}")

    elif data == "back_to_settings":
        keyboard = [
            [InlineKeyboardButton("🔒 Toggle Force Subscription", callback_data="toggle_force_sub")],
            [InlineKeyboardButton("⏳ Set Delete Timer", callback_data="set_delete_timer")],
            [InlineKeyboardButton("🔗 Manage Force Sub Channels", callback_data="manage_force_sub_channels")],
            [InlineKeyboardButton("🔧 Set Shortener", callback_data="set_shortener")],
            [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_to_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.message.edit_text(
            f"⚙️ **Settings Menu** ⚙️\n\n"
            f"🔒 **Force Subscription**: {'Enabled' if settings.get('force_subscription', False) else 'Disabled'}\n"
            f"⏳ **Delete Timer**: {settings.get('delete_timer', '0m')}\n"
            f"🔗 **Force Sub Channels**: {', '.join(settings.get('forcesub_channels', ['@bot_paiyan_official']))}\n"
            f"🔧 **Shortener**: {settings.get('shortener', 'GPLinks')}",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        send_log_to_channel(context, f"Admin {user_id} returned to settings menu ⚙️")
        log_user_activity(context, user_id, username, "Returned to Settings Menu")

    elif data == "back_to_main":
        keyboard = [
            [InlineKeyboardButton("🔍 Search Files", callback_data="search_info")],
            [InlineKeyboardButton("ℹ️ About Bot", callback_data="about_bot")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.message.edit_text(
            "🎉 **Welcome to TamilSender Bot!** 🎉\n\n"
            "🔍 Use /search to find files\n"
            "📤 Use /upload to upload files\n"
            "📁 Use /get to retrieve a file by ID\n"
            "📦 Use /batch to get a range of files\n"
            "🔗 Use /genlink to generate a link\n"
            "📢 Use /batchgen for batch links\n\n"
            "👇 **Choose an option below** 👇",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        send_log_to_channel(context, f"Admin {user_id} returned to main menu 🏁")
        log_user_activity(context, user_id, username, "Returned to Main Menu")

def handle_channel_input(update: Update, context: CallbackContext):
    """Handle input for adding/removing force subscription channels. 🔗"""
    user_id = str(update.effective_user.id)
    username = update.effective_user.username or "Unknown"
    action = context.user_data.get("awaiting_channel")

    if not action:
        return

    if not is_admin(user_id):
        update.message.reply_text("🚫 You are not authorized to perform this action. 😓")
        send_log_to_channel(context, f"User {user_id} tried to modify force sub channels but is not an admin. 🚫")
        log_user_activity(context, user_id, username, "Tried to Modify Force Sub Channels (Unauthorized)")
        return

    channel = update.message.text.strip()
    if not channel.startswith("@"):
        channel = f"@{channel}"

    settings = get_settings()
    forcesub_channels = settings.get("forcesub_channels", ["@bot_paiyan_official"])

    if action == "add":
        if channel in forcesub_channels:
            update.message.reply_text(f"🚫 Channel {channel} is already in the list. 😓")
            send_log_to_channel(context, f"Admin {user_id} tried to add duplicate channel {channel} 🚫")
            log_user_activity(context, user_id, username, f"Tried to Add Duplicate Channel {channel}")
        else:
            forcesub_channels.append(channel)
            settings["forcesub_channels"] = forcesub_channels
            save_settings(settings)
            update.message.reply_text(f"✅ Channel {channel} added to force subscription! 🎉")
            send_log_to_channel(context, f"Admin {user_id} added channel {channel} to force subscription 🔗")
            log_user_activity(context, user_id, username, f"Added Channel {channel} to Force Subscription")

    elif action == "remove":
        if channel not in forcesub_channels:
            update.message.reply_text(f"🚫 Channel {channel} is not in the list. 😓")
            send_log_to_channel(context, f"Admin {user_id} tried to remove non-existent channel {channel} 🚫")
            log_user_activity(context, user_id, username, f"Tried to Remove Non-Existent Channel {channel}")
        else:
            forcesub_channels.remove(channel)
            settings["forcesub_channels"] = forcesub_channels
            save_settings(settings)
            update.message.reply_text(f"✅ Channel {channel} removed from force subscription! 🎉")
            send_log_to_channel(context, f"Admin {user_id} removed channel {channel} from force subscription 🔗")
            log_user_activity(context, user_id, username, f"Removed Channel {channel} from Force Subscription")

    context.user_data.pop("awaiting_channel", None)
    keyboard = [
        [InlineKeyboardButton("➕ Add Channel", callback_data="add_force_sub_channel")],
        [InlineKeyboardButton("➖ Remove Channel", callback_data="remove_force_sub_channel")],
        [InlineKeyboardButton("🔙 Back to Settings", callback_data="back_to_settings")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(
        "🔗 **Manage Force Subscription Channels** 🔗\n\n"
        f"Current Channels: {', '.join(settings.get('forcesub_channels', ['@bot_paiyan_official']))}",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
