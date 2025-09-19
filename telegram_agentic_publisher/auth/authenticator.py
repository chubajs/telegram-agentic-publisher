"""Telegram authentication module."""

import asyncio
import getpass
from typing import Optional, Dict, Any
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import (
    SessionPasswordNeededError,
    PhoneCodeInvalidError,
    PhoneNumberInvalidError,
    FloodWaitError,
)
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class TelegramAuthenticator:
    """Handles Telegram authentication and session management."""

    def __init__(self, api_id: str, api_hash: str):
        """
        Initialize authenticator.

        Args:
            api_id: Telegram API ID
            api_hash: Telegram API hash
        """
        self.api_id = int(api_id)
        self.api_hash = api_hash
        self.client: Optional[TelegramClient] = None
        self.session_string: Optional[str] = None

    async def authenticate(
        self,
        phone: str,
        session_string: Optional[str] = None,
        code_callback=None,
        password_callback=None,
    ) -> Dict[str, Any]:
        """
        Authenticate with Telegram.

        Args:
            phone: Phone number in international format
            session_string: Optional existing session string
            code_callback: Optional callback to get verification code
            password_callback: Optional callback to get 2FA password

        Returns:
            User information dictionary

        Raises:
            Various telethon errors on authentication failure
        """
        try:
            # Create client with string session
            if session_string:
                self.client = TelegramClient(
                    StringSession(session_string), self.api_id, self.api_hash
                )
            else:
                self.client = TelegramClient(
                    StringSession(), self.api_id, self.api_hash
                )

            await self.client.connect()

            # Check if already authorized
            if await self.client.is_user_authorized():
                logger.info("Already authorized with existing session")
                me = await self.client.get_me()
                self.session_string = self.client.session.save()
                return self._user_to_dict(me)

            # Send code request
            logger.info(f"Sending authentication code to {phone}")
            await self.client.send_code_request(phone)

            # Get verification code
            if code_callback:
                code = await code_callback()
            else:
                code = input("Enter the verification code: ").strip()

            try:
                # Try to sign in with code
                await self.client.sign_in(phone, code)

            except SessionPasswordNeededError:
                # 2FA is enabled
                logger.info("Two-factor authentication is required")
                if password_callback:
                    password = await password_callback()
                else:
                    password = getpass.getpass("Enter your 2FA password: ")
                await self.client.sign_in(password=password)

            except PhoneCodeInvalidError:
                raise ValueError("Invalid verification code")

            # Get user info
            me = await self.client.get_me()
            self.session_string = self.client.session.save()
            user_info = self._user_to_dict(me)

            logger.info(
                f"Successfully authenticated as {user_info['first_name']} "
                f"(@{user_info['username']})"
            )
            return user_info

        except PhoneNumberInvalidError:
            raise ValueError(f"Invalid phone number: {phone}")

        except FloodWaitError as e:
            raise RuntimeError(
                f"Too many attempts. Please wait {e.seconds} seconds and try again."
            )

        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            raise

    async def check_session(self, session_string: str) -> Optional[Dict[str, Any]]:
        """
        Check if a session is valid.

        Args:
            session_string: Session string to check

        Returns:
            User info if session is valid, None otherwise
        """
        try:
            client = TelegramClient(
                StringSession(session_string), self.api_id, self.api_hash
            )
            await client.connect()

            if await client.is_user_authorized():
                me = await client.get_me()
                await client.disconnect()
                return self._user_to_dict(me)

            await client.disconnect()
            return None

        except Exception as e:
            logger.warning(f"Session check failed: {e}")
            return None

    async def revoke_session(self, session_string: str) -> bool:
        """
        Revoke a session.

        Args:
            session_string: Session string to revoke

        Returns:
            True if successfully revoked
        """
        try:
            client = TelegramClient(
                StringSession(session_string), self.api_id, self.api_hash
            )
            await client.connect()

            if await client.is_user_authorized():
                await client.log_out()
                logger.info("Session successfully revoked")
                return True

            return False

        except Exception as e:
            logger.error(f"Failed to revoke session: {e}")
            return False

    def _user_to_dict(self, user) -> Dict[str, Any]:
        """
        Convert Telethon User object to dictionary.

        Args:
            user: Telethon User object

        Returns:
            User information dictionary
        """
        return {
            "id": user.id,
            "username": user.username or "",
            "first_name": user.first_name or "",
            "last_name": user.last_name or "",
            "phone": user.phone or "",
            "is_bot": user.bot,
            "is_verified": user.verified,
            "is_restricted": user.restricted,
            "is_scam": user.scam,
            "is_fake": user.fake,
        }

    def get_session_string(self) -> Optional[str]:
        """
        Get the current session string.

        Returns:
            Session string if authenticated, None otherwise
        """
        return self.session_string

    async def disconnect(self):
        """Disconnect the client."""
        if self.client:
            await self.client.disconnect()
            self.client = None