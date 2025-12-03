"""
Database models for cryptocurrency and FIAT transaction tracking
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
import enum

from crypto_db.database import Base


class TransactionType(enum.Enum):
    """Transaction types for crypto operations"""
    BUY = "buy"
    SELL = "sell"
    TRANSFER_IN = "transfer_in"
    TRANSFER_OUT = "transfer_out"
    STAKE = "stake"
    UNSTAKE = "unstake"
    REWARD = "reward"
    FEE = "fee"


class DepositType(enum.Enum):
    """Deposit types for FIAT operations"""
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"


class Platform(Base):
    """
    Trading/Exchange platforms (Binance, Coinbase, Kraken, etc.)
    """
    __tablename__ = "platforms"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    crypto_transactions = relationship("CryptoTransaction", back_populates="platform")
    fiat_deposits = relationship("FiatDeposit", back_populates="platform")


class CryptoTransaction(Base):
    """
    Cryptocurrency transactions across all platforms
    """
    __tablename__ = "crypto_transactions"

    id = Column(Integer, primary_key=True, index=True)
    platform_id = Column(Integer, ForeignKey("platforms.id"), nullable=False)
    
    # Transaction details
    transaction_type = Column(SQLEnum(TransactionType), nullable=False)
    cryptocurrency = Column(String(20), nullable=False)  # BTC, ETH, ADA, etc.
    amount = Column(Float, nullable=False)
    
    # Pricing information
    price_per_unit = Column(Float, nullable=False)  # Price in FIAT currency
    fiat_currency = Column(String(3), default="EUR")  # EUR, USD, etc.
    total_value = Column(Float, nullable=False)  # amount * price_per_unit
    
    # Fees
    fee_amount = Column(Float, default=0.0)
    fee_currency = Column(String(20), default="EUR")
    
    # Transaction metadata
    transaction_date = Column(DateTime, nullable=False)
    transaction_id = Column(String(200))  # Platform's transaction ID
    notes = Column(String(1000))
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    platform = relationship("Platform", back_populates="crypto_transactions")


class FiatDeposit(Base):
    """
    FIAT currency deposits and withdrawals
    """
    __tablename__ = "fiat_deposits"

    id = Column(Integer, primary_key=True, index=True)
    platform_id = Column(Integer, ForeignKey("platforms.id"), nullable=False)
    
    # Deposit details
    deposit_type = Column(SQLEnum(DepositType), nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String(3), default="EUR")
    
    # Transaction metadata
    transaction_date = Column(DateTime, nullable=False)
    transaction_id = Column(String(200))  # Bank/Platform transaction ID
    notes = Column(String(1000))
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    platform = relationship("Platform", back_populates="fiat_deposits")


class TaxReport(Base):
    """
    Tax reports for Spanish fiscal compliance
    """
    __tablename__ = "tax_reports"

    id = Column(Integer, primary_key=True, index=True)
    
    # Report details
    tax_year = Column(Integer, nullable=False)
    report_type = Column(String(50), nullable=False)  # annual, quarterly, etc.
    
    # Calculated values
    total_gains = Column(Float, default=0.0)
    total_losses = Column(Float, default=0.0)
    net_result = Column(Float, default=0.0)
    
    # Report metadata
    generated_at = Column(DateTime, default=datetime.utcnow)
    report_data = Column(String)  # JSON serialized detailed data
    notes = Column(String(1000))
