import os
from telegram import Bot
from utils.db_channel import get_setting

async def log_error(message: str):
    """Log errors to log channel and Render."""
    try:
        bot = Bot(token=os.getenv("TELEGRAM_TOKEN"))
        log_channel = await get_setting("log_channel_id")
        if log_channel:
            await bot.send_message(
                chat_id=log_channel,
                text=message,
                disable_notification=True
            )
        print(message)  # Log to Render
        return True
    except Exception as e:
        print(f"⚠️ Logger error: {str(e)}")
        return False
