"""
Database Models (ORM)
====================

SQLAlchemy ORM models with proper relationships and constraints.
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Numeric, Index, UniqueConstraint, Text, Enum as SQLEnum, Boolean
from sqlalchemy.orm import relationship
from src.database.base import Base
# Ensure auth models (UserModel) are imported so ForeignKey references to
# 'users' resolve when creating all tables. Importing here registers the
# `UserModel` with the shared declarative `Base` before other models are
# defined which reference it.
import src.auth.models  # noqa: F401
from datetime import datetime, timezone
from src.utils.time import now_utc
from decimal import Decimal
from enum import Enum as PyEnum


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
    created_at = Column(DateTime, default=now_utc, nullable=False)
    updated_at = Column(DateTime, default=now_utc, onupdate=now_utc)

    # Ownership (optional)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    user = relationship("UserModel", back_populates="wallets")

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
    price_fiat_in = Column(Numeric(30, 8), nullable=True)
    price_fiat_out = Column(Numeric(30, 8), nullable=True)
    created_at = Column(DateTime, default=now_utc, nullable=False)
    updated_at = Column(DateTime, default=now_utc, onupdate=now_utc)
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
    timestamp = Column(DateTime, default=now_utc, nullable=False, index=True)

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
    gain_loss_fiat = Column(Numeric(30, 8), nullable=True)
    cost_basis_fiat = Column(Numeric(30, 8), nullable=True)
    proceeds_fiat = Column(Numeric(30, 8), nullable=True)
    tax_method = Column(String(50), nullable=False)  # 'FIFO', 'LIFO', 'AVERAGE_COST', 'SPECIFIC_ID'
    year = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=now_utc, nullable=False)

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
    # Strict DB-level ownership using ForeignKey to users.id
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    user = relationship("UserModel", back_populates="exchange_accounts")
    exchange = Column(String(50), nullable=False)  # binance, coinbase, kraken
    api_key_encrypted = Column(String(500), nullable=False)
    api_secret_encrypted = Column(String(500), nullable=False)
    label = Column(String(100))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=now_utc)


class ExchangeBalance(Base):
    """Per-exchange asset balances"""
    __tablename__ = "exchange_balances"
    __table_args__ = (
        Index("idx_exchange_balance_account_asset", "exchange_account_id", "asset"),
    )

    id = Column(Integer, primary_key=True)
    exchange_account_id = Column(Integer, ForeignKey("exchange_accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    asset = Column(String(50), nullable=False, index=True)
    free = Column(Numeric(50, 18), nullable=False, default=0)
    locked = Column(Numeric(50, 18), nullable=False, default=0)
    total = Column(Numeric(50, 18), nullable=False, default=0)
    total_usd = Column(Numeric(30, 8), nullable=True)
    total_fiat = Column(Numeric(30, 8), nullable=True)
    created_at = Column(DateTime, default=now_utc)


class ExchangeTrade(Base):
    """Trades executed on exchanges (user-level)"""
    __tablename__ = "exchange_trades"
    __table_args__ = (
        UniqueConstraint("exchange_account_id", "trade_id", name="uq_exchange_trade_account_tradeid"),
        Index("idx_exchange_trade_account_symbol", "exchange_account_id", "symbol"),
    )

    id = Column(Integer, primary_key=True)
    exchange_account_id = Column(Integer, ForeignKey("exchange_accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    trade_id = Column(String(200), nullable=True, index=True)
    symbol = Column(String(50), nullable=False, index=True)
    price = Column(Numeric(50, 18))
    price_fiat = Column(Numeric(30, 8))
    qty = Column(Numeric(50, 18))
    commission = Column(Numeric(50, 18))
    commission_fiat = Column(Numeric(30, 8))
    commission_asset = Column(String(50))
    is_buyer = Column(Boolean, default=False)
    is_maker = Column(Boolean, default=False)
    timestamp = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=now_utc)


class ExchangeDeposit(Base):
    __tablename__ = "exchange_deposits"
    __table_args__ = (
        UniqueConstraint("exchange_account_id", "deposit_id", name="uq_exchange_deposit_account_depositid"),
        Index("idx_exchange_deposit_account_asset", "exchange_account_id", "asset"),
    )

    id = Column(Integer, primary_key=True)
    exchange_account_id = Column(Integer, ForeignKey("exchange_accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    deposit_id = Column(String(200), nullable=True, index=True)
    asset = Column(String(50), nullable=False)
    amount = Column(Numeric(50, 18))
    amount_fiat = Column(Numeric(30, 8))
    address = Column(String(500))
    txid = Column(String(200))
    network = Column(String(50))
    status = Column(String(50))
    timestamp = Column(DateTime)
    created_at = Column(DateTime, default=now_utc)


class ExchangeWithdrawal(Base):
    __tablename__ = "exchange_withdrawals"
    __table_args__ = (
        UniqueConstraint("exchange_account_id", "withdrawal_id", name="uq_exchange_withdrawal_account_withdrawalid"),
        Index("idx_exchange_withdrawal_account_asset", "exchange_account_id", "asset"),
    )

    id = Column(Integer, primary_key=True)
    exchange_account_id = Column(Integer, ForeignKey("exchange_accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    withdrawal_id = Column(String(200), nullable=True, index=True)
    asset = Column(String(50), nullable=False)
    amount = Column(Numeric(50, 18))
    amount_fiat = Column(Numeric(30, 8))
    address = Column(String(500))
    txid = Column(String(200))
    network = Column(String(50))
    status = Column(String(50))
    timestamp = Column(DateTime)
    created_at = Column(DateTime, default=now_utc)

class BlockchainWallet(Base):
    """Blockchain wallet model"""
    __tablename__ = "blockchain_wallets"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    user = relationship("UserModel", back_populates="blockchain_wallets")
    address = Column(String(500), nullable=False)
    network = Column(String(50), nullable=False)  # ethereum, bitcoin, solana, etc
    wallet_type = Column(String(50), nullable=False)  # metamask, phantom, ledger
    label = Column(String(100))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    balances = relationship("WalletBalance", back_populates="wallet", cascade="all, delete-orphan")

class WalletBalance(Base):
    """Wallet balance snapshot"""
    __tablename__ = "wallet_balances"
    
    id = Column(Integer, primary_key=True)
    wallet_id = Column(Integer, ForeignKey("blockchain_wallets.id", ondelete="CASCADE"))
    token = Column(String(100), nullable=False)
    balance = Column(String(100), nullable=False)  # Use String for Decimal
    balance_usd = Column(Numeric(30, 8), nullable=True)
    balance_fiat = Column(Numeric(30, 8), nullable=True)
    timestamp = Column(DateTime, default=now_utc)
    
    # Relationship back to blockchain wallet
    wallet = relationship("BlockchainWallet", back_populates="balances")

class DeFiPosition(Base):
    """DeFi protocol position"""
    __tablename__ = "defi_positions"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    user = relationship("UserModel", back_populates="defi_positions")
    address = Column(String(500), nullable=False)
    protocol = Column(String(50), nullable=False)  # uniswap, aave, etc
    position_type = Column(String(50), nullable=False)  # liquidity, lending, borrowing
    token0 = Column(String(100))
    token1 = Column(String(100))
    balance0 = Column(String(100))
    balance1 = Column(String(100))
    created_at = Column(DateTime, default=now_utc)


class PriceMapping(Base):
    """Map token symbol or contract address to CoinGecko id"""
    __tablename__ = "price_mappings"
    __table_args__ = (
        UniqueConstraint("symbol", "network", name="uq_price_mapping_symbol_network"),
        Index("idx_price_mapping_symbol", "symbol"),
        Index("idx_price_mapping_contract", "contract_address"),
    )

    id = Column(Integer, primary_key=True)
    symbol = Column(String(50), nullable=True)  # e.g., 'ETH', 'USDC'
    network = Column(String(50), nullable=True)  # 'ethereum', 'solana', etc
    contract_address = Column(String(255), nullable=True, index=True)  # optional contract for ERC-20
    coingecko_id = Column(String(255), nullable=False, index=True)
    source = Column(String(50), nullable=True)  # 'manual', 'coin_gecko_contract', etc
    created_at = Column(DateTime, default=now_utc)


class PriceCache(Base):
    """Cache of fetched prices used for calculations. Stores price for cg_id, vs_currency, rounded_minute timestamp."""
    __tablename__ = "price_cache"
    __table_args__ = (
        UniqueConstraint("coingecko_id", "vs_currency", "ts_minute", name="uq_pricecache_cg_vs_ts"),
        Index("idx_pricecache_cg_vs", "coingecko_id", "vs_currency"),
        Index("idx_pricecache_ts", "ts_minute"),
    )

    id = Column(Integer, primary_key=True)
    coingecko_id = Column(String(255), nullable=False, index=True)
    vs_currency = Column(String(10), nullable=False, index=True)
    ts_minute = Column(Integer, nullable=False, index=True)  # unix timestamp rounded to minute
    price = Column(Numeric(40, 18), nullable=True)
    fetched_at = Column(DateTime, default=now_utc)

