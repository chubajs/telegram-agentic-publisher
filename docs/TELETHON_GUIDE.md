# Telethon Integration Guide

This guide provides comprehensive documentation for using `telegram-agentic-publisher` with Telethon, based on official Telethon documentation and best practices.

## Table of Contents

1. [Basic Message Sending](#basic-message-sending)
2. [Markdown Formatting](#markdown-formatting)
3. [Media Galleries and Albums](#media-galleries-and-albums)
4. [Advanced Formatting with Entities](#advanced-formatting-with-entities)
5. [Session Management](#session-management)
6. [File Handling](#file-handling)
7. [Custom Markdown Extensions](#custom-markdown-extensions)

## Basic Message Sending

### Simple Text Message

```python
from telegram_agentic_publisher import TelegramPublisher

# Basic message sending
await publisher.publish(
    channel="@channelname",
    content="Hello, World!"
)

# With parse mode (default is markdown)
await publisher.publish(
    channel="@channelname",
    content="**Bold** and *italic* text",
    parse_mode="md"  # or "html"
)
```

### Telethon Direct Usage

```python
from telethon import TelegramClient

# Send with markdown parsing
await client.send_message(
    chat_id='@channel',
    message='*Hello* **world**!',
    parse_mode='md'
)

# Send with HTML parsing
await client.send_message(
    chat_id='@channel',
    message='<b>Hello</b> <i>world</i>!',
    parse_mode='html'
)
```

## Markdown Formatting

### Supported Markdown Syntax

Based on Telethon v1.40+ documentation:

```python
# All markdown features
message = """
**Bold text**
*Italic text*
__Underlined text__
~~Strikethrough text~~
`inline code`
[Link text](https://example.com)

> Blockquote
> Multi-line quote

```python
# Code block
print("Hello")
```
"""

await publisher.publish(channel="@channel", content=message)
```

### Inline Mentions

```python
# Mention users inline
message = "Hello [user](@username), check this out!"
await publisher.publish(channel="@channel", content=message)
```

### Nested Formatting

```python
# Telethon supports nested entities
message = "**__Bold and underlined__** text"
await publisher.publish(channel="@channel", content=message)
```

## Media Galleries and Albums

### Sending Multiple Images as Album

```python
# Using telegram-agentic-publisher
media_files = [
    "photo1.jpg",
    "photo2.jpg",
    "photo3.jpg",
    "https://example.com/photo4.jpg"  # URLs supported
]

# Send as album (up to 10 items)
await publisher.publish(
    channel="@channel",
    content="Check out this photo gallery! 📸",
    media=media_files
)
```

### Telethon Direct Album Sending

```python
# Direct Telethon usage for albums
await client.send_file(
    chat='@channel',
    file=[file1, file2, file3],  # List creates album
    caption="Album caption"
)

# Albums larger than 10 items are automatically sliced
large_album = [f"photo{i}.jpg" for i in range(25)]
await client.send_file(chat, large_album)  # Sent as 3 albums
```

### Multiple Captions for Albums

```python
# Different caption for each item
files = ['photo1.jpg', 'photo2.jpg']
captions = ['First photo', 'Second photo']

await client.send_file(
    chat='@channel',
    file=files,
    caption=captions  # List of captions
)
```

### Album Event Handling

```python
from telethon import events

@client.on(events.Album)
async def album_handler(event):
    # Handle entire album at once
    print(f"Received album with {len(event.messages)} items")
    print(f"Album ID: {event.grouped_id}")

    # Download all media from album
    for message in event.messages:
        if message.photo:
            await message.download_media()
```

## Advanced Formatting with Entities

### Using Message Entities Directly

```python
from telethon.tl.types import (
    MessageEntityBold,
    MessageEntityItalic,
    MessageEntityCode,
    MessageEntityTextUrl,
    MessageEntityStrike,
    MessageEntityUnderline
)

# Manual entity creation
text = "Hello world, check this link"
entities = [
    MessageEntityBold(offset=0, length=5),  # "Hello"
    MessageEntityItalic(offset=6, length=5),  # "world"
    MessageEntityTextUrl(offset=19, length=4, url='https://example.com')  # "link"
]

await client.send_message(
    chat='@channel',
    message=text,
    formatting_entities=entities  # Bypass parse_mode
)
```

### Custom Markdown Parser for Spoilers and Emoji

```python
from telethon.extensions import markdown
from telethon import types

class CustomMarkdown:
    @staticmethod
    def parse(text):
        text, entities = markdown.parse(text)
        for i, e in enumerate(entities):
            if isinstance(e, types.MessageEntityTextUrl):
                if e.url == 'spoiler':
                    entities[i] = types.MessageEntitySpoiler(e.offset, e.length)
                elif e.url.startswith('emoji/'):
                    doc_id = int(e.url.split('/')[1])
                    entities[i] = types.MessageEntityCustomEmoji(
                        e.offset, e.length, doc_id
                    )
        return text, entities

# Usage
client.parse_mode = CustomMarkdown()
await client.send_message(
    'me',
    'Hidden [text](spoiler) with [❤️](emoji/5449505950283078474)!'
)
```

## Session Management

### String Session Creation and Storage

```python
from telethon.sessions import StringSession
from telegram_agentic_publisher import SessionManager

# Create new session
client = TelegramClient(StringSession(), api_id, api_hash)
await client.start(phone='+1234567890')

# Save session string
session_string = client.session.save()

# Store in SessionManager
session_mgr = SessionManager(storage_path, encryption_key)
session_id = session_mgr.create_session(
    name="My Session",
    phone="+1234567890",
    session_string=session_string,
    user_info={"username": "myusername"}
)
```

### Loading and Using Sessions

```python
# Load session
session_data = session_mgr.get_session(session_id)
session_string = session_data["session_string"]

# Create client with saved session
client = TelegramClient(
    StringSession(session_string),
    api_id,
    api_hash
)
await client.connect()
```

## File Handling

### Sending Different File Types

```python
# Send as photo (compressed)
await publisher.publish(
    channel="@channel",
    media="photo.jpg"
)

# Send as document (uncompressed)
await client.send_file(
    '@channel',
    'photo.jpg',
    force_document=True
)

# Send video with streaming support
await client.send_file(
    '@channel',
    'video.mp4',
    supports_streaming=True
)

# Send with custom thumbnail
await client.send_file(
    '@channel',
    'video.mp4',
    thumb='thumbnail.jpg'
)
```

### Sending Bytes and Streams

```python
from io import BytesIO

# Send bytes as file
image_data = BytesIO(b'...')
image_data.name = 'image.jpg'  # Extension matters
await client.send_file('@channel', image_data)

# Send byte string directly
await client.send_file('@channel', b'file content')
```

### Download Media with Options

```python
# Download with different sizes
await client.download_media(
    message,
    thumb=-1  # -1 for largest thumbnail
)

# Download as bytes
media_bytes = await client.download_media(
    message,
    file=bytes
)

# Stream download with offset
async for chunk in client.iter_download(
    message,
    offset=1024  # Start from byte 1024
):
    process_chunk(chunk)
```

### Progress Callbacks

```python
async def progress_callback(current, total):
    percent = current * 100 / total
    print(f"Downloaded {current}/{total} ({percent:.1f}%)")

# Upload with progress
await client.send_file(
    '@channel',
    'large_file.zip',
    progress_callback=progress_callback
)

# Download with progress
await client.download_media(
    message,
    progress_callback=progress_callback
)
```

## Custom Markdown Extensions

### Implementation in telegram-agentic-publisher

```python
from telegram_agentic_publisher.formatting import MarkdownProcessor

class ExtendedMarkdown(MarkdownProcessor):
    """Extended markdown with custom features."""

    def parse_markdown_entities(self, text):
        # Get base entities
        text, entities = super().parse_markdown_entities(text)

        # Add custom processing
        # Example: [[highlight]] for highlighted text
        import re
        highlight_pattern = r'\[\[([^\]]+)\]\]'

        for match in re.finditer(highlight_pattern, text):
            # Add custom entity
            entities.append(
                MessageEntityTextUrl(
                    offset=match.start(),
                    length=match.end() - match.start(),
                    url='highlight'
                )
            )

        return text, entities
```

### Template Integration

```python
# Use templates with Telethon formatting
template = """
📢 **{title|upper}**

{description}

{?has_media}
🖼️ See attached media
{/has_media}

{#tags}
#{.}
{/tags}
"""

data = {
    "title": "announcement",
    "description": "This is a *formatted* message",
    "has_media": True,
    "tags": ["news", "update"]
}

await publisher.publish(
    channel="@channel",
    template=template,
    template_data=data,
    media=["image1.jpg", "image2.jpg"]
)
```

## Best Practices

### 1. Message Length Limits

```python
# Telegram message limit is 4096 characters
if len(content) > 4096:
    # Split or truncate
    content = content[:4090] + "..."
```

### 2. Media Gallery Limits

```python
# Maximum 10 items per album
if len(media_files) > 10:
    # Send in batches
    for i in range(0, len(media_files), 10):
        batch = media_files[i:i+10]
        await publisher.publish(
            channel="@channel",
            media=batch
        )
```

### 3. Error Handling

```python
from telethon.errors import FloodWaitError, ChatWriteForbiddenError

try:
    await publisher.publish(channel="@channel", content=message)
except FloodWaitError as e:
    print(f"Rate limited. Wait {e.seconds} seconds")
    await asyncio.sleep(e.seconds)
    # Retry
except ChatWriteForbiddenError:
    print("No permission to post in this channel")
```

### 4. Scheduled Messages

```python
from datetime import timedelta

# Schedule message for later
await client.send_message(
    '@channel',
    'Scheduled message',
    schedule=timedelta(hours=1)
)
```

## References

- [Telethon Documentation](https://docs.telethon.dev/)
- [Telegram Bot API](https://core.telegram.org/bots/api)
- [telegram-agentic-publisher GitHub](https://github.com/chubajs/telegram-agentic-publisher)

---

*Generated with Context7 - Telethon v1.41 documentation*