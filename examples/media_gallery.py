"""Media gallery posting example."""

import asyncio
from telegram_agentic_publisher import TelegramPublisher, SessionManager
from telegram_agentic_publisher.utils import Config


async def main():
    config = Config()
    session_mgr = SessionManager(config.session_storage_path, config.session_encryption_key)

    # Get session
    sessions = session_mgr.list_sessions()
    if not sessions:
        print("No sessions available. Please authenticate first.")
        return

    # Create publisher
    publisher = TelegramPublisher(
        api_id=config.api_id,
        api_hash=config.api_hash,
        session_id=sessions[0]["id"],
        session_manager=session_mgr
    )

    try:
        await publisher.connect()

        # Prepare media files (mix of local files and URLs)
        media_files = [
            "path/to/photo1.jpg",  # Local file
            "path/to/photo2.png",  # Local file
            "https://example.com/image3.jpg",  # URL
        ]

        # Caption with markdown formatting
        caption = """
📸 **Photo Gallery Example**

This gallery contains:
• *Local images* from disk
• Images from __URLs__
• All in one beautiful gallery!

[More examples](https://github.com/yourusername/telegram-agentic-publisher)
        """

        # Post gallery
        message_id, message_url = await publisher.publish(
            channel="@your_channel",
            content=caption,
            media=media_files,
            parse_mode="md"
        )

        if message_id:
            print(f"✅ Gallery posted: {message_url}")
        else:
            print("❌ Failed to post gallery")

    finally:
        await publisher.disconnect()


if __name__ == "__main__":
    asyncio.run(main())