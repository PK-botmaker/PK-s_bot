from telegram.ext import Application
from utils.logger import log_error

async def sync_backup_channels(app: Application):
    """Sync files to backup channels."""
    try:
        db = app.bot_data.get("firestore_db")
        channels = db.collection("storage_channels").where("active", "==", True).get()
        for channel in channels:
            channel_id = channel.to_dict().get("channel_id")
            files = db.collection("cloned_files").get()
            for file in files:
                metadata = file.to_dict()
                await app.bot.forward_message(
                    chat_id=channel_id,
                    from_chat_id=os.getenv("PRIVATE_CHANNEL_ID"),
                    message_id=metadata["message_id"]
                )
        print("Backup sync completed!")
    except Exception as e:
        log_error(f"Backup sync error: {str(e)}")

if __name__ == "__main__":
    import asyncio
    app = Application.builder().token(os.getenv("TELEGRAM_TOKEN")).build()
    asyncio.run(sync_backup_channels(app))
