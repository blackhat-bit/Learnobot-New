"""
Encryption service for sensitive data (API keys, secrets).
Uses Fernet symmetric encryption from cryptography library.
"""
from cryptography.fernet import Fernet, InvalidToken
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class EncryptionService:
    """Service for encrypting/decrypting sensitive data like API keys"""
    
    def __init__(self, encryption_key: Optional[str] = None):
        """
        Initialize encryption service.
        
        Args:
            encryption_key: Base64-encoded Fernet key. If None, operates in plain-text mode (dev only).
        """
        self.cipher = None
        
        if encryption_key:
            try:
                self.cipher = Fernet(encryption_key.encode())
                logger.info("✅ Encryption service initialized with key")
            except Exception as e:
                logger.error(f"❌ Failed to initialize encryption cipher: {e}")
                logger.warning("⚠️  Falling back to plain-text mode (INSECURE)")
        else:
            logger.warning("⚠️  No ENCRYPTION_KEY configured - API keys stored in PLAIN TEXT (dev mode only)")
    
    def encrypt(self, plain_text: str) -> Optional[str]:
        """
        Encrypt a string (like an API key).
        
        Args:
            plain_text: The text to encrypt
            
        Returns:
            Encrypted string (base64), or plain text if encryption not available
        """
        if not plain_text:
            return None
            
        if self.cipher is None:
            # Development mode - no encryption
            logger.debug("Storing value without encryption (dev mode)")
            return plain_text
        
        try:
            encrypted_bytes = self.cipher.encrypt(plain_text.encode())
            return encrypted_bytes.decode()
        except Exception as e:
            logger.error(f"❌ Encryption failed: {e}")
            logger.warning("Falling back to plain text storage (INSECURE)")
            return plain_text
    
    def decrypt(self, encrypted_text: str) -> Optional[str]:
        """
        Decrypt a string to get original value.
        
        Args:
            encrypted_text: The encrypted text (or plain text if encryption wasn't used)
            
        Returns:
            Decrypted string, or the original text if decryption fails (backwards compatibility)
        """
        if not encrypted_text:
            return None
            
        if self.cipher is None:
            # Development mode - no encryption was used
            logger.debug("Retrieving value without decryption (dev mode)")
            return encrypted_text
        
        try:
            decrypted_bytes = self.cipher.decrypt(encrypted_text.encode())
            return decrypted_bytes.decode()
        except InvalidToken:
            # This is likely plain text from before encryption was enabled
            logger.warning(f"⚠️  Decryption failed - value appears to be plain text (migration needed)")
            return encrypted_text
        except Exception as e:
            logger.error(f"❌ Decryption error: {e}")
            return None
    
    def is_encrypted(self) -> bool:
        """Check if encryption is enabled"""
        return self.cipher is not None


# Global instance - will be initialized in main.py with config
encryption_service: Optional[EncryptionService] = None


def init_encryption_service(encryption_key: Optional[str] = None) -> EncryptionService:
    """
    Initialize the global encryption service.
    Should be called during application startup.
    
    Args:
        encryption_key: The encryption key from config
        
    Returns:
        The initialized EncryptionService instance
    """
    global encryption_service
    encryption_service = EncryptionService(encryption_key)
    return encryption_service


def get_encryption_service() -> EncryptionService:
    """
    Get the global encryption service instance.
    
    Returns:
        The EncryptionService instance
        
    Raises:
        RuntimeError: If service hasn't been initialized
    """
    if encryption_service is None:
        raise RuntimeError("Encryption service not initialized. Call init_encryption_service() first.")
    return encryption_service

