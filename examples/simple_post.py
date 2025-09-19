"""Simple posting example."""

import asyncio
import os
from dotenv import load_dotenv
from telegram_agentic_publisher import TelegramPublisher, SessionManager
from telegram_agentic_publisher.utils import Config

# Load environment variables
load_dotenv()


async def main():
    # Configuration
    config = Config()

    # Create session manager
    session_mgr = SessionManager(
        storage_path=config.session_storage_path,
        encryption_key=config.session_encryption_key
    )

    # Get first available session
    sessions = session_mgr.list_sessions()
    if not sessions:
        print("No sessions available. Please run authentication first:")
        print("telegram-publisher auth -p +YOUR_PHONE_NUMBER")
        return

    session_id = sessions[0]["id"]
    print(f"Using session: {sessions[0]['name']}")

    # Create publisher
    async with TelegramPublisher(
        api_id=config.api_id,
        api_hash=config.api_hash,
        session_id=session_id,
        session_manager=session_mgr
    ) as publisher:
        # Post simple message
        message_id, message_url = await publisher.publish(
            channel="@your_channel",  # Replace with your channel
            content="Hello from Telegram Agentic Publisher! 🚀"
        )

        if message_id:
            print(f"✅ Message posted successfully!")
            print(f"📍 URL: {message_url}")
        else:
            print("❌ Failed to post message")


if __name__ == "__main__":
    asyncio.run(main())