"""
Encryption utilities for secure local data storage.
"""

import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from typing import Union, Optional
import logging

logger = logging.getLogger(__name__)

class EncryptionManager:
    """Handles encryption and decryption of sensitive data."""

    def __init__(self, key: Optional[Union[str, bytes]] = None):
        """Initialize encryption manager with a key."""
        if key:
            self.fernet = Fernet(key.encode() if isinstance(key, str) else key)
        else:
            # Generate a new key if none provided
            self.fernet = Fernet(Fernet.generate_key())

    @classmethod
    def from_password(cls, password: str, salt: Optional[bytes] = None) -> "EncryptionManager":
        """Create encryption manager from a password."""
        if salt is None:
            salt = os.urandom(16)

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return cls(key)

    def encrypt_string(self, data: str) -> bytes:
        """Encrypt a string and return bytes."""
        if not data:
            return b""
        try:
            return self.fernet.encrypt(data.encode('utf-8'))
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise

    def decrypt_string(self, encrypted_data: bytes) -> str:
        """Decrypt bytes and return a string."""
        if not encrypted_data:
            return ""
        try:
            return self.fernet.decrypt(encrypted_data).decode('utf-8')
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise

    def encrypt_dict(self, data: dict) -> bytes:
        """Encrypt a dictionary as JSON."""
        import json
        json_str = json.dumps(data, ensure_ascii=False)
        return self.encrypt_string(json_str)

    def decrypt_dict(self, encrypted_data: bytes) -> dict:
        """Decrypt bytes and return a dictionary."""
        import json
        json_str = self.decrypt_string(encrypted_data)
        return json.loads(json_str) if json_str else {}

    def get_key(self) -> bytes:
        """Get the encryption key."""
        # This is for backup purposes only - handle with care
        return self.fernet._signing_key + self.fernet._encryption_key

class SecureStorage:
    """Wrapper for secure file-based storage."""

    def __init__(self, file_path: str, encryption_key: str):
        self.file_path = file_path
        self.encryption_manager = EncryptionManager(encryption_key)

        # Ensure parent directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

    def save(self, data: dict) -> bool:
        """Save encrypted data to file."""
        try:
            encrypted_data = self.encryption_manager.encrypt_dict(data)
            with open(self.file_path, 'wb') as f:
                f.write(encrypted_data)
            return True
        except Exception as e:
            logger.error(f"Failed to save secure data: {e}")
            return False

    def load(self) -> dict:
        """Load and decrypt data from file."""
        try:
            if not os.path.exists(self.file_path):
                return {}

            with open(self.file_path, 'rb') as f:
                encrypted_data = f.read()

            if not encrypted_data:
                return {}

            return self.encryption_manager.decrypt_dict(encrypted_data)
        except Exception as e:
            logger.error(f"Failed to load secure data: {e}")
            return {}

    def exists(self) -> bool:
        """Check if the secure file exists."""
        return os.path.exists(self.file_path)

    def delete(self) -> bool:
        """Delete the secure file."""
        try:
            if os.path.exists(self.file_path):
                os.remove(self.file_path)
            return True
        except Exception as e:
            logger.error(f"Failed to delete secure file: {e}")
            return False

def generate_key() -> str:
    """Generate a new Fernet key."""
    return Fernet.generate_key().decode()

def is_valid_key(key: str) -> bool:
    """Check if a key is valid for Fernet encryption."""
    try:
        Fernet(key.encode())
        return True
    except Exception:
        return False
