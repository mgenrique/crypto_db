"""
Authentication Routes
====================

User registration, login, and API key management endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
import logging

from src.auth.service import AuthService
from src.auth.dependencies import get_current_user, get_auth_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


# ============================================================================
# SCHEMAS
# ============================================================================

class RegisterRequest(BaseModel):
    """User registration request"""
    email: EmailStr = Field(..., description="User email")
    username: str = Field(..., min_length=3, max_length=50, description="Username")
    password: str = Field(..., min_length=8, description="Password (min 8 chars)")


class LoginRequest(BaseModel):
    """User login request"""
    email: EmailStr = Field(..., description="User email")
    password: str = Field(..., description="User password")


class TokenResponse(BaseModel):
    """Token response"""
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")


class APIKeyRequest(BaseModel):
    """API key creation request"""
    name: str = Field(..., min_length=1, max_length=100, description="API key name")


class APIKeyResponse(BaseModel):
    """API key response"""
    key: str = Field(..., description="API key")
    secret: str = Field(..., description="API secret")
    name: str = Field(..., description="API key name")
    created_at: str = Field(..., description="Creation timestamp")


# ============================================================================
# AUTHENTICATION ENDPOINTS
# ============================================================================

@router.post("/register", status_code=201)
async def register(
    request: RegisterRequest,
    auth_svc: AuthService = Depends(get_auth_service)
):
    """
    Register new user
    
    Example:
        POST /api/v1/auth/register
        {
            "email": "user@example.com",
            "username": "myuser",
            "password": "securepass123"
        }
    """
    try:
        user = auth_svc.register_user(
            email=request.email,
            username=request.username,
            password=request.password
        )
        return {
            "status": "success",
            "message": "User registered successfully",
            "user": user
        }
    except ValueError as e:
        logger.warning(f"Registration failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )


@router.post("/login", response_model=dict)
async def login(
    request: LoginRequest,
    auth_svc: AuthService = Depends(get_auth_service)
):
    """
    Login user and get tokens
    
    Example:
        POST /api/v1/auth/login
        {
            "email": "user@example.com",
            "password": "securepass123"
        }
    """
    try:
        result = auth_svc.authenticate_user(
            email=request.email,
            password=request.password
        )
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )


@router.post("/refresh", response_model=dict)
async def refresh_token(
    refresh_token: str,
    auth_svc: AuthService = Depends(get_auth_service)
):
    """
    Refresh access token using refresh token
    
    Example:
        POST /api/v1/auth/refresh
        {
            "refresh_token": "eyJ0eXAi..."
        }
    """
    try:
        new_token = auth_svc.refresh_access_token(refresh_token)
        
        if not new_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        return {
            "access_token": new_token,
            "token_type": "bearer"
        }
    except Exception as e:
        logger.error(f"Token refresh error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )


# ============================================================================
# API KEY ENDPOINTS
# ============================================================================

@router.post("/api-keys", response_model=APIKeyResponse, status_code=201)
async def create_api_key(
    request: APIKeyRequest,
    current_user: dict = Depends(get_current_user),
    auth_svc: AuthService = Depends(get_auth_service)
):
    """
    Create new API key
    
    Example:
        POST /api/v1/auth/api-keys
        {
            "name": "Mobile App Integration"
        }
    
    Headers:
        Authorization: Bearer {access_token}
    """
    try:
        api_key = auth_svc.create_api_key(
            user_id=current_user['user_id'],
            name=request.name
        )
        return api_key
    except Exception as e:
        logger.error(f"API key creation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create API key"
        )


@router.get("/api-keys")
async def list_api_keys(
    current_user: dict = Depends(get_current_user),
    auth_svc: AuthService = Depends(get_auth_service)
):
    """
    List user's API keys
    
    Example:
        GET /api/v1/auth/api-keys
    
    Headers:
        Authorization: Bearer {access_token}
    """
    try:
        keys = auth_svc.get_user_api_keys(current_user['user_id'])
        return {"api_keys": keys}
    except Exception as e:
        logger.error(f"Error listing API keys: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list API keys"
        )


@router.get("/profile")
async def get_profile(current_user: dict = Depends(get_current_user)):
    """
    Get current user profile
    
    Example:
        GET /api/v1/auth/profile
    
    Headers:
        Authorization: Bearer {access_token}
    """
    return {
        "user_id": current_user['user_id'],
        "email": current_user['email'],
        "username": current_user['username']
    }
