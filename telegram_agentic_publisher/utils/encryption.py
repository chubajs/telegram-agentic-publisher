"""Encryption utilities for session management."""

import os
import base64
import json
from pathlib import Path
from typing import Dict, Any, Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class Encryption:
    """Handles encryption and decryption of sensitive session data."""

    def __init__(self, key: Optional[str] = None):
        """
        Initialize encryption with a key.

        Args:
            key: Encryption key (will be generated if not provided)
        """
        if key:
            self.key = key.encode() if isinstance(key, str) else key
        else:
            self.key = self._generate_key()

        # Derive a proper Fernet key from the provided key
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b"telegram_publisher_salt",  # Static salt for consistency
            iterations=100000,
        )
        key_bytes = base64.urlsafe_b64encode(kdf.derive(self.key[:32].ljust(32, b'\0')))
        self.fernet = Fernet(key_bytes)

    def _generate_key(self) -> bytes:
        """
        Generate a random encryption key.

        Returns:
            Random encryption key
        """
        return Fernet.generate_key()

    def encrypt_string(self, data: str) -> str:
        """
        Encrypt a string.

        Args:
            data: String to encrypt

        Returns:
            Base64 encoded encrypted string
        """
        encrypted = self.fernet.encrypt(data.encode())
        return base64.b64encode(encrypted).decode()

    def decrypt_string(self, encrypted_data: str) -> str:
        """
        Decrypt a string.

        Args:
            encrypted_data: Base64 encoded encrypted string

        Returns:
            Decrypted string
        """
        encrypted = base64.b64decode(encrypted_data.encode())
        decrypted = self.fernet.decrypt(encrypted)
        return decrypted.decode()

    def encrypt_dict(self, data: Dict[str, Any]) -> str:
        """
        Encrypt a dictionary.

        Args:
            data: Dictionary to encrypt

        Returns:
            Base64 encoded encrypted JSON string
        """
        json_str = json.dumps(data)
        return self.encrypt_string(json_str)

    def decrypt_dict(self, encrypted_data: str) -> Dict[str, Any]:
        """
        Decrypt a dictionary.

        Args:
            encrypted_data: Base64 encoded encrypted JSON string

        Returns:
            Decrypted dictionary
        """
        json_str = self.decrypt_string(encrypted_data)
        return json.loads(json_str)

    def encrypt_file(self, file_path: Path, output_path: Optional[Path] = None) -> Path:
        """
        Encrypt a file.

        Args:
            file_path: Path to file to encrypt
            output_path: Optional output path (defaults to file_path.enc)

        Returns:
            Path to encrypted file
        """
        if not output_path:
            output_path = file_path.with_suffix(file_path.suffix + ".enc")

        with open(file_path, "rb") as f:
            data = f.read()

        encrypted = self.fernet.encrypt(data)

        with open(output_path, "wb") as f:
            f.write(encrypted)

        return output_path

    def decrypt_file(self, file_path: Path, output_path: Optional[Path] = None) -> Path:
        """
        Decrypt a file.

        Args:
            file_path: Path to encrypted file
            output_path: Optional output path

        Returns:
            Path to decrypted file
        """
        if not output_path:
            # Remove .enc extension if present
            if file_path.suffix == ".enc":
                output_path = file_path.with_suffix("")
            else:
                output_path = file_path.with_suffix(".dec")

        with open(file_path, "rb") as f:
            encrypted = f.read()

        decrypted = self.fernet.decrypt(encrypted)

        with open(output_path, "wb") as f:
            f.write(decrypted)

        return output_path