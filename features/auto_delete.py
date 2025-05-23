import asyncio
from telegram import Bot
from utils.logging_utils import log_error

async def set_auto_delete(bot: Bot, chat_id: str, message_id: int, hours: int):
    """Set auto-delete for messages."""
    try:
        await asyncio.sleep(hours * 3600)
        await bot.delete_message(chat_id=chat_id, message_id=message_id)
        logger.info(f"✅ Message {message_id} deleted from {chat_id}")
    except Exception as e:
        await log_error(f"Auto-delete error: {str(e)}")
        logger.info(f"⚠️ Failed to delete message {message_id}")
