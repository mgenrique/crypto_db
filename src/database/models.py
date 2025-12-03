"""
Database Models (ORM)
====================

SQLAlchemy ORM models with proper relationships and constraints.
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Numeric, Index, UniqueConstraint, Text, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
from decimal import Decimal
from enum import Enum as PyEnum

Base = declarative_base()


class WalletModel(Base):
    """Wallet database model"""
    __tablename__ = "wallets"
    __table_args__ = (
        UniqueConstraint("address", "network", name="uq_wallet_address_network"),
        Index("idx_wallet_address", "address"),
        Index("idx_wallet_network", "network"),
    )

    id = Column(Integer, primary_key=True)
    address = Column(String(255), nullable=False, index=True)
    wallet_type = Column(String(50), nullable=False)  # 'hot', 'cold', 'hardware', 'exchange', 'defi'
    network = Column(String(50), nullable=False)  # 'ethereum', 'arbitrum', 'base', etc
    label = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    transactions = relationship("TransactionModel", back_populates="wallet", cascade="all, delete-orphan")
    balances = relationship("BalanceModel", back_populates="wallet", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Wallet {self.address[:8]}... on {self.network}>"


class TransactionModel(Base):
    """Transaction database model"""
    __tablename__ = "transactions"
    __table_args__ = (
        UniqueConstraint("tx_hash", "wallet_id", name="uq_transaction_hash_wallet"),
        Index("idx_transaction_wallet", "wallet_id"),
        Index("idx_transaction_hash", "tx_hash"),
        Index("idx_transaction_created", "created_at"),
    )

    id = Column(Integer, primary_key=True)
    wallet_id = Column(Integer, ForeignKey("wallets.id", ondelete="CASCADE"), nullable=False)
    tx_hash = Column(String(255), nullable=False, index=True)
    tx_type = Column(String(50), nullable=False)  # 'buy', 'sell', 'swap', 'transfer_in', 'transfer_out', etc
    token_in = Column(String(20), nullable=True)  # e.g., 'ETH', 'USDC'
    token_out = Column(String(20), nullable=True)
    amount_in = Column(Numeric(50, 18), nullable=True)  # BigDecimal for precise values
    amount_out = Column(Numeric(50, 18), nullable=True)
    fee = Column(Numeric(50, 18), default=0)
    fee_token = Column(String(20), nullable=True)  # 'ETH', 'GWEI', 'USD', etc
    price_usd_in = Column(Numeric(30, 8), nullable=True)  # Historical price for tax purposes
    price_usd_out = Column(Numeric(30, 8), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    notes = Column(Text, nullable=True)

    # Relationships
    wallet = relationship("WalletModel", back_populates="transactions")
    tax_records = relationship("TaxRecordModel", back_populates="transaction", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Transaction {self.tx_hash[:16]}... {self.tx_type}>"


class BalanceModel(Base):
    """Balance snapshot database model"""
    __tablename__ = "balances"
    __table_args__ = (
        UniqueConstraint("wallet_id", "token_symbol", "timestamp", name="uq_balance_snapshot"),
        Index("idx_balance_wallet", "wallet_id"),
        Index("idx_balance_symbol", "token_symbol"),
        Index("idx_balance_timestamp", "timestamp"),
    )

    id = Column(Integer, primary_key=True)
    wallet_id = Column(Integer, ForeignKey("wallets.id", ondelete="CASCADE"), nullable=False)
    token_symbol = Column(String(20), nullable=False)
    balance = Column(Numeric(50, 18), nullable=False)  # Token amount
    balance_usd = Column(Numeric(30, 8), nullable=True)  # USD equivalent
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    wallet = relationship("WalletModel", back_populates="balances")

    def __repr__(self):
        return f"<Balance {self.token_symbol} {self.balance}>"


class TaxRecordModel(Base):
    """Tax calculation record"""
    __tablename__ = "tax_records"
    __table_args__ = (
        Index("idx_tax_wallet", "wallet_id"),
        Index("idx_tax_year", "year"),
        Index("idx_tax_method", "tax_method"),
    )

    id = Column(Integer, primary_key=True)
    wallet_id = Column(Integer, ForeignKey("wallets.id", ondelete="CASCADE"), nullable=False)
    transaction_id = Column(Integer, ForeignKey("transactions.id", ondelete="CASCADE"), nullable=False)
    gain_loss = Column(Numeric(30, 8), nullable=False)  # Profit or loss
    cost_basis = Column(Numeric(30, 8), nullable=False)
    proceeds = Column(Numeric(30, 8), nullable=False)
    tax_method = Column(String(50), nullable=False)  # 'FIFO', 'LIFO', 'AVERAGE_COST', 'SPECIFIC_ID'
    year = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    transaction = relationship("TransactionModel", back_populates="tax_records")

    def __repr__(self):
        return f"<TaxRecord {self.year} gain={self.gain_loss}>"

class BlockchainNetwork(PyEnum):
    ETHEREUM = "ethereum"
    ARBITRUM = "arbitrum"
    BASE = "base"
    POLYGON = "polygon"
    BITCOIN = "bitcoin"
    SOLANA = "solana"

class WalletType(PyEnum):
    METAMASK = "metamask"
    PHANTOM = "phantom"
    LEDGER = "ledger"
    EXCHANGE = "exchange"
    SELF_CUSTODY = "self_custody"

class ExchangeAccount(Base):
    """Exchange account model"""
    __tablename__ = "exchange_accounts"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    exchange = Column(String(50), nullable=False)  # binance, coinbase, kraken
    api_key_encrypted = Column(String(500), nullable=False)
    api_secret_encrypted = Column(String(500), nullable=False)
    label = Column(String(100))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class BlockchainWallet(Base):
    """Blockchain wallet model"""
    __tablename__ = "blockchain_wallets"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    address = Column(String(500), nullable=False)
    network = Column(String(50), nullable=False)  # ethereum, bitcoin, solana, etc
    wallet_type = Column(String(50), nullable=False)  # metamask, phantom, ledger
    label = Column(String(100))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    balances = relationship("WalletBalance", back_populates="wallet", cascade="all, delete-orphan")

class WalletBalance(Base):
    """Wallet balance snapshot"""
    __tablename__ = "wallet_balances"
    
    id = Column(Integer, primary_key=True)
    wallet_id = Column(Integer, ForeignKey("blockchain_wallets.id", ondelete="CASCADE"))
    token = Column(String(100), nullable=False)
    balance = Column(String(100), nullable=False)  # Use String for Decimal
    balance_usd = Column(String(100))
    timestamp = Column(DateTime, default=datetime.utcnow)

class DeFiPosition(Base):
    """DeFi protocol position"""
    __tablename__ = "defi_positions"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    address = Column(String(500), nullable=False)
    protocol = Column(String(50), nullable=False)  # uniswap, aave, etc
    position_type = Column(String(50), nullable=False)  # liquidity, lending, borrowing
    token0 = Column(String(100))
    token1 = Column(String(100))
    balance0 = Column(String(100))
    balance1 = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)

