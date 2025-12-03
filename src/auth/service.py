"""
Authentication Service
======================

User registration, login, API key management.
"""

from sqlalchemy.orm import Session
from typing import Optional, Dict, Any, Tuple
import logging

from src.auth.models import UserModel, APIKeyModel
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
        try:
            with self.db_manager.session_context() as session:
                # Check if email exists
                existing_email = session.query(UserModel).filter_by(email=email).first()
                if existing_email:
                    raise ValueError("Email already registered")
                
                # Check if username exists
                existing_username = session.query(UserModel).filter_by(username=username).first()
                if existing_username:
                    raise ValueError("Username already taken")
                
                # Hash password
                hashed_pwd = SecurityService.hash_password(password)
                
                # Create user
                user = UserModel(
                    email=email,
                    username=username,
                    hashed_password=hashed_pwd
                )
                session.add(user)
                session.flush()
                
                logger.info(f"✅ User registered: {username}")
                
                return {
                    "id": user.id,
                    "email": user.email,
                    "username": user.username,
                    "created_at": user.created_at.isoformat()
                }
        except ValueError as e:
            logger.error(f"Registration error: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"❌ Error registering user: {str(e)}")
            raise

    def authenticate_user(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """
        Authenticate user and return tokens
        
        Args:
            email: User email
            password: Plain password
            
        Returns:
            Dict with access_token, refresh_token, user_info or None
        """
        try:
            with self.db_manager.session_context() as session:
                user = session.query(UserModel).filter_by(email=email).first()
                
                if not user or not SecurityService.verify_password(password, user.hashed_password):
                    logger.warning(f"Failed login attempt for {email}")
                    return None
                
                if not user.is_active:
                    logger.warning(f"Inactive user login attempt: {email}")
                    return None
                
                # Create tokens
                access_token = SecurityService.create_access_token({
                    "sub": user.email,
                    "user_id": user.id,
                    "username": user.username,
                    "type": "access"
                })
                
                refresh_token = SecurityService.create_refresh_token({
                    "sub": user.email,
                    "user_id": user.id,
                    "type": "refresh"
                })
                
                logger.info(f"✅ User authenticated: {user.username}")
                
                return {
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "token_type": "bearer",
                    "user": {
                        "id": user.id,
                        "email": user.email,
                        "username": user.username
                    }
                }
        except Exception as e:
            logger.error(f"❌ Error authenticating user: {str(e)}")
            return None

    def refresh_access_token(self, refresh_token: str) -> Optional[str]:
        """
        Refresh access token using refresh token
        
        Args:
            refresh_token: Refresh token
            
        Returns:
            New access token or None
        """
        try:
            payload = SecurityService.verify_token(refresh_token)
            
            if not payload or payload.get("type") != "refresh":
                logger.warning("Invalid refresh token")
                return None
            
            user_id = payload.get("user_id")
            
            with self.db_manager.session_context() as session:
                user = session.query(UserModel).filter_by(id=user_id).first()
                
                if not user or not user.is_active:
                    logger.warning(f"Refresh token for invalid user: {user_id}")
                    return None
                
                # Create new access token
                access_token = SecurityService.create_access_token({
                    "sub": user.email,
                    "user_id": user.id,
                    "username": user.username,
                    "type": "access"
                })
                
                logger.info(f"✅ Token refreshed for user: {user.username}")
                return access_token
        except Exception as e:
            logger.error(f"❌ Error refreshing token: {str(e)}")
            return None

    def create_api_key(self, user_id: int, name: str) -> Dict[str, str]:
        """
        Create new API key for user
        
        Args:
            user_id: User ID
            name: API key name
            
        Returns:
            Dict with key and secret
        """
        try:
            with self.db_manager.session_context() as session:
                user = session.query(UserModel).filter_by(id=user_id).first()
                if not user:
                    raise ValueError("User not found")
                
                api_key = APIKeyModel(
                    user_id=user_id,
                    key=APIKeyModel.generate_key(),
                    secret=APIKeyModel.generate_secret(),
                    name=name
                )
                session.add(api_key)
                session.flush()
                
                logger.info(f"✅ API key created for user {user.username}: {name}")
                
                return {
                    "key": api_key.key,
                    "secret": api_key.secret,
                    "name": api_key.name,
                    "created_at": api_key.created_at.isoformat()
                }
        except Exception as e:
            logger.error(f"❌ Error creating API key: {str(e)}")
            raise

    def verify_api_key(self, key: str, secret: str) -> Optional[int]:
        """
        Verify API key and secret
        
        Args:
            key: API key
            secret: API secret
            
        Returns:
            User ID or None
        """
        try:
            with self.db_manager.session_context() as session:
                api_key = session.query(APIKeyModel).filter_by(key=key).first()
                
                if not api_key or not api_key.is_active:
                    logger.warning(f"Invalid API key: {key[:10]}...")
                    return None
                
                if api_key.secret != secret:
                    logger.warning(f"Invalid API secret for key: {key[:10]}...")
                    return None
                
                # Update last_used
                from datetime import datetime
                api_key.last_used = datetime.utcnow()
                session.flush()
                
                logger.info(f"✅ API key verified for user: {api_key.user_id}")
                return api_key.user_id
        except Exception as e:
            logger.error(f"❌ Error verifying API key: {str(e)}")
            return None

    def get_user_api_keys(self, user_id: int) -> list:
        """Get user's API keys"""
        try:
            with self.db_manager.session_context() as session:
                keys = session.query(APIKeyModel).filter_by(user_id=user_id).all()
                
                return [
                    {
                        "id": k.id,
                        "name": k.name,
                        "key": k.key[:10] + "...",  # Mask key
                        "is_active": k.is_active,
                        "created_at": k.created_at.isoformat(),
                        "last_used": k.last_used.isoformat() if k.last_used else None
                    }
                    for k in keys
                ]
        except Exception as e:
            logger.error(f"❌ Error getting API keys: {str(e)}")
            return []
