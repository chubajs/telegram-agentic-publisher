"""Session management for persistent storage."""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
from telethon import TelegramClient
from telethon.sessions import StringSession
from ..utils.encryption import Encryption
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class SessionManager:
    """Manages Telegram sessions with encrypted storage."""

    def __init__(self, storage_path: Path, encryption_key: Optional[str] = None):
        """
        Initialize session manager.

        Args:
            storage_path: Path to store session files
            encryption_key: Optional encryption key for sessions
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.encryption = Encryption(encryption_key) if encryption_key else None
        self.sessions_file = self.storage_path / "sessions.json"
        self.sessions: Dict[str, Dict[str, Any]] = self._load_sessions()

    def _load_sessions(self) -> Dict[str, Dict[str, Any]]:
        """
        Load sessions from storage.

        Returns:
            Dictionary of session configurations
        """
        if not self.sessions_file.exists():
            return {}

        try:
            with open(self.sessions_file, "r") as f:
                data = json.load(f)

            # Decrypt session strings if encryption is enabled
            if self.encryption:
                for session_id, session_data in data.items():
                    if "session_string" in session_data:
                        try:
                            session_data["session_string"] = self.encryption.decrypt_string(
                                session_data["session_string"]
                            )
                        except Exception as e:
                            logger.warning(f"Failed to decrypt session {session_id}: {e}")
                            session_data["status"] = "corrupted"

            return data

        except Exception as e:
            logger.error(f"Failed to load sessions: {e}")
            return {}

    def _save_sessions(self):
        """Save sessions to storage."""
        try:
            # Create a copy for saving
            save_data = {}
            for session_id, session_data in self.sessions.items():
                save_data[session_id] = session_data.copy()

                # Encrypt session strings if encryption is enabled
                if self.encryption and "session_string" in save_data[session_id]:
                    save_data[session_id]["session_string"] = self.encryption.encrypt_string(
                        save_data[session_id]["session_string"]
                    )

            with open(self.sessions_file, "w") as f:
                json.dump(save_data, f, indent=2)

            logger.debug(f"Saved {len(self.sessions)} sessions")

        except Exception as e:
            logger.error(f"Failed to save sessions: {e}")

    def create_session(
        self,
        session_name: str,
        phone: str,
        session_string: str,
        user_info: Dict[str, Any],
    ) -> str:
        """
        Create a new session.

        Args:
            session_name: Human-readable session name
            phone: Phone number
            session_string: Telethon session string
            user_info: User information dictionary

        Returns:
            Session ID
        """
        # Generate session ID
        session_id = f"session_{int(datetime.now().timestamp())}"

        # Create session record
        self.sessions[session_id] = {
            "id": session_id,
            "name": session_name,
            "phone": phone,
            "session_string": session_string,
            "user_info": user_info,
            "created_at": datetime.now().isoformat(),
            "last_used": datetime.now().isoformat(),
            "status": "active",
            "usage_count": 0,
        }

        self._save_sessions()
        logger.info(f"Created session '{session_name}' with ID {session_id}")
        return session_id

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get session by ID.

        Args:
            session_id: Session ID

        Returns:
            Session data or None if not found
        """
        return self.sessions.get(session_id)

    def get_session_by_name(self, session_name: str) -> Optional[Dict[str, Any]]:
        """
        Get session by name.

        Args:
            session_name: Session name

        Returns:
            Session data or None if not found
        """
        for session in self.sessions.values():
            if session.get("name") == session_name:
                return session
        return None

    def list_sessions(self) -> List[Dict[str, Any]]:
        """
        List all sessions.

        Returns:
            List of session summaries
        """
        sessions_list = []
        for session_id, session_data in self.sessions.items():
            sessions_list.append({
                "id": session_id,
                "name": session_data.get("name", "Unknown"),
                "username": session_data.get("user_info", {}).get("username", ""),
                "phone": session_data.get("phone", ""),
                "status": session_data.get("status", "unknown"),
                "created_at": session_data.get("created_at", ""),
                "last_used": session_data.get("last_used", ""),
                "usage_count": session_data.get("usage_count", 0),
            })
        return sessions_list

    def update_session_status(self, session_id: str, status: str):
        """
        Update session status.

        Args:
            session_id: Session ID
            status: New status (active, expired, revoked, corrupted)
        """
        if session_id in self.sessions:
            self.sessions[session_id]["status"] = status
            self._save_sessions()
            logger.info(f"Updated session {session_id} status to {status}")

    def update_last_used(self, session_id: str):
        """
        Update session last used timestamp.

        Args:
            session_id: Session ID
        """
        if session_id in self.sessions:
            self.sessions[session_id]["last_used"] = datetime.now().isoformat()
            self.sessions[session_id]["usage_count"] = (
                self.sessions[session_id].get("usage_count", 0) + 1
            )
            self._save_sessions()

    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session.

        Args:
            session_id: Session ID

        Returns:
            True if deleted successfully
        """
        if session_id in self.sessions:
            del self.sessions[session_id]
            self._save_sessions()
            logger.info(f"Deleted session {session_id}")
            return True
        return False

    def create_client(
        self, session_id: str, api_id: str, api_hash: str
    ) -> Optional[TelegramClient]:
        """
        Create a Telegram client from a saved session.

        Args:
            session_id: Session ID
            api_id: Telegram API ID
            api_hash: Telegram API hash

        Returns:
            TelegramClient instance or None if session not found
        """
        session_data = self.get_session(session_id)
        if not session_data:
            logger.error(f"Session {session_id} not found")
            return None

        session_string = session_data.get("session_string")
        if not session_string:
            logger.error(f"Session {session_id} has no session string")
            return None

        try:
            client = TelegramClient(
                StringSession(session_string),
                int(api_id),
                api_hash
            )
            return client

        except Exception as e:
            logger.error(f"Failed to create client for session {session_id}: {e}")
            self.update_session_status(session_id, "corrupted")
            return None