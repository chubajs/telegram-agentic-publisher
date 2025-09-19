"""Template-based posting example."""

import asyncio
from datetime import datetime
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

        # Define template
        template = """
📰 **{title|upper}**

{?has_subtitle}_{subtitle}_
{/has_subtitle}

{content}

{?has_image}
🖼️ [View Image]({image_url})
{/has_image}

{?tags}
📌 Tags: {#tags}#{.} {/tags}
{/tags}

{?source}
📖 Source: [{source.name}]({source.url})
{/source}

⏰ Posted: {posted_at|date:%B %d, %Y at %H:%M}
        """

        # Data for template
        data = {
            "title": "Breaking News",
            "has_subtitle": True,
            "subtitle": "Important announcement from our team",
            "content": "We're excited to announce the release of Telegram Agentic Publisher! "
                      "This powerful library makes it easy to post rich content to Telegram channels.",
            "has_image": True,
            "image_url": "https://example.com/announcement.jpg",
            "tags": ["announcement", "release", "telegram", "opensource"],
            "source": {
                "name": "Official Blog",
                "url": "https://example.com/blog"
            },
            "posted_at": datetime.now().isoformat()
        }

        # Post with template
        message_id, message_url = await publisher.publish(
            channel="@your_channel",
            template=template,
            template_data=data,
            parse_mode="md"
        )

        if message_id:
            print(f"✅ Templated message posted: {message_url}")
        else:
            print("❌ Failed to post message")

    finally:
        await publisher.disconnect()


if __name__ == "__main__":
    asyncio.run(main())