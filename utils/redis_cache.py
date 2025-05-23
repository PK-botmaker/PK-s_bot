from utils.logger import log_error

async def cache_data(key: str, value: str):
    """Cache data in Redis (optional)."""
    try:
        # Simulated Redis caching
        logger.info(f"✅ Cached data: {key}")
        return True
    except Exception as e:
        await log_error(f"Redis cache error: {str(e)}")
        logger.info("⚠️ Failed to cache data")
        return False
