"""Main Telegram publisher class."""

from typing import Optional, Dict, Any, List, Union, Tuple
from pathlib import Path
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import (
    ChatWriteForbiddenError,
    ChannelPrivateError,
    MessageTooLongError,
    MediaInvalidError,
)
from ..auth.session_manager import SessionManager
from ..formatting.markdown_processor import MarkdownProcessor
from ..media.media_handler import MediaHandler
from .template_processor import TemplateProcessor
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class TelegramPublisher:
    """Main class for publishing to Telegram channels."""

    def __init__(
        self,
        api_id: str,
        api_hash: str,
        session_string: Optional[str] = None,
        session_id: Optional[str] = None,
        session_manager: Optional[SessionManager] = None,
    ):
        """
        Initialize Telegram publisher.

        Args:
            api_id: Telegram API ID
            api_hash: Telegram API hash
            session_string: Optional session string for authentication
            session_id: Optional session ID if using SessionManager
            session_manager: Optional SessionManager instance
        """
        self.api_id = int(api_id)
        self.api_hash = api_hash
        self.session_string = session_string
        self.session_id = session_id
        self.session_manager = session_manager
        self.client: Optional[TelegramClient] = None
        self.markdown_processor = MarkdownProcessor()
        self.media_handler = MediaHandler()
        self.template_processor = TemplateProcessor()
        self.connected = False

    async def connect(self) -> bool:
        """
        Connect to Telegram.

        Returns:
            True if connected successfully
        """
        try:
            # Create client from session
            if self.session_id and self.session_manager:
                self.client = self.session_manager.create_client(
                    self.session_id, str(self.api_id), self.api_hash
                )
                if not self.client:
                    logger.error("Failed to create client from session manager")
                    return False
            elif self.session_string:
                self.client = TelegramClient(
                    StringSession(self.session_string), self.api_id, self.api_hash
                )
            else:
                logger.error("No session provided for connection")
                return False

            # Connect to Telegram
            await self.client.connect()

            # Check authorization
            if not await self.client.is_user_authorized():
                logger.error("Session is not authorized")
                if self.session_id and self.session_manager:
                    self.session_manager.update_session_status(self.session_id, "expired")
                return False

            # Get user info for logging
            me = await self.client.get_me()
            logger.info(f"Connected as @{me.username} ({me.first_name})")

            # Update session last used
            if self.session_id and self.session_manager:
                self.session_manager.update_last_used(self.session_id)

            self.connected = True
            return True

        except Exception as e:
            logger.error(f"Connection failed: {e}")
            return False

    async def publish(
        self,
        channel: Union[str, int],
        content: Optional[str] = None,
        media: Optional[Union[List, str, Path]] = None,
        template: Optional[str] = None,
        template_data: Optional[Dict[str, Any]] = None,
        parse_mode: Optional[str] = "md",
        link_preview: bool = False,
        silent: bool = False,
        schedule: Optional[int] = None,
    ) -> Tuple[Optional[int], Optional[str]]:
        """
        Publish content to a Telegram channel.

        Args:
            channel: Channel ID or username
            content: Text content (can contain markdown)
            media: Optional media (list of files/URLs or single file/URL)
            template: Optional template string
            template_data: Data for template processing
            parse_mode: Parse mode ('md' for markdown, 'html', or None)
            link_preview: Whether to show link previews
            silent: Send silently (no notification)
            schedule: Optional Unix timestamp for scheduled posting

        Returns:
            Tuple of (message_id, message_url) or (None, None) if failed
        """
        if not self.connected:
            logger.error("Not connected to Telegram")
            return None, None

        try:
            # Process template if provided
            if template and template_data:
                content = self.template_processor.process(template, template_data)
                logger.debug(f"Processed template, content length: {len(content)}")

            # Process markdown if enabled
            if content and parse_mode == "md":
                content = self.markdown_processor.fix_telethon_markdown(content)

            # Handle channel ID format
            if isinstance(channel, str) and channel.startswith("-100"):
                try:
                    channel = int(channel)
                except ValueError:
                    pass  # Keep as string (username)

            # Prepare media if provided
            media_files = None
            if media:
                if not isinstance(media, list):
                    media = [media]

                media_files, _ = await self.media_handler.prepare_media(media)
                logger.info(f"Prepared {len(media_files)} media files")

            # Send message based on content type
            if media_files and len(media_files) > 0:
                result = await self._send_with_media(
                    channel, content, media_files, parse_mode, link_preview, silent, schedule
                )
            elif content:
                result = await self._send_text_only(
                    channel, content, parse_mode, link_preview, silent, schedule
                )
            else:
                logger.error("No content or media to send")
                return None, None

            # Extract message info
            if result:
                message_id = result.id
                message_url = self._build_message_url(channel, message_id)
                logger.info(f"Published successfully: {message_url}")
                return message_id, message_url

            return None, None

        except ChatWriteForbiddenError:
            logger.error(f"No permission to write to channel {channel}")
            return None, None

        except ChannelPrivateError:
            logger.error(f"Channel {channel} is private or doesn't exist")
            return None, None

        except MessageTooLongError:
            logger.error("Message is too long (max 4096 characters)")
            return None, None

        except MediaInvalidError as e:
            logger.error(f"Media is invalid: {e}")
            return None, None

        except Exception as e:
            logger.error(f"Publishing failed: {e}")
            return None, None

    async def _send_text_only(
        self,
        channel: Union[str, int],
        content: str,
        parse_mode: Optional[str],
        link_preview: bool,
        silent: bool,
        schedule: Optional[int],
    ):
        """Send text-only message."""
        # Check message length
        if len(content) > 4096:
            logger.warning(f"Message too long ({len(content)}), truncating")
            content = content[:4090] + "..."

        return await self.client.send_message(
            channel,
            content,
            parse_mode=parse_mode,
            link_preview=link_preview,
            silent=silent,
            schedule=schedule,
        )

    async def _send_with_media(
        self,
        channel: Union[str, int],
        caption: Optional[str],
        media_files: List[Path],
        parse_mode: Optional[str],
        link_preview: bool,
        silent: bool,
        schedule: Optional[int],
    ):
        """Send message with media."""
        # Check caption length for media
        max_caption_length = 4096 if len(media_files) > 1 else 1024

        if caption and len(caption) > max_caption_length:
            logger.warning(f"Caption too long ({len(caption)}), truncating")
            caption = caption[: max_caption_length - 3] + "..."

        # Upload and send media
        uploaded_files = []
        for media_file in media_files:
            try:
                uploaded = await self.client.upload_file(media_file)
                uploaded_files.append(uploaded)
            except Exception as e:
                logger.error(f"Failed to upload {media_file}: {e}")

        if not uploaded_files:
            logger.error("No files were uploaded successfully")
            return None

        # Send as album or single file
        return await self.client.send_file(
            channel,
            file=uploaded_files,
            caption=caption,
            parse_mode=parse_mode if caption else None,
            link_preview=link_preview,
            silent=silent,
            schedule=schedule,
        )

    def _build_message_url(self, channel: Union[str, int], message_id: int) -> str:
        """
        Build Telegram message URL.

        Args:
            channel: Channel ID or username
            message_id: Message ID

        Returns:
            Message URL
        """
        if isinstance(channel, int):
            # Channel ID - extract channel number
            channel_id = str(channel).replace("-100", "")
            return f"https://t.me/c/{channel_id}/{message_id}"
        else:
            # Username
            username = str(channel).replace("@", "")
            return f"https://t.me/{username}/{message_id}"

    async def get_channel_info(self, channel: Union[str, int]) -> Optional[Dict[str, Any]]:
        """
        Get information about a channel.

        Args:
            channel: Channel ID or username

        Returns:
            Channel information dictionary or None
        """
        if not self.connected:
            logger.error("Not connected to Telegram")
            return None

        try:
            entity = await self.client.get_entity(channel)
            return {
                "id": entity.id,
                "title": getattr(entity, "title", "Unknown"),
                "username": getattr(entity, "username", None),
                "participants_count": getattr(entity, "participants_count", 0),
                "is_channel": getattr(entity, "broadcast", False),
                "is_group": getattr(entity, "megagroup", False),
                "is_private": not getattr(entity, "username", None),
            }
        except Exception as e:
            logger.error(f"Failed to get channel info for {channel}: {e}")
            return None

    async def get_me(self) -> Optional[Dict[str, Any]]:
        """
        Get information about the authenticated user.

        Returns:
            User information dictionary or None
        """
        if not self.connected:
            logger.error("Not connected to Telegram")
            return None

        try:
            me = await self.client.get_me()
            return {
                "id": me.id,
                "username": me.username or "",
                "first_name": me.first_name or "",
                "last_name": me.last_name or "",
                "phone": me.phone or "",
            }
        except Exception as e:
            logger.error(f"Failed to get user info: {e}")
            return None

    async def disconnect(self):
        """Disconnect from Telegram."""
        if self.client:
            await self.client.disconnect()
            self.connected = False
            logger.info("Disconnected from Telegram")

        # Clean up media handler
        await self.media_handler.cleanup()

    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()
