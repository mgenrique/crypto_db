"""
Authentication Dependencies
============================

Dependency injection for authentication.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
from fastapi.security import HTTPAuthorizationCredentials
from typing import Optional
import logging

from src.auth.security import SecurityService
from src.auth.service import AuthService
from src.database import get_db_manager

logger = logging.getLogger(__name__)

security = HTTPBearer()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """
    Get current user from JWT token
    
    Usage:
        @app.get("/user/profile")
        async def get_profile(current_user: dict = Depends(get_current_user)):
            return current_user
    """
    token = credentials.credentials
    payload = SecurityService.verify_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = payload.get("user_id")
    # Accept 0 as a valid user id (single-user deployments may use id 0)
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )
    
    return {
        "user_id": user_id,
        "email": payload.get("sub"),
        "username": payload.get("username")
    }


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[dict]:
    """Get current user if authenticated, otherwise None"""
    if not credentials:
        return None
    
    return await get_current_user(credentials)


async def get_api_key_user(
    key: str = None,
    secret: str = None
) -> int:
    """
    Verify API key credentials
    
    Usage in routes:
        @app.get("/api/data")
        async def get_data(user_id: int = Depends(get_api_key_user)):
            ...
    """
    if not key or not secret:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key and secret required"
        )

    # Use single-user auth service if available (no DB lookup)
    try:
        svc = get_auth_service()
        # svc may be SingleUserAuthService or AuthService; both expose verify_api_key
        user_id = svc.verify_api_key(key, secret)
    except Exception:
        user_id = None

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key or secret"
        )

    return user_id


def get_auth_service() -> AuthService:
    """Get authentication service"""
    # Prefer single-user service when env vars are set. Import lazily to avoid
    # creating DB model side-effects during app startup.
    from os import getenv
    if getenv("ADMIN_EMAIL"):
        from src.auth.service import SingleUserAuthService
        return SingleUserAuthService()

    # Fallback to DB-backed AuthService
    return AuthService(get_db_manager())
