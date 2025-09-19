"""Configuration management for telegram-agentic-publisher."""

import os
from pathlib import Path
from typing import Optional, Dict, Any
from dotenv import load_dotenv


class Config:
    """Manages application configuration from environment variables."""

    def __init__(self, env_file: Optional[str] = None):
        """
        Initialize configuration.

        Args:
            env_file: Path to .env file (optional)
        """
        if env_file and Path(env_file).exists():
            load_dotenv(env_file)
        else:
            load_dotenv()

        # Telegram API credentials
        self.api_id = self._get_required("TELEGRAM_API_ID")
        self.api_hash = self._get_required("TELEGRAM_API_HASH")

        # Optional configurations with defaults
        self.session_encryption_key = os.getenv("SESSION_ENCRYPTION_KEY")
        self.session_storage_path = Path(os.getenv("SESSION_STORAGE_PATH", "./data/sessions/"))
        self.media_cache_path = Path(os.getenv("MEDIA_CACHE_PATH", "./data/media_cache/"))
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        self.log_file = os.getenv("LOG_FILE")

        # Create directories if they don't exist
        self.session_storage_path.mkdir(parents=True, exist_ok=True)
        self.media_cache_path.mkdir(parents=True, exist_ok=True)

        if self.log_file:
            log_dir = Path(self.log_file).parent
            log_dir.mkdir(parents=True, exist_ok=True)

    def _get_required(self, key: str) -> str:
        """
        Get required environment variable.

        Args:
            key: Environment variable name

        Returns:
            Environment variable value

        Raises:
            ValueError: If environment variable is not set
        """
        value = os.getenv(key)
        if not value:
            raise ValueError(f"Required environment variable {key} is not set")
        return value

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert configuration to dictionary.

        Returns:
            Configuration as dictionary
        """
        return {
            "api_id": self.api_id,
            "api_hash": "***" if self.api_hash else None,  # Hide sensitive data
            "session_encryption_key": "***" if self.session_encryption_key else None,
            "session_storage_path": str(self.session_storage_path),
            "media_cache_path": str(self.media_cache_path),
            "log_level": self.log_level,
            "log_file": self.log_file,
        }