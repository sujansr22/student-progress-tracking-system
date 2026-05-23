import logging
from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy import TypeDecorator, Text

logger = logging.getLogger(__name__)

_fernet: Fernet | None = None


def _get_fernet() -> Fernet:
    global _fernet
    if _fernet is None:
        from app.core.config import settings
        _fernet = Fernet(settings.ENCRYPTION_KEY.encode())
    return _fernet


class EncryptedText(TypeDecorator):
    """
    SQLAlchemy column type that transparently encrypts on write and decrypts on read.
    Underlying DB column stays TEXT — no schema migration needed.
    """
    impl = Text
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return _get_fernet().encrypt(value.encode()).decode()

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        try:
            return _get_fernet().decrypt(value.encode()).decode()
        except (InvalidToken, Exception):
            # Fallback for any plain-text rows that existed before encryption was added
            logger.warning("EncryptedText: decryption failed, returning raw value")
            return value
