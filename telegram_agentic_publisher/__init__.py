"""
Telegram Agentic Publisher

An open-source library for posting to Telegram channels via authorized user accounts.
Supports rich formatting, media galleries, and template-based content generation.

Author: Serge Bulaev (https://bulaev.net)
License: MIT
"""

__version__ = "1.0.0"
__author__ = "Serge Bulaev"
__email__ = "serge@bulaev.net"
__website__ = "https://bulaev.net"

from .core.publisher import TelegramPublisher
from .auth.authenticator import TelegramAuthenticator
from .auth.session_manager import SessionManager
from .formatting.markdown_processor import MarkdownProcessor
from .media.media_handler import MediaHandler

__all__ = [
    "TelegramPublisher",
    "TelegramAuthenticator",
    "SessionManager",
    "MarkdownProcessor",
    "MediaHandler",
]