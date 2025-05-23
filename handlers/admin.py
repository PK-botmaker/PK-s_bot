import os
import logging
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Bot
from telegram.ext import CallbackContext
from datetime import datetime

logger = logging.getLogger(__name__)

CLONED_BOTS_PATH = "/opt/render/project/src/data/cloned_bots.json"
SETTINGS_PATH = "/opt/render/project/src/data/settings.json"
USERS_PATH = "/opt/render/project/src/data/users.json"
ADMINS_PATH = "/opt/render/project/src/data/admins.json"

# Compulsory channel 🔒
COMPULSORY_CHANNEL = "@bot_paiyan_official"

# Initialize settings and users files 📂
if not os.path.exists(SETTINGS_PATH):
    with open(SETTINGS_PATH, "w") as f:
        json.dump({
            "force_subscription": False,
            "search_caption": "🔍 Search Result",
            "shortener": "GPLinks",
            "delete_timer": "0m",
            "forcesub_channels": [COMPULSORY_CHANNEL]
        }, f)

if not os.path.exists(USERS_PATH):
    with open(USERS_PATH, "w") as f:
        json.dump([], f)

def get_cloned_bots():
    """Load cloned bots from cloned_bots.json. 🤖"""
    try:
        with open(CLONED_BOTS_PATH, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"🚨 Failed to load cloned bots: {str(e)}")
        return []

def save_cloned_bots(cloned_bots):
    """Save cloned bots to cloned_bots.json. 💾"""
    try:
        with open(CLONED_BOTS_PATH, "w") as f:
            json.dump(cloned_bots, f, indent=4)
    except Exception as e:
        logger.error(f"🚨 Failed to save cloned bots: {str(e)}")

def get_settings():
    """Load bot settings from settings.json. ⚙️"""
    try:
        with open(SETTINGS_PATH, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"🚨 Failed to load settings: {str(e)}")
        return {"force_subscription": False, "search_caption": "🔍 Search Result", "shortener": "GPLinks", "delete_timer": "0m", "forcesub_channels": [COMPULSORY_CHANNEL]}

def save_settings(settings):
    """Save bot settings to settings.json. 💾"""
    try:
        with open(SETTINGS_PATH, "w") as f:
            json.dump(settings, f, indent=4)
    except Exception as e:
        logger.error(f"🚨 Failed to save settings: {str(e)}")

def get_users():
    """Load user IDs from users.json. 👥"""
    try:
        with open(USERS_PATH, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"🚨 Failed to load users: {str(e)}")
        return []

def save_users(users):
    """Save user IDs to users.json. 💾"""
    try:
        with open(USERS_PATH, "w") as f:
            json.dump(users, f, indent=4)
    except Exception as e:
        logger.error(f"🚨 Failed to save users: {str(e)}")

def add_user(user_id):
    """Add a user ID to users.json if not already present. ➕"""
    users = get_users()
    if str(user_id) not in users:
        users.append(str(user_id))
        save_users(users)

def get_admins():
    """Load admin IDs from admins.json. 🔑"""
    try:
        with open(ADMINS_PATH, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"🚨 Failed to load admins: {str(e)}")
        return []

def save_admins(admins):
    """Save admin IDs to admins.json. 💾"""
    try:
        with open(ADMINS_PATH, "w") as f:
            json.dump(admins, f, indent=4)
    except Exception as e:
        logger.error(f"🚨 Failed to save admins: {str(e)}")

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
    cloned_bots = get_cloned_bots()
    user_bots = [bot for bot in cloned_bots if bot["owner_id"] == user_id]
    num_bots = len(user_bots)
    files = []
    try:
        with open("/opt/render/project/src/data/files.json", "r") as f:
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

def start(update: Update, context: CallbackContext):
    """Handle /start command to show admin menu or welcome message with About button for cloned bots. 👋"""
    user_id = str(update.effective_user.id)
    username = update.effective_user.username or "Unknown"

    # Add user to users.json for broadcasting ➕
    add_user(user_id)

    # Set the first user as admin if no admins exist 🔑
    admins = get_admins()
    if not admins:
        admins.append(user_id)
        save_admins(admins)
        logger.info(f"✅ User {user_id} set as the first admin 🎉")
        send_log_to_channel(context, f"User {user_id} set as the first admin. 🎊")

    context.bot_data["admin_ids"] = admins

    # Check subscription to all force subscription channels 🔒
    settings = get_settings()
    forcesub_channels = settings.get("forcesub_channels", [COMPULSORY_CHANNEL])
    if settings.get("force_subscription", False):
        keyboard = []
        for channel in forcesub_channels:
            try:
                chat_id = channel if channel.startswith("@") else f"@{channel}"
                member = context.bot.get_chat_member(chat_id=chat_id, user_id=user_id)
                if member.status in ["left", "kicked"]:
                    keyboard.append([InlineKeyboardButton(f"🔗 Join {chat_id} 🌟", url=f"https://t.me/{chat_id[1:]}")])
            except Exception as e:
                update.message.reply_text(f"🚫 Error checking membership for {chat_id}. Please try again. 😓")
                send_log_to_channel(context, f"Error checking membership for user {user_id} in {chat_id}: {str(e)}")
                return

        if keyboard:
            reply_markup = InlineKeyboardMarkup(keyboard)
            update.message.reply_text("🚫 You must join the following channels to use this bot! 🔗", reply_markup=reply_markup)
            send_log_to_channel(context, f"User {user_id} denied access - not subscribed to required channels. 🚫")
            return

    # Check if this is a cloned bot 🤖
    cloned_bots = get_cloned_bots()
    bot_token = context.bot.token
    is_cloned = any(bot["token"] == bot_token for bot in cloned_bots)

    if user_id in admins and not is_cloned:
        keyboard = [
            [InlineKeyboardButton("🤖 Clone Bot 🛠️", callback_data="clone_bot_menu"),
             InlineKeyboardButton("📢 Broadcast 📣", callback_data="broadcast")],
            [InlineKeyboardButton("📊 Bot Stats 📈", callback_data="bot_stats"),
             InlineKeyboardButton("⚙️ Settings 🔧", callback_data="settings_menu")],
            [InlineKeyboardButton("📦 Batch Menu 📁", callback_data="batch_menu"),
             InlineKeyboardButton("🔗 Shortener 🔗", callback_data="shortener_menu")],
            [InlineKeyboardButton("📝 Tutorial 📚", callback_data="tutorial")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text("👋 Welcome, Admin! What would you like to do? 🚀", reply_markup=reply_markup)
        send_log_to_channel(context, f"Admin {user_id} accessed the admin menu. ⚙️")
        log_user_activity(context, user_id, username, "Accessed Admin Menu")
    else:
        keyboard = [[InlineKeyboardButton("ℹ️ About This Bot 📖", callback_data="about_cloned_bot")]]
        if is_cloned:
            bot_type = next(bot["type"] for bot in cloned_bots if bot["token"] == bot_token)
            welcome_text = f"👋 Welcome to the {bot_type.capitalize()} Bot! 🌟\nUse /search <query> to find files 🔍" if bot_type == "searchbot" else f"👋 Welcome to the {bot_type.capitalize()} Bot! 🌟\nUse /upload to store files 📤"
        else:
            welcome_text = "👋 Welcome to the Search Bot! 🌟\nUse /search <query> to find files, or join our group to search! 🔍"
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text(welcome_text, reply_markup=reply_markup)
        send_log_to_channel(context, f"User {user_id} started the bot. 🎉")
        log_user_activity(context, user_id, username, "Started Bot")

def about_cloned_bot(update: Update, context: CallbackContext):
    """Show the About section for cloned bots. ℹ️"""
    user_id = str(update.effective_user.id)
    bot_token = context.bot.token
    cloned_bots = get_cloned_bots()
    bot_info = next((bot for bot in cloned_bots if bot["token"] == bot_token), None)

    if not bot_info:
        update.callback_query.message.edit_text("🚫 This bot is not a cloned bot. 😓")
        return

    owner_id = bot_info.get("owner_id")
    bot_type = bot_info.get("type")
    visibility = bot_info.get("visibility")
    created_at = bot_info.get("created_at")

    about_text = (
        "📖 **About This Bot** 📖\n\n"
        f"👤 **My Owner**: User ID {owner_id} 🌟\n"
        f"🧑‍💻 **Developer**: @Dhileep_S 💻\n"
        f"🤖 **Cloned From**: @tamilsender_bot 🔗\n"
        f"🇮🇳 **Language**: Tamil (Tanglish) 🗣️\n"
        f"🛠️ **Bot Type**: {bot_type.capitalize()} ⚙️\n"
        f"🔐 **Visibility**: {visibility.capitalize()} 🔒\n"
        f"🕒 **Created On**: {created_at} ⏳"
    )
    keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="back_to_main")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.callback_query.message.edit_text(about_text, reply_markup=reply_markup, parse_mode="Markdown")
    send_log_to_channel(context, f"User {user_id} viewed the About section of a cloned bot. ℹ️")

def clone_bot_menu(update: Update, context: CallbackContext):
    """Show the Clone Bot sub-menu. 🤖"""
    user_id = str(update.effective_user.id)
    username = update.effective_user.username or "Unknown"
    admin_ids = context.bot_data.get("admin_ids", [])

    if user_id not in admin_ids:
        update.callback_query.message.reply_text("🚫 Only admins can access the clone bot menu. 😞")
        send_log_to_channel(context, f"User {user_id} denied access to clone bot menu - not an admin. 🚫")
        return

    keyboard = [
        [InlineKeyboardButton("➕ Create Clone Bot 🆕", callback_data="create_clone_bot"),
         InlineKeyboardButton("📋 View Clone Bots 👀", callback_data="view_clone_bots")],
        [InlineKeyboardButton("🗑️ Delete Clone Bot 🗑️", callback_data="delete_clone_bot")],
        [InlineKeyboardButton("🔙 Back 🔄", callback_data="back_to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.callback_query.message.edit_text("🤖 Clone Bot Menu: 🛠️", reply_markup=reply_markup)
    send_log_to_channel(context, f"Admin {user_id} accessed the clone bot menu. ⚙️")
    log_user_activity(context, user_id, username, "Accessed Clone Bot Menu")

def settings_menu(update: Update, context: CallbackContext):
    """Show the Settings sub-menu. ⚙️"""
    user_id = str(update.effective_user.id)
    username = update.effective_user.username or "Unknown"
    admin_ids = context.bot_data.get("admin_ids", [])

    if user_id not in admin_ids:
        update.callback_query.message.reply_text("🚫 Only admins can access settings. 😞")
        send_log_to_channel(context, f"User {user_id} denied access to settings menu - not an admin. 🚫")
        return

    settings = get_settings()
    force_sub_status = "✅ On" if settings.get("force_subscription", False) else "❌ Off"
    delete_timer = settings.get("delete_timer", "0m")
    keyboard = [
        [InlineKeyboardButton(f"🔒 Force Subscription: {force_sub_status}", callback_data="toggle_force_subscription"),
         InlineKeyboardButton("📝 Set Caption ✍️", callback_data="set_caption")],
        [InlineKeyboardButton(f"🕒 Delete Timer: {delete_timer} ⏳", callback_data="set_delete_timer"),
         InlineKeyboardButton("📢 ForceSub Channels 📣", callback_data="forcesub_menu")],
        [InlineKeyboardButton("🔙 Back 🔄", callback_data="back_to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.callback_query.message.edit_text("⚙️ Settings Menu: 🔧", reply_markup=reply_markup)
    send_log_to_channel(context, f"Admin {user_id} accessed the settings menu. ⚙️")
    log_user_activity(context, user_id, username, "Accessed Settings Menu")

def forcesub_menu(update: Update, context: CallbackContext):
    """Show the ForceSub Channels sub-menu with dynamic '+' buttons. 📢"""
    user_id = str(update.effective_user.id)
    username = update.effective_user.username or "Unknown"
    admin_ids = context.bot_data.get("admin_ids", [])

    if user_id not in admin_ids:
        update.callback_query.message.reply_text("🚫 Only admins can manage force subscription channels. 😞")
        send_log_to_channel(context, f"User {user_id} denied access to forcesub menu - not an admin. 🚫")
        return

    settings = get_settings()
    forcesub_channels = settings.get("forcesub_channels", [COMPULSORY_CHANNEL])
    response = "📢 ForceSub Channels:\n\n"
    for idx, channel in enumerate(forcesub_channels, 1):
        response += f"{idx}. {channel} 🔗\n"

    keyboard = []
    if len(forcesub_channels) < 3:  # Limit to 3 channels for simplicity
        keyboard.append([InlineKeyboardButton("➕ Add Channel 🆕", callback_data=f"add_forcesub_channel_{len(forcesub_channels)}")])
    keyboard.append([InlineKeyboardButton("🔙 Back 🔄", callback_data="settings_menu")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.callback_query.message.edit_text(response, reply_markup=reply_markup)
    send_log_to_channel(context, f"Admin {user_id} accessed the forcesub channels menu. 📢")
    log_user_activity(context, user_id, username, "Accessed ForceSub Channels Menu")

def add_forcesub_channel(update: Update, context: CallbackContext):
    """Initiate adding a new force subscription channel. ➕"""
    user_id = str(update.effective_user.id)
    username = update.effective_user.username or "Unknown"
    admin_ids = context.bot_data.get("admin_ids", [])

    if user_id not in admin_ids:
        update.callback_query.message.reply_text("🚫 Only admins can add force subscription channels. 😞")
        send_log_to_channel(context, f"User {user_id} denied access to add forcesub channel - not an admin. 🚫")
        return

    context.user_data["awaiting_forcesub_channel"] = True
    context.user_data["forcesub_channel_index"] = int(update.callback_query.data.split("_")[-1])
    update.callback_query.message.reply_text("📢 Please send the channel username (e.g., @channelname). ✍️")
    send_log_to_channel(context, f"Admin {user_id} initiated adding a force subscription channel. ➕")
    log_user_activity(context, user_id, username, "Initiated Adding ForceSub Channel")

def handle_forcesub_input(update: Update, context: CallbackContext):
    """Handle the input for a new force subscription channel. 📢"""
    if not context.user_data.get("awaiting_forcesub_channel"):
        return

    user_id = str(update.effective_user.id)
    username = update.effective_user.username or "Unknown"
    admin_ids = context.bot_data.get("admin_ids", [])

    if user_id not in admin_ids:
        update.message.reply_text("🚫 Only admins can add force subscription channels. 😞")
        send_log_to_channel(context, f"User {user_id} denied access to add forcesub channel - not an admin. 🚫")
        return

    channel = update.message.text.strip()
    if not channel.startswith("@"):
        channel = f"@{channel}"

    settings = get_settings()
    forcesub_channels = settings.get("forcesub_channels", [COMPULSORY_CHANNEL])
    if channel in forcesub_channels:
        update.message.reply_text("🚫 This channel is already added! 😅")
        send_log_to_channel(context, f"Admin {user_id} tried to add duplicate channel: {channel} 🚫")
        return

    if channel == COMPULSORY_CHANNEL and len(forcesub_channels) > 1:
        update.message.reply_text(f"🚫 {COMPULSORY_CHANNEL} is already a compulsory channel! 😅")
        return

    forcesub_channels.append(channel)
    settings["forcesub_channels"] = forcesub_channels
    save_settings(settings)

    update.message.reply_text(f"✅ Added {channel} to force subscription channels! 🎉")
    context.user_data["awaiting_forcesub_channel"] = False
    send_log_to_channel(context, f"Admin {user_id} added force subscription channel: {channel} 🎊")
    log_user_activity(context, user_id, username, f"Added ForceSub Channel: {channel}")

    # Return to forcesub menu 🔄
    response = "📢 ForceSub Channels:\n\n"
    for idx, ch in enumerate(forcesub_channels, 1):
        response += f"{idx}. {ch} 🔗\n"

    keyboard = []
    if len(forcesub_channels) < 3:
        keyboard.append([InlineKeyboardButton("➕ Add Channel 🆕", callback_data=f"add_forcesub_channel_{len(forcesub_channels)}")])
    keyboard.append([InlineKeyboardButton("🔙 Back 🔄", callback_data="settings_menu")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(response, reply_markup=reply_markup)

def set_delete_timer(update: Update, context: CallbackContext):
    """Initiate the process to set a delete timer for messages. 🕒"""
    user_id = str(update.effective_user.id)
    username = update.effective_user.username or "Unknown"
    admin_ids = context.bot_data.get("admin_ids", [])

    if user_id not in admin_ids:
        update.callback_query.message.reply_text("🚫 Only admins can set the delete timer. 😞")
        send_log_to_channel(context, f"User {user_id} denied access to set delete timer - not an admin. 🚫")
        return

    context.user_data["awaiting_delete_timer"] = True
    update.callback_query.message.reply_text("🕒 Please send the delete timer (e.g., 10m for 10 minutes, 10h for 10 hours, 0m to disable). ⏰")
    send_log_to_channel(context, f"Admin {user_id} initiated setting a delete timer. ⏳")
    log_user_activity(context, user_id, username, "Initiated Setting Delete Timer")

def handle_delete_timer_input(update: Update, context: CallbackContext):
    """Handle the delete timer input. ⏳"""
    if not context.user_data.get("awaiting_delete_timer"):
        return

    user_id = str(update.effective_user.id)
    username = update.effective_user.username or "Unknown"
    admin_ids = context.bot_data.get("admin_ids", [])

    if user_id not in admin_ids:
        update.message.reply_text("🚫 Only admins can set the delete timer. 😞")
        send_log_to_channel(context, f"User {user_id} denied access to set delete timer - not an admin. 🚫")
        return

    timer = update.message.text.strip()
    if not (timer.endswith("m") or timer.endswith("h")) or not timer[:-1].isdigit():
        update.message.reply_text("🚫 Invalid format! Please use formats like 10m, 10h, or 0m. 😅")
        send_log_to_channel(context, f"Admin {user_id} provided invalid delete timer format: {timer} 🚫")
        return

    settings = get_settings()
    settings["delete_timer"] = timer
    save_settings(settings)

    update.message.reply_text(f"✅ Delete timer set to: {timer} ⏳")
    context.user_data["awaiting_delete_timer"] = False
    send_log_to_channel(context, f"Admin {user_id} set delete timer to: {timer} 🎉")
    log_user_activity(context, user_id, username, f"Set Delete Timer to: {timer}")

    # Return to settings menu 🔄
    force_sub_status = "✅ On" if settings.get("force_subscription", False) else "❌ Off"
    keyboard = [
        [InlineKeyboardButton(f"🔒 Force Subscription: {force_sub_status}", callback_data="toggle_force_subscription"),
         InlineKeyboardButton("📝 Set Caption ✍️", callback_data="set_caption")],
        [InlineKeyboardButton(f"🕒 Delete Timer: {timer} ⏳", callback_data="set_delete_timer"),
         InlineKeyboardButton("📢 ForceSub Channels 📣", callback_data="forcesub_menu")],
        [InlineKeyboardButton("🔙 Back 🔄", callback_data="back_to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("⚙️ Settings Menu: 🔧", reply_markup=reply_markup)

def batch_menu(update: Update, context: CallbackContext):
    """Show the Batch sub-menu (placeholder). 📦"""
    user_id = str(update.effective_user.id)
    username = update.effective_user.username or "Unknown"
    admin_ids = context.bot_data.get("admin_ids", [])

    if user_id not in admin_ids:
        update.callback_query.message.reply_text("🚫 Only admins can access the batch menu. 😞")
        send_log_to_channel(context, f"User {user_id} denied access to batch menu - not an admin. 🚫")
        return

    keyboard = [
        [InlineKeyboardButton("🔙 Back 🔄", callback_data="back_to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.callback_query.message.edit_text("📦 Batch Menu (Coming Soon): 🚧", reply_markup=reply_markup)
    send_log_to_channel(context, f"Admin {user_id} accessed the batch menu. 📦")
    log_user_activity(context, user_id, username, "Accessed Batch Menu")

def shortener_menu(update: Update, context: CallbackContext):
    """Show the Shortener sub-menu. 🔗"""
    user_id = str(update.effective_user.id)
    username = update.effective_user.username or "Unknown"
    admin_ids = context.bot_data.get("admin_ids", [])

    if user_id not in admin_ids:
        update.callback_query.message.reply_text("🚫 Only admins can access the shortener menu. 😞")
        send_log_to_channel(context, f"User {user_id} denied access to shortener menu - not an admin. 🚫")
        return

    settings = get_settings()
    current_shortener = settings.get("shortener", "GPLinks")
    keyboard = [
        [InlineKeyboardButton("🔗 GPLinks" + (" ✅" if current_shortener == "GPLinks" else ""), callback_data="set_shortener_GPLinks"),
         InlineKeyboardButton("🔗 TinyURL" + (" ✅" if current_shortener == "TinyURL" else ""), callback_data="set_shortener_TinyURL")],
        [InlineKeyboardButton("🔗 None" + (" ✅" if current_shortener == "None" else ""), callback_data="set_shortener_None")],
        [InlineKeyboardButton("🔙 Back 🔄", callback_data="back_to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.callback_query.message.edit_text("🔗 Shortener Menu: 🔗", reply_markup=reply_markup)
    send_log_to_channel(context, f"Admin {user_id} accessed the shortener menu. 🔗")
    log_user_activity(context, user_id, username, "Accessed Shortener Menu")

def set_shortener(update: Update, context: CallbackContext):
    """Set the link shortener. 🔗"""
    query = update.callback_query
    user_id = str(query.from_user.id)
    username = query.from_user.username or "Unknown"
    admin_ids = context.bot_data.get("admin_ids", [])

    if user_id not in admin_ids:
        query.message.reply_text("🚫 Only admins can set the shortener. 😞")
        send_log_to_channel(context, f"User {user_id} denied access to set shortener - not an admin. 🚫")
        return

    shortener = query.data.split("_")[-1]
    settings = get_settings()
    settings["shortener"] = shortener
    save_settings(settings)

    query.message.reply_text(f"✅ Link shortener set to: {shortener} 🎉")
    send_log_to_channel(context, f"Admin {user_id} set link shortener to: {shortener} 🎊")
    log_user_activity(context, user_id, username, f"Set Link Shortener to: {shortener}")

    # Return to shortener menu 🔄
    keyboard = [
        [InlineKeyboardButton("🔗 GPLinks" + (" ✅" if shortener == "GPLinks" else ""), callback_data="set_shortener_GPLinks"),
         InlineKeyboardButton("🔗 TinyURL" + (" ✅" if shortener == "TinyURL" else ""), callback_data="set_shortener_TinyURL")],
        [InlineKeyboardButton("🔗 None" + (" ✅" if shortener == "None" else ""), callback_data="set_shortener_None")],
        [InlineKeyboardButton("🔙 Back 🔄", callback_data="back_to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.message.reply_text("🔗 Shortener Menu: 🔗", reply_markup=reply_markup)

def tutorial(update: Update, context: CallbackContext):
    """Show a tutorial for using the bot. 📚"""
    user_id = str(update.effective_user.id)
    username = update.effective_user.username or "Unknown"
    admin_ids = context.bot_data.get("admin_ids", [])

    if user_id not in admin_ids:
        update.callback_query.message.reply_text("🚫 Only admins can view the tutorial. 😞")
        send_log_to_channel(context, f"User {user_id} denied access to tutorial - not an admin. 🚫")
        return

    tutorial_text = (
        "📝 Tutorial:\n\n"
        "1. Use /search <query> to find files. 🔍\n"
        "2. All group messages are treated as search queries. 💬\n"
        "3. Cloned bots redirect to the group for search (searchbot) or handle file storage (filestorebot). 🤖\n"
        "4. Use the admin menu to manage the bot! ⚙️"
    )
    keyboard = [[InlineKeyboardButton("🔙 Back 🔄", callback_data="back_to_main")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.callback_query.message.edit_text(tutorial_text, reply_markup=reply_markup)
    send_log_to_channel(context, f"Admin {user_id} viewed the tutorial. 📚")
    log_user_activity(context, user_id, username, "Viewed Tutorial")

def back_to_main(update: Update, context: CallbackContext):
    """Return to the main admin menu. 🔄"""
    user_id = str(update.effective_user.id)
    username = update.effective_user.username or "Unknown"
    admin_ids = context.bot_data.get("admin_ids", [])

    if user_id not in admin_ids:
        update.callback_query.message.reply_text("🚫 Only admins can access the admin menu. 😞")
        send_log_to_channel(context, f"User {user_id} denied access to admin menu - not an admin. 🚫")
        return

    keyboard = [
        [InlineKeyboardButton("🤖 Clone Bot 🛠️", callback_data="clone_bot_menu"),
         InlineKeyboardButton("📢 Broadcast 📣", callback_data="broadcast")],
        [InlineKeyboardButton("📊 Bot Stats 📈", callback_data="bot_stats"),
         InlineKeyboardButton("⚙️ Settings 🔧", callback_data="settings_menu")],
        [InlineKeyboardButton("📦 Batch Menu 📁", callback_data="batch_menu"),
         InlineKeyboardButton("🔗 Shortener 🔗", callback_data="shortener_menu")],
        [InlineKeyboardButton("📝 Tutorial 📚", callback_data="tutorial")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.callback_query.message.edit_text("👋 Welcome, Admin! What would you like to do? 🚀", reply_markup=reply_markup)
    send_log_to_channel(context, f"Admin {user_id} returned to the main admin menu. ⚙️")
    log_user_activity(context, user_id, username, "Returned to Main Admin Menu")

def create_clone_bot(update: Update, context: CallbackContext):
    """Initiate the process to create a cloned bot. ➕"""
    user_id = str(update.effective_user.id)
    username = update.effective_user.username or "Unknown"
    admin_ids = context.bot_data.get("admin_ids", [])

    if user_id not in admin_ids:
        update.callback_query.message.reply_text("🚫 Only admins can create clone bots. 😞")
        send_log_to_channel(context, f"User {user_id} denied access to create clone bot - not an admin. 🚫")
        return

    context.user_data["awaiting_clone_token"] = True
    update.callback_query.message.reply_text("🤖 Please send the Telegram bot token for the new clone bot. 🔑")
    send_log_to_channel(context, f"Admin {user_id} initiated clone bot creation. ➕")
    log_user_activity(context, user_id, username, "Initiated Clone Bot Creation")

def handle_clone_input(update: Update, context: CallbackContext):
    """Handle the bot token input for creating a cloned bot. 🔑"""
    if not context.user_data.get("awaiting_clone_token"):
        return

    user_id = str(update.effective_user.id)
    username = update.effective_user.username or "Unknown"
    admin_ids = context.bot_data.get("admin_ids", [])

    if user_id not in admin_ids:
        update.message.reply_text("🚫 Only admins can create clone bots. 😞")
        send_log_to_channel(context, f"User {user_id} denied access to create clone bot - not an admin. 🚫")
        return

    token = update.message.text.strip()
    try:
        bot = Bot(token)
        bot_info = bot.get_me()
        bot_username = bot_info.username
        logger.info(f"ℹ️ Validating token for bot @{bot_username}")
        send_log_to_channel(context, f"Admin {user_id} validated token for bot @{bot_username}. ✅")
    except Exception as e:
        update.message.reply_text(f"🚫 Invalid bot token: {str(e)} 😓")
        context.user_data["awaiting_clone_token"] = False
        send_log_to_channel(context, f"Admin {user_id} provided invalid token: {str(e)} 🚫")
        return

    context.user_data["clone_token"] = token
    context.user_data["awaiting_clone_token"] = False

    keyboard = [
        [InlineKeyboardButton("🔍 SearchBot 🔎", callback_data="usage_searchbot"),
         InlineKeyboardButton("📦 FileStoreBot 📁", callback_data="usage_filestorebot")],
        [InlineKeyboardButton("❌ Cancel 🚫", callback_data="cancel_clone")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("🤖 What type of bot do you want to create? 🛠️", reply_markup=reply_markup)
    send_log_to_channel(context, f"Admin {user_id} selecting type for new clone bot. 🛠️")
    log_user_activity(context, user_id, username, "Selecting Clone Bot Type")

def handle_usage_selection(update: Update, context: CallbackContext):
    """Handle the usage selection for the cloned bot (searchbot or filestorebot). 🛠️"""
    query = update.callback_query
    user_id = str(query.from_user.id)
    username = query.from_user.username or "Unknown"
    admin_ids = context.bot_data.get("admin_ids", [])

    if user_id not in admin_ids:
        query.message.reply_text("🚫 Only admins can create clone bots. 😞")
        send_log_to_channel(context, f"User {user_id} denied access to create clone bot - not an admin. 🚫")
        return

    if query.data == "cancel_clone":
        context.user_data.clear()
        query.message.edit_text("❌ Clone bot creation cancelled. 😢")
        send_log_to_channel(context, f"Admin {user_id} cancelled clone bot creation. 🚫")
        log_user_activity(context, user_id, username, "Cancelled Clone Bot Creation")
        return

    bot_type = "searchbot" if query.data == "usage_searchbot" else "filestorebot"
    context.user_data["bot_type"] = bot_type

    keyboard = [
        [InlineKeyboardButton("🔒 Private 🔐", callback_data="visibility_private"),
         InlineKeyboardButton("🌐 Public 🌍", callback_data="visibility_public")],
        [InlineKeyboardButton("❌ Cancel 🚫", callback_data="cancel_clone")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.message.edit_text("🔐 Should the cloned bot be private or public? 🔍", reply_markup=reply_markup)
    send_log_to_channel(context, f"Admin {user_id} selecting visibility for new clone bot of type {bot_type}. 🔒")
    log_user_activity(context, user_id, username, f"Selecting Visibility for {bot_type}")

def handle_visibility_selection(update: Update, context: CallbackContext):
    """Handle the visibility selection for the cloned bot. 🔐"""
    query = update.callback_query
    user_id = str(query.from_user.id)
    username = query.from_user.username or "Unknown"
    admin_ids = context.bot_data.get("admin_ids", [])

    if user_id not in admin_ids:
        query.message.reply_text("🚫 Only admins can create clone bots. 😞")
        send_log_to_channel(context, f"User {user_id} denied access to create clone bot - not an admin. 🚫")
        return

    if query.data == "cancel_clone":
        context.user_data.clear()
        query.message.edit_text("❌ Clone bot creation cancelled. 😢")
        send_log_to_channel(context, f"Admin {user_id} cancelled clone bot creation. 🚫")
        log_user_activity(context, user_id, username, "Cancelled Clone Bot Creation")
        return

    visibility = "private" if query.data == "visibility_private" else "public"
    token = context.user_data.get("clone_token")
    bot_type = context.user_data.get("bot_type")
    if not token or not bot_type:
        query.message.edit_text("🚫 No bot token or type found. Please start over with /start. 😓")
        send_log_to_channel(context, f"Admin {user_id} failed to create clone bot - no token or type found. 🚫")
        return

    cloned_bots = get_cloned_bots()
    cloned_bots.append({
        "token": token,
        "visibility": visibility,
        "type": bot_type,
        "owner_id": user_id,
        "created_at": datetime.now().isoformat(),
        "standalone": False
    })
    save_cloned_bots(cloned_bots)

    # Start the cloned bot 🚀
    from bot import start_cloned_bot
    success = start_cloned_bot(token, admin_ids, bot_type)
    if success:
        query.message.edit_text(f"✅ Cloned bot created successfully! It’s a {bot_type} with {visibility} visibility. 🎉")
        send_log_to_channel(context, f"Admin {user_id} successfully created a {bot_type} with token ending {token[-4:]} 🎊")
        log_user_activity(context, user_id, username, f"Created Clone Bot: {bot_type} ({visibility})")
    else:
        query.message.edit_text("🚫 Failed to start the cloned bot. Please check the logs. 😓")
        send_log_to_channel(context, f"Admin {user_id} failed to start cloned bot with token ending {token[-4:]} 🚫")

    context.user_data.clear()

def view_clone_bots(update: Update, context: CallbackContext):
    """Show all cloned bots to the admin with delete buttons. 📋"""
    user_id = str(update.effective_user.id)
    username = update.effective_user.username or "Unknown"
    admin_ids = context.bot_data.get("admin_ids", [])

    if user_id not in admin_ids:
        update.callback_query.message.reply_text("🚫 Only admins can view clone bots. 😞")
        send_log_to_channel(context, f"User {user_id} denied access to view clone bots - not an admin. 🚫")
        return

    cloned_bots = get_cloned_bots()
    if not cloned_bots:
        update.callback_query.message.reply_text("📋 No cloned bots found. 😢")
        send_log_to_channel(context, f"Admin {user_id} viewed clone bots - none found. 📋")
        return

    response = "📋 Cloned Bots:\n\n"
    keyboard = []
    for idx, bot in enumerate(cloned_bots, 1):
        response += f"{idx}. Token ending: {bot['token'][-4:]} | Type: {bot['type']} | Visibility: {bot['visibility']} | Created: {bot['created_at']}\n"
        keyboard.append([InlineKeyboardButton(f"🗑️ Delete Bot {idx} 🗑️", callback_data=f"delete_clone_bot_{idx-1}")])
    keyboard.append([InlineKeyboardButton("🔙 Back 🔄", callback_data="clone_bot_menu")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.callback_query.message.edit_text(response, reply_markup=reply_markup)
    send_log_to_channel(context, f"Admin {user_id} viewed clone bots. 📋")
    log_user_activity(context, user_id, username, "Viewed Clone Bots")

def delete_clone_bot(update: Update, context: CallbackContext):
    """Show confirmation for deleting a cloned bot. 🗑️"""
    user_id = str(update.effective_user.id)
    username = update.effective_user.username or "Unknown"
    admin_ids = context.bot_data.get("admin_ids", [])

    if user_id not in admin_ids:
        update.callback_query.message.reply_text("🚫 Only admins can delete clone bots. 😞")
        send_log_to_channel(context, f"User {user_id} denied access to delete clone bot - not an admin. 🚫")
        return

    bot_index = int(update.callback_query.data.split("_")[-1])
    cloned_bots = get_cloned_bots()
    if bot_index < 0 or bot_index >= len(cloned_bots):
        update.callback_query.message.edit_text("🚫 Invalid bot selection. 😓")
        send_log_to_channel(context, f"Admin {user_id} selected invalid bot index for deletion: {bot_index} 🚫")
        return

    bot = cloned_bots[bot_index]
    response = f"⚠️ Are you sure you want to delete this bot?\nToken ending: {bot['token'][-4:]} | Type: {bot['type']}"
    keyboard = [
        [InlineKeyboardButton("✅ Yes, Delete ✔️", callback_data=f"confirm_delete_bot_{bot_index}"),
         InlineKeyboardButton("❌ Cancel 🚫", callback_data="cancel_delete")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.callback_query.message.edit_text(response, reply_markup=reply_markup)
    send_log_to_channel(context, f"Admin {user_id} initiated deletion confirmation for bot with token ending {bot['token'][-4:]} 🗑️")
    log_user_activity(context, user_id, username, f"Initiated Deletion of Bot (Token ending: {bot['token'][-4:]})")

def confirm_delete_bot(update: Update, context: CallbackContext):
    """Handle the deletion of a cloned bot after confirmation. 🗑️"""
    query = update.callback_query
    user_id = str(query.from_user.id)
    username = query.from_user.username or "Unknown"
    admin_ids = context.bot_data.get("admin_ids", [])

    if user_id not in admin_ids:
        query.message.reply_text("🚫 Only admins can delete clone bots. 😞")
        send_log_to_channel(context, f"User {user_id} denied access to delete clone bot - not an admin. 🚫")
        return

    if query.data == "cancel_delete":
        query.message.edit_text("❌ Clone bot deletion cancelled. 😢")
        send_log_to_channel(context, f"Admin {user_id} cancelled clone bot deletion. 🚫")
        log_user_activity(context, user_id, username, "Cancelled Clone Bot Deletion")
        return view_clone_bots(update, context)

    bot_index = int(query.data.split("_")[-1])
    cloned_bots = get_cloned_bots()
    if bot_index < 0 or bot_index >= len(cloned_bots):
        query.message.edit_text("🚫 Invalid bot selection. 😓")
        send_log_to_channel(context, f"Admin {user_id} selected invalid bot index for deletion: {bot_index} 🚫")
        return

    deleted_bot = cloned_bots.pop(bot_index)
    save_cloned_bots(cloned_bots)
    keyboard = [[InlineKeyboardButton("🔙 Back 🔄", callback_data="clone_bot_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.message.edit_text(f"✅ Cloned bot with token ending {deleted_bot['token'][-4:]} deleted successfully! 🎉", reply_markup=reply_markup)
    send_log_to_channel(context, f"Admin {user_id} deleted cloned bot with token ending {deleted_bot['token'][-4:]} 🎊")
    log_user_activity(context, user_id, username, f"Deleted Clone Bot (Token ending: {deleted_bot['token'][-4:]})")

def toggle_force_subscription(update: Update, context: CallbackContext):
    """Toggle the force subscription setting. 🔒"""
    user_id = str(update.effective_user.id)
    username = update.effective_user.username or "Unknown"
    admin_ids = context.bot_data.get("admin_ids", [])

    if user_id not in admin_ids:
        update.callback_query.message.reply_text("🚫 Only admins can toggle force subscription. 😞")
        send_log_to_channel(context, f"User {user_id} denied access to toggle force subscription - not an admin. 🚫")
        return

    settings = get_settings()
    current_state = settings.get("force_subscription", False)
    settings["force_subscription"] = not current_state
    save_settings(settings)

    state_text = "enabled" if settings["force_subscription"] else "disabled"
    update.callback_query.message.reply_text(f"🔒 Force subscription {state_text}! 🎉")
    send_log_to_channel(context, f"Admin {user_id} {state_text} force subscription. 🎊")
    log_user_activity(context, user_id, username, f"Force Subscription {state_text.capitalize()}")

    # Return to settings menu 🔄
    force_sub_status = "✅ On" if settings.get("force_subscription", False) else "❌ Off"
    delete_timer = settings.get("delete_timer", "0m")
    keyboard = [
        [InlineKeyboardButton(f"🔒 Force Subscription: {force_sub_status}", callback_data="toggle_force_subscription"),
         InlineKeyboardButton("📝 Set Caption ✍️", callback_data="set_caption")],
        [InlineKeyboardButton(f"🕒 Delete Timer: {delete_timer} ⏳", callback_data="set_delete_timer"),
         InlineKeyboardButton("📢 ForceSub Channels 📣", callback_data="forcesub_menu")],
        [InlineKeyboardButton("🔙 Back 🔄", callback_data="back_to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.callback_query.message.reply_text("⚙️ Settings Menu: 🔧", reply_markup=reply_markup)

def set_caption(update: Update, context: CallbackContext):
    """Initiate the process to set a custom caption for search results. 📝"""
    user_id = str(update.effective_user.id)
    username = update.effective_user.username or "Unknown"
    admin_ids = context.bot_data.get("admin_ids", [])

    if user_id not in admin_ids:
        update.callback_query.message.reply_text("🚫 Only admins can set captions. 😞")
        send_log_to_channel(context, f"User {user_id} denied access to set caption - not an admin. 🚫")
        return

    context.user_data["awaiting_caption"] = True
    update.callback_query.message.reply_text("📝 Please send the new caption for search results (max 100 characters). ✍️")
    send_log_to_channel(context, f"Admin {user_id} initiated setting a new caption. ✍️")
    log_user_activity(context, user_id, username, "Initiated Setting Caption")

def handle_caption_input(update: Update, context: CallbackContext):
    """Handle the caption input for search results. ✍️"""
    if not context.user_data.get("awaiting_caption"):
        return

    user_id = str(update.effective_user.id)
    username = update.effective_user.username or "Unknown"
    admin_ids = context.bot_data.get("admin_ids", [])

    if user_id not in admin_ids:
        update.message.reply_text("🚫 Only admins can set captions. 😞")
        send_log_to_channel(context, f"User {user_id} denied access to set caption - not an admin. 🚫")
        return

    caption = update.message.text.strip()
    if len(caption) > 100:
        update.message.reply_text("🚫 Caption too long! Please keep it under 100 characters. 😅")
        send_log_to_channel(context, f"Admin {user_id} provided a caption that was too long. 🚫")
        return

    settings = get_settings()
    settings["search_caption"] = caption
    save_settings(settings)

    update.message.reply_text(f"✅ Search caption set to: {caption} 🎉")
    context.user_data["awaiting_caption"] = False
    send_log_to_channel(context, f"Admin {user_id} set search caption to: {caption} 🎊")
    log_user_activity(context, user_id, username, f"Set Search Caption to: {caption}")

    # Return to settings menu 🔄
    force_sub_status = "✅ On" if settings.get("force_subscription", False) else "❌ Off"
    delete_timer = settings.get("delete_timer", "0m")
    keyboard = [
        [InlineKeyboardButton(f"🔒 Force Subscription: {force_sub_status}", callback_data="toggle_force_subscription"),
         InlineKeyboardButton("📝 Set Caption ✍️", callback_data="set_caption")],
        [InlineKeyboardButton(f"🕒 Delete Timer: {delete_timer} ⏳", callback_data="set_delete_timer"),
         InlineKeyboardButton("📢 ForceSub Channels 📣", callback_data="forcesub_menu")],
        [InlineKeyboardButton("🔙 Back 🔄", callback_data="back_to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("⚙️ Settings Menu: 🔧", reply_markup=reply_markup)

def broadcast(update: Update, context: CallbackContext):
    """Initiate the process to send a broadcast message with inline buttons. 📢"""
    user_id = str(update.effective_user.id)
    username = update.effective_user.username or "Unknown"
    admin_ids = context.bot_data.get("admin_ids", [])

    if user_id not in admin_ids:
        update.callback_query.message.reply_text("🚫 Only admins can broadcast messages. 😞")
        send_log_to_channel(context, f"User {user_id} denied access to broadcast - not an admin. 🚫")
        return

    context.user_data["awaiting_broadcast"] = True
    update.callback_query.message.reply_text("📢 Please send the broadcast message you want to send to all users. 📣")
    send_log_to_channel(context, f"Admin {user_id} initiated a broadcast. 📢")
    log_user_activity(context, user_id, username, "Initiated Broadcast")

def handle_broadcast_input(update: Update, context: CallbackContext):
    """Handle the broadcast message input and send it to all users with inline buttons. 📣"""
    if not context.user_data.get("awaiting_broadcast"):
        return

    user_id = str(update.effective_user.id)
    username = update.effective_user.username or "Unknown"
    admin_ids = context.bot_data.get("admin_ids", [])

    if user_id not in admin_ids:
        update.message.reply_text("🚫 Only admins can broadcast messages. 😞")
        send_log_to_channel(context, f"User {user_id} denied access to broadcast - not an admin. 🚫")
        return

    broadcast_message = update.message.text.strip()
    settings = get_settings()
    forcesub_channels = settings.get("forcesub_channels", [COMPULSORY_CHANNEL])
    keyboard = []
    for channel in forcesub_channels:
        keyboard.append([InlineKeyboardButton(f"🔗 Join {channel} 🌟", url=f"https://t.me/{channel[1:]}")])
    reply_markup = InlineKeyboardMarkup(keyboard)

    users = get_users()
    success_count = 0
    for uid in users:
        try:
            context.bot.send_message(
                chat_id=uid,
                text=broadcast_message,
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
            success_count += 1
        except Exception as e:
            logger.error(f"🚨 Failed to send broadcast to user {uid}: {str(e)}")
            continue

    update.message.reply_text(f"✅ Broadcast sent to {success_count} users! 📣")
    context.user_data["awaiting_broadcast"] = False
    send_log_to_channel(context, f"Admin {user_id} sent a broadcast to {success_count} users. 🎊")
    log_user_activity(context, user_id, username, f"Sent Broadcast to {success_count} Users")
    back_to_main(update, context)

def bot_stats(update: Update, context: CallbackContext):
    """Show basic bot statistics. 📈"""
    user_id = str(update.effective_user.id)
    username = update.effective_user.username or "Unknown"
    admin_ids = context.bot_data.get("admin_ids", [])

    if user_id not in admin_ids:
        update.callback_query.message.reply_text("🚫 Only admins can view bot stats. 😞")
        send_log_to_channel(context, f"User {user_id} denied access to view bot stats - not an admin. 🚫")
        return

    files = []
    with open("/opt/render/project/src/data/files.json", "r") as f:
        files = json.load(f)

    cloned_bots = get_cloned_bots()
    stats = (
        f"📊 Bot Stats:\n\n"
        f"📁 **Total Files**: {len(files)} 📦\n"
        f"🤖 **Total Cloned Bots**: {len(cloned_bots)} ⚙️\n"
        f"👥 **Total Users**: {len(get_users())} 🌟\n"
    )
    keyboard = [[InlineKeyboardButton("🔙 Back 🔄", callback_data="back_to_main")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.callback_query.message.edit_text(stats, reply_markup=reply_markup, parse_mode="Markdown")
    send_log_to_channel(context, f"Admin {user_id} viewed bot stats. 📈")
    log_user_activity(context, user_id, username, "Viewed Bot Stats")