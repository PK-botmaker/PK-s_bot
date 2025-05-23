from telegram import Bot
from utils.logging_utils import log_error

async def send_message(bot: Bot, chat_id: str, text: str, reply_markup=None):
    """Send message with link error handling."""
    try:
        if len(text) > 4096:
            text = text[:4093] + "..."
            await log_error(f"Message truncated for {chat_id}")
        message = await bot.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=reply_markup,
            disable_web_page_preview=True
        )
        logger.info(f"✅ Message sent to {chat_id}")
        return message
    except Exception as e:
        await log_error(f"Send message error to {chat_id}: {str(e)}")
        return None
