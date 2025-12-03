"""
Security & JWT
==============

JWT token generation and validation, password hashing.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
import jwt
import logging
from passlib.context import CryptContext
from src.utils import ConfigLoader

logger = logging.getLogger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT config - read from YAML security section (single source of truth)
cfg = ConfigLoader()
sec = cfg.get_security_config()
SECRET_KEY = sec.get("secret_key") or "dev-secret-key-change-in-production-12345"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(sec.get("access_token_expire_minutes", 30))
REFRESH_TOKEN_EXPIRE_DAYS = int(sec.get("refresh_token_expire_days", 7))


class SecurityService:
    """Security and authentication service"""

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password with bcrypt"""
        try:
            return pwd_context.hash(password)
        except Exception:
            # Fallback to a safe alternative if bcrypt backend fails in this env
            alt = CryptContext(schemes=["sha256_crypt"], deprecated="auto")
            return alt.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        try:
            return pwd_context.verify(plain_password, hashed_password)
        except Exception:
            alt = CryptContext(schemes=["sha256_crypt"], deprecated="auto")
            try:
                return alt.verify(plain_password, hashed_password)
            except Exception:
                return False

    @staticmethod
    def create_access_token(
        data: Dict[str, Any],
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Create JWT access token
        
        Args:
            data: Payload data
            expires_delta: Optional expiration delta
            
        Returns:
            JWT token string
        """
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        
        logger.info(f"✅ Access token created for user: {data.get('sub')}")
        return encoded_jwt

    @staticmethod
    def create_refresh_token(data: Dict[str, Any]) -> str:
        """Create JWT refresh token"""
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode.update({"exp": expire, "type": "refresh"})
        
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        logger.info(f"✅ Refresh token created for user: {data.get('sub')}")
        return encoded_jwt

    @staticmethod
    def verify_token(token: str) -> Optional[Dict[str, Any]]:
        """
        Verify and decode JWT token
        
        Args:
            token: JWT token string
            
        Returns:
            Decoded payload or None
        """
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Token has expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {str(e)}")
            return None

    @staticmethod
    def extract_user_id_from_token(token: str) -> Optional[int]:
        """Extract user ID from token"""
        payload = SecurityService.verify_token(token)
        if payload:
            return payload.get("user_id")
        return None
