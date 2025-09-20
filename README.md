# Telegram Agentic Publisher

An open-source Python library for posting to Telegram channels via authorized user accounts. Supports rich formatting, media galleries, and template-based content generation.

**Author**: [Serge Bulaev](https://bulaev.org) <a href="https://www.linkedin.com/in/sbulaev/"><img src="https://upload.wikimedia.org/wikipedia/commons/8/81/LinkedIn_icon.svg" alt="LinkedIn" width="20" height="20" style="vertical-align: middle;"></a>
**[Co.Actor](https://co.actor)** - Your Co-Author for creative content
**[Creative Content Crafts](https://cccrafts.ai)** - AI Content Strategy Audit and Consulting
**License**: MIT

## Features

- ✅ **User Account Posting**: Post as a real Telegram user to any channel
- 📝 **Rich Formatting**: Full markdown support with bold, italic, links, code blocks, etc.
- 🖼️ **Media Galleries**: Send single images or create beautiful media albums (up to 10 items)
- 🎨 **Template System**: Dynamic content generation with powerful templating
- 🔐 **Secure Sessions**: Encrypted session storage for multiple accounts
- 🚀 **Async/Await**: Modern asynchronous architecture for performance
- 💾 **Media Caching**: Smart caching system for media files
- 🛠️ **CLI Tool**: Complete command-line interface for all operations

## Installation

### From PyPI (when published)
```bash
pip install telegram-agentic-publisher
```

### From Source
```bash
git clone https://github.com/chubajs/telegram-agentic-publisher.git
cd telegram-agentic-publisher
pip install -e .
```

### Requirements
- Python 3.8+
- Telegram API credentials (get from https://my.telegram.org/apps)

## Quick Start

### 1. Set Up Configuration

Create a `.env` file with your Telegram API credentials:

```env
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash
```

### 2. Authenticate

```bash
# Authenticate with your phone number
telegram-publisher auth -p +1234567890 -n "My Session"
```

### 3. Post Content

```bash
# Simple text post
telegram-publisher post @channelname -t "Hello, World!"

# With media
telegram-publisher post @channelname -t "Check out this image!" -m photo.jpg

# Multiple media (gallery)
telegram-publisher post @channelname -t "Photo gallery" -m pic1.jpg -m pic2.jpg -m pic3.jpg
```

## Usage Examples

### Python API

```python
import asyncio
from telegram_agentic_publisher import TelegramPublisher, SessionManager
from telegram_agentic_publisher.utils import Config

async def main():
    # Load configuration
    config = Config()

    # Create session manager
    session_mgr = SessionManager(
        storage_path=config.session_storage_path,
        encryption_key=config.session_encryption_key
    )

    # Get or create session
    sessions = session_mgr.list_sessions()
    if sessions:
        session_id = sessions[0]["id"]
    else:
        # Need to authenticate first
        from telegram_agentic_publisher import TelegramAuthenticator

        auth = TelegramAuthenticator(config.api_id, config.api_hash)
        user_info = await auth.authenticate("+1234567890")
        session_id = session_mgr.create_session(
            "My Session",
            "+1234567890",
            auth.get_session_string(),
            user_info
        )

    # Create publisher
    publisher = TelegramPublisher(
        api_id=config.api_id,
        api_hash=config.api_hash,
        session_id=session_id,
        session_manager=session_mgr
    )

    # Connect
    await publisher.connect()

    # Post with markdown formatting
    content = """
    **Bold Title**

    This is a post with *italic text* and a [link](https://example.com).

    `inline code` and even code blocks:

    ```python
    print("Hello, Telegram!")
    ```
    """

    message_id, message_url = await publisher.publish(
        channel="@mychannel",
        content=content,
        parse_mode="md"
    )

    print(f"Posted: {message_url}")

    # Disconnect
    await publisher.disconnect()

asyncio.run(main())
```

### Media Galleries

```python
# Post with media gallery
media_files = [
    "photo1.jpg",
    "photo2.jpg",
    "https://example.com/photo3.jpg",  # URLs are supported
]

message_id, message_url = await publisher.publish(
    channel="@mychannel",
    content="Check out these photos! 📸",
    media=media_files
)
```

### Templates

Create dynamic content with templates:

```python
# Template with placeholders
template = """
📢 **{title}**

{description}

{?has_link}
🔗 Read more: {link}
{/has_link}

{#tags}#{.} {/tags}
"""

# Data for template
data = {
    "title": "Important Announcement",
    "description": "This is a templated message",
    "has_link": True,
    "link": "https://co.actor",
    "tags": ["news", "update", "telegram"]
}

message_id, message_url = await publisher.publish(
    channel="@mychannel",
    template=template,
    template_data=data
)
```

## CLI Reference

### Authentication

```bash
# Basic authentication
telegram-publisher auth --phone +1234567890

# With custom session name
telegram-publisher auth --phone +1234567890 --name "Work Account"
```

### Session Management

```bash
# List all sessions
telegram-publisher sessions

# Use specific session for posting
telegram-publisher post @channel -s "Work Account" -t "Hello"
```

### Posting

```bash
# Text post
telegram-publisher post @channel -t "Your message"

# From file
telegram-publisher post @channel -f message.txt

# With media
telegram-publisher post @channel -t "Caption" -m image.jpg

# Multiple media
telegram-publisher post @channel -m img1.jpg -m img2.jpg -m img3.jpg

# Silent post (no notification)
telegram-publisher post @channel -t "Silent message" --silent

# Disable link preview
telegram-publisher post @channel -t "https://example.com" --no-preview
```

### Channel Information

```bash
# Get channel info
telegram-publisher info @channelname

# With specific session
telegram-publisher info @channelname -s "Session Name"
```

## Advanced Features

### Markdown Formatting

The library supports full Telegram markdown:

- **Bold**: `**text**`
- *Italic*: `*text*` or `_text_`
- __Underline__: `__text__`
- ~~Strikethrough~~: `~~text~~`
- `Code`: `` `code` ``
- [Links](url): `[text](url)`
- Code blocks: `` ```language\ncode\n``` ``
- > Quotes: `> quoted text`

### Template System

Templates support various features:

#### Variables
```
Hello {name}!
Your email: {user.email}
```

#### Filters
```
{name|upper}        # UPPERCASE
{name|lower}        # lowercase
{name|title}        # Title Case
{text|truncate:50}  # Truncate to 50 chars
{date|date:%Y-%m-%d} # Format date
{text|escape_md}    # Escape markdown
```

#### Conditionals
```
{?has_image}
Image: {image_url}
{/has_image}

{?!is_public}
This is a private message
{/is_public}
```

#### Loops
```
Tags:
{#tags}
- {.}
{/tags}

Users:
{#users}
Name: {name}, Age: {age}
{/users}
```

### Media Handling

- Automatic image optimization
- Support for photos, videos, and documents
- Media caching to avoid re-downloads
- Gallery creation (up to 10 items)
- Mixed local files and URLs

### Session Security

- Encrypted session storage
- Session expiration detection
- Multiple account support
- Session status tracking
- Usage statistics

## Configuration

All configuration can be done via environment variables or `.env` file:

```env
# Required
TELEGRAM_API_ID=12345678
TELEGRAM_API_HASH=your_api_hash

# Optional
SESSION_ENCRYPTION_KEY=your_encryption_key
SESSION_STORAGE_PATH=./data/sessions/
MEDIA_CACHE_PATH=./data/media_cache/
LOG_LEVEL=INFO
LOG_FILE=./logs/telegram_publisher.log
```

## Architecture

The library is organized into modular components:

- **Core**: Main publisher and template processor
- **Auth**: Authentication and session management
- **Formatting**: Markdown processing and entity conversion
- **Media**: Media handling, downloading, and optimization
- **Utils**: Configuration, logging, and encryption

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

### Development Setup

```bash
# Clone repository
git clone https://github.com/chubajs/telegram-agentic-publisher.git
cd telegram-agentic-publisher

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e .[dev]

# Run tests
pytest
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Built with [Telethon](https://github.com/LonamiWebs/Telethon)
- Inspired by the scheduler project's Telegram publishing needs
- Thanks to all contributors

## Author

**Serge Bulaev**
- 🌐 Website: [https://co.actor](https://co.actor)
- 💼 LinkedIn: [https://www.linkedin.com/in/sbulaev/](https://www.linkedin.com/in/sbulaev/)
- 🐙 GitHub: [@chubajs](https://github.com/chubajs)
- 📧 Email: serge@bulaev.net

## Support

For issues and questions:
- GitHub Issues: [Create an issue](https://github.com/chubajs/telegram-agentic-publisher/issues)
- Documentation: [Full docs](https://github.com/chubajs/telegram-agentic-publisher/wiki)

## Disclaimer

This tool uses Telegram user accounts for posting. Please ensure you comply with Telegram's Terms of Service and use this tool responsibly. The authors are not responsible for any misuse or violations of Telegram's policies.