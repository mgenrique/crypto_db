"""
Authentication Models
=====================

User and API key models for authentication.
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from src.database.base import Base
from datetime import datetime, timezone
from src.utils.time import now_utc
import secrets



class UserModel(Base):
    """User database model"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=now_utc, nullable=False)
    updated_at = Column(DateTime, default=now_utc, onupdate=now_utc)

    # Relationships
    api_keys = relationship("APIKeyModel", back_populates="user", cascade="all, delete-orphan")
    # Wallets and exchange accounts owned by the user
    wallets = relationship("WalletModel", back_populates="user", cascade="all, delete-orphan")
    blockchain_wallets = relationship("BlockchainWallet", back_populates="user", cascade="all, delete-orphan")
    exchange_accounts = relationship("ExchangeAccount", back_populates="user", cascade="all, delete-orphan")
    defi_positions = relationship("DeFiPosition", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User {self.username}>"


class APIKeyModel(Base):
    """API Key database model"""
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    key = Column(String(255), unique=True, nullable=False, index=True)
    secret = Column(String(255), nullable=False)
    name = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=now_utc, nullable=False)
    last_used = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("UserModel", back_populates="api_keys")

    @staticmethod
    def generate_key():
        """Generate random API key"""
        return "sk_" + secrets.token_urlsafe(32)

    @staticmethod
    def generate_secret():
        """Generate random API secret"""
        return secrets.token_urlsafe(64)

    def __repr__(self):
        return f"<APIKey {self.name}>"


# Actualizar WalletModel para incluir user_id
# En src/database/models.py, agregar:
# user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
# user = relationship("UserModel", back_populates="wallets")
