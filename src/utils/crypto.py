"""
Simple encryption helpers using Fernet.

We derive a 32-byte base64 key from the configured `security.secret_key` so
projects don't need to store a second key. This is convenient for development
but for production you may want to use a dedicated encryption key.
"""
from typing import Optional
import hashlib
import base64
from cryptography.fernet import Fernet
from src.utils.config_loader import ConfigLoader


def _get_fernet() -> Fernet:
    cfg = ConfigLoader()
    sec = cfg.get_security_config()
    raw = sec.get("secret_key") or ""
    # Derive 32 bytes key and base64-url-safe encode
    key_bytes = hashlib.sha256(raw.encode("utf-8")).digest()
    b64 = base64.urlsafe_b64encode(key_bytes)
    return Fernet(b64)


def encrypt_value(plaintext: str) -> str:
    f = _get_fernet()
    token = f.encrypt(plaintext.encode("utf-8"))
    return token.decode("utf-8")


def decrypt_value(token: str) -> Optional[str]:
    f = _get_fernet()
    try:
        val = f.decrypt(token.encode("utf-8"))
        return val.decode("utf-8")
    except Exception:
        return None


__all__ = ["encrypt_value", "decrypt_value"]
