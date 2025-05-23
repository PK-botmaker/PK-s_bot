from utils.db_channel import set_setting, get_setting
from utils.logging_utils import log_error

async def add_storage_channel(channel_id: str):
    """Add a storage channel."""
    try:
        channels = await get_setting("storage_channels", [])
        if channel_id not in channels:
            channels.append(channel_id)
            await set_setting("storage_channels", channels)
            logger.info(f"✅ Channel {channel_id} added")
        else:
            logger.info(f"⚠️ Channel {channel_id} already exists")
    except Exception as e:
        await log_error(f"Channel add error: {str(e)}")
        logger.info(f"⚠️ Failed to add channel {channel_id}")

async def remove_storage_channel(channel_id: str):
    """Remove a storage channel."""
    try:
        channels = await get_setting("storage_channels", [])
        if channel_id in channels:
            channels.remove(channel_id)
            await set_setting("storage_channels", channels)
            logger.info(f"✅ Channel {channel_id} removed")
        else:
            logger.info(f"⚠️ Channel {channel_id} not found")
    except Exception as e:
        await log_error(f"Channel remove error: {str(e)}")
        logger.info(f"⚠️ Failed to remove channel {channel_id}")
