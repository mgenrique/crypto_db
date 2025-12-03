"""
Authentication Service
======================

User registration, login, API key management.
"""

from sqlalchemy.orm import Session
from typing import Optional, Dict, Any, Tuple
import logging

from src.auth.security import SecurityService

logger = logging.getLogger(__name__)


class AuthService:
    """Authentication service"""

    def __init__(self, db_manager):
        self.db_manager = db_manager

    def register_user(self, email: str, username: str, password: str) -> Dict[str, Any]:
        """
        Register new user
        
        Args:
            email: User email
            username: Username
            password: Plain password
            
        Returns:
            User info dict
        """
        raise NotImplementedError("DB-backed user registration is disabled in single-user mode")

    def authenticate_user(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """
        Authenticate user and return tokens
        
        Args:
            email: User email
            password: Plain password
            
        Returns:
            Dict with access_token, refresh_token, user_info or None
        """
        raise NotImplementedError("DB-backed authentication is disabled in single-user mode")

    def refresh_access_token(self, refresh_token: str) -> Optional[str]:
        """
        Refresh access token using refresh token
        
        Args:
            refresh_token: Refresh token
            
        Returns:
            New access token or None
        """
        raise NotImplementedError("DB-backed token refresh is disabled in single-user mode")

    def create_api_key(self, user_id: int, name: str) -> Dict[str, str]:
        """
        Create new API key for user
        
        Args:
            user_id: User ID
            name: API key name
            
        Returns:
            Dict with key and secret
        """
        raise NotImplementedError("DB-backed API key creation is disabled in single-user mode")

    def verify_api_key(self, key: str, secret: str) -> Optional[int]:
        """
        Verify API key and secret
        
        Args:
            key: API key
            secret: API secret
            
        Returns:
            User ID or None
        """
        raise NotImplementedError("DB-backed API key verification is disabled in single-user mode")

    def get_user_api_keys(self, user_id: int) -> list:
        """Get user's API keys"""
        raise NotImplementedError("DB-backed API key listing is disabled in single-user mode")


class SingleUserAuthService:
    """
    Single-user authentication service that validates credentials
    against environment variables (.env) instead of the database.
    """

    def __init__(self):
        from os import getenv
        self.admin_email = getenv("ADMIN_EMAIL")
        self.admin_username = getenv("ADMIN_USERNAME")
        # Prefer hashed password in env; support plain password for convenience
        self.admin_password_hash = getenv("ADMIN_PASSWORD_HASH")
        self.admin_password = getenv("ADMIN_PASSWORD")
        # Optional API key/secret single-user pair
        self.admin_api_key = getenv("ADMIN_API_KEY")
        self.admin_api_secret = getenv("ADMIN_API_SECRET")

    def authenticate_user(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """
        Authenticate against the single admin credentials stored in env.
        Returns token dict on success or None.
        """
        try:
            if not self.admin_email:
                logger.warning("Single-user admin email not configured")
                return None

            if email != self.admin_email:
                logger.warning(f"Failed login attempt for {email}")
                return None

            # Verify using hash if provided, otherwise compare plain
            if self.admin_password_hash:
                if not SecurityService.verify_password(password, self.admin_password_hash):
                    logger.warning(f"Failed login attempt for {email}")
                    return None
            else:
                if self.admin_password is None or password != self.admin_password:
                    logger.warning(f"Failed login attempt for {email}")
                    return None

            # Build tokens similar to multi-user service; use user_id 0
            access_token = SecurityService.create_access_token({
                "sub": self.admin_email,
                "user_id": 0,
                "username": self.admin_username or "admin",
                "type": "access"
            })

            refresh_token = SecurityService.create_refresh_token({
                "sub": self.admin_email,
                "user_id": 0,
                "type": "refresh"
            })

            logger.info(f"✅ Single-user authenticated: {self.admin_username}")

            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
                "user": {
                    "id": 0,
                    "email": self.admin_email,
                    "username": self.admin_username or "admin"
                }
            }
        except Exception as e:
            logger.error(f"❌ Error authenticating single-user: {str(e)}")
            return None

    def refresh_access_token(self, refresh_token: str) -> Optional[str]:
        try:
            payload = SecurityService.verify_token(refresh_token)
            if not payload or payload.get("type") != "refresh":
                logger.warning("Invalid refresh token")
                return None

            # No DB lookup needed - re-issue new access token
            access_token = SecurityService.create_access_token({
                "sub": payload.get("sub"),
                "user_id": payload.get("user_id", 0),
                "username": payload.get("username", self.admin_username or "admin"),
                "type": "access"
            })
            logger.info("✅ Single-user token refreshed")
            return access_token
        except Exception as e:
            logger.error(f"❌ Error refreshing single-user token: {str(e)}")
            return None

    def create_api_key(self, user_id: int, name: str) -> Dict[str, str]:
        # API key management backed by DB is not supported in single-user mode.
        raise NotImplementedError("API key creation is disabled in single-user mode")

    def verify_api_key(self, key: str, secret: str) -> Optional[int]:
        """
        Verify against single ADMIN_API_KEY/ADMIN_API_SECRET if configured.
        Returns user_id (0) if matches, otherwise None.
        """
        try:
            if self.admin_api_key and self.admin_api_secret:
                if key == self.admin_api_key and secret == self.admin_api_secret:
                    logger.info("✅ Single-user API key verified")
                    return 0
            logger.warning("Invalid API key/secret in single-user mode")
            return None
        except Exception as e:
            logger.error(f"❌ Error verifying single-user API key: {str(e)}")
            return None

    def get_user_api_keys(self, user_id: int) -> list:
        # Not supported in single-user mode
        return []
