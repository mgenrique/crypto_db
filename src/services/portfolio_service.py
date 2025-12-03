"""
Portfolio Service
=================

Portfolio management business logic.
Handles wallets, transactions, and balance tracking.
"""

from sqlalchemy.orm import Session
from sqlalchemy import func
from decimal import Decimal
from datetime import datetime
from typing import List, Optional, Dict, Any
import logging

from src.database.models import (
    WalletModel, TransactionModel, BalanceModel
)

logger = logging.getLogger(__name__)


class PortfolioService:
    """Portfolio business logic service"""

    def __init__(self, db_manager):
        """
        Initialize portfolio service
        
        Args:
            db_manager: DatabaseManager instance
        """
        self.db_manager = db_manager

    def add_wallet(self, 
                   address: str, 
                   wallet_type: str, 
                   network: str, 
                   label: str) -> Dict[str, Any]:
        """
        Add new wallet to portfolio
        
        Args:
            address: Wallet address (0x... for Ethereum, or any format)
            wallet_type: 'hot', 'cold', 'hardware', 'exchange', 'defi'
            network: 'ethereum', 'arbitrum', 'base', 'polygon', etc
            label: User-friendly name
            
        Returns:
            Created wallet dict
        """
        try:
            with self.db_manager.session_context() as session:
                # Check if wallet already exists
                existing = session.query(WalletModel).filter_by(
                    address=address,
                    network=network
                ).first()
                
                if existing:
                    logger.warning(f"Wallet {address} on {network} already exists")
                    return {
                        "id": existing.id,
                        "address": existing.address,
                        "network": existing.network,
                        "label": existing.label,
                        "wallet_type": existing.wallet_type,
                        "created_at": existing.created_at.isoformat(),
                        "status": "already_exists"
                    }
                
                # Create new wallet
                wallet = WalletModel(
                    address=address,
                    wallet_type=wallet_type,
                    network=network,
                    label=label
                )
                session.add(wallet)
                session.flush()
                
                logger.info(f"✅ Wallet added: {address[:8]}... on {network}")
                
                return {
                    "id": wallet.id,
                    "address": wallet.address,
                    "network": wallet.network,
                    "label": wallet.label,
                    "wallet_type": wallet.wallet_type,
                    "created_at": wallet.created_at.isoformat(),
                    "status": "created"
                }
        except Exception as e:
            logger.error(f"❌ Error adding wallet: {str(e)}")
            raise

    def get_wallets(self, network: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get all wallets or filter by network
        
        Args:
            network: Optional network filter
            
        Returns:
            List of wallet dicts
        """
        try:
            with self.db_manager.session_context() as session:
                query = session.query(WalletModel)
                
                if network:
                    query = query.filter_by(network=network)
                
                wallets = query.order_by(WalletModel.created_at.desc()).all()
                
                return [
                    {
                        "id": w.id,
                        "address": w.address,
                        "wallet_type": w.wallet_type,
                        "network": w.network,
                        "label": w.label,
                        "created_at": w.created_at.isoformat(),
                        "transactions_count": len(w.transactions)
                    }
                    for w in wallets
                ]
        except Exception as e:
            logger.error(f"❌ Error getting wallets: {str(e)}")
            return []

    def get_wallet(self, wallet_id: int) -> Optional[Dict[str, Any]]:
        """
        Get wallet by ID
        
        Args:
            wallet_id: Wallet ID
            
        Returns:
            Wallet dict or None
        """
        try:
            with self.db_manager.session_context() as session:
                wallet = session.query(WalletModel).filter_by(id=wallet_id).first()
                
                if not wallet:
                    logger.warning(f"Wallet {wallet_id} not found")
                    return None
                
                return {
                    "id": wallet.id,
                    "address": wallet.address,
                    "wallet_type": wallet.wallet_type,
                    "network": wallet.network,
                    "label": wallet.label,
                    "created_at": wallet.created_at.isoformat(),
                    "transactions_count": len(wallet.transactions),
                    "latest_update": wallet.updated_at.isoformat()
                }
        except Exception as e:
            logger.error(f"❌ Error getting wallet: {str(e)}")
            return None

    def remove_wallet(self, wallet_id: int) -> bool:
        """
        Remove wallet and all associated data
        
        Args:
            wallet_id: Wallet ID to remove
            
        Returns:
            True if successful
        """
        try:
            with self.db_manager.session_context() as session:
                wallet = session.query(WalletModel).filter_by(id=wallet_id).first()
                
                if not wallet:
                    logger.warning(f"Wallet {wallet_id} not found")
                    return False
                
                session.delete(wallet)
                logger.info(f"✅ Wallet {wallet_id} removed (cascade deleted all related data)")
                return True
        except Exception as e:
            logger.error(f"❌ Error removing wallet: {str(e)}")
            return False

    def record_transaction(self,
                          wallet_id: int,
                          tx_hash: str,
                          tx_type: str,
                          token_in: str,
                          token_out: str,
                          amount_in: Decimal,
                          amount_out: Decimal,
                          fee: Decimal = Decimal("0"),
                          fee_token: Optional[str] = None,
                          price_usd_in: Optional[Decimal] = None,
                          price_usd_out: Optional[Decimal] = None,
                          notes: Optional[str] = None) -> Dict[str, Any]:
        """
        Record transaction for wallet
        
        Args:
            wallet_id: Wallet ID
            tx_hash: Transaction hash
            tx_type: 'buy', 'sell', 'swap', 'transfer_in', 'transfer_out'
            token_in: Input token symbol
            token_out: Output token symbol
            amount_in: Input amount
            amount_out: Output amount
            fee: Transaction fee
            fee_token: Fee token symbol
            price_usd_in: Historical price of input token
            price_usd_out: Historical price of output token
            notes: Additional notes
            
        Returns:
            Created transaction dict
        """
        try:
            with self.db_manager.session_context() as session:
                # Verify wallet exists
                wallet = session.query(WalletModel).filter_by(id=wallet_id).first()
                if not wallet:
                    raise ValueError(f"Wallet {wallet_id} not found")
                
                # Check for duplicate
                existing = session.query(TransactionModel).filter_by(
                    wallet_id=wallet_id,
                    tx_hash=tx_hash
                ).first()
                
                if existing:
                    logger.warning(f"Transaction {tx_hash} already exists")
                    return {"status": "already_exists", "id": existing.id}
                
                # Create transaction
                transaction = TransactionModel(
                    wallet_id=wallet_id,
                    tx_hash=tx_hash,
                    tx_type=tx_type,
                    token_in=token_in,
                    token_out=token_out,
                    amount_in=amount_in,
                    amount_out=amount_out,
                    fee=fee,
                    fee_token=fee_token,
                    price_usd_in=price_usd_in,
                    price_usd_out=price_usd_out,
                    notes=notes
                )
                session.add(transaction)
                session.flush()
                
                logger.info(f"✅ Transaction recorded: {tx_hash[:16]}... {tx_type}")
                
                return {
                    "id": transaction.id,
                    "wallet_id": transaction.wallet_id,
                    "tx_hash": transaction.tx_hash,
                    "tx_type": transaction.tx_type,
                    "token_in": transaction.token_in,
                    "token_out": transaction.token_out,
                    "amount_in": str(transaction.amount_in),
                    "amount_out": str(transaction.amount_out),
                    "fee": str(transaction.fee),
                    "created_at": transaction.created_at.isoformat(),
                    "status": "created"
                }
        except Exception as e:
            logger.error(f"❌ Error recording transaction: {str(e)}")
            raise

    def get_transactions(self, wallet_id: int, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get wallet transactions
        
        Args:
            wallet_id: Wallet ID
            limit: Maximum number of transactions to return
            
        Returns:
            List of transaction dicts
        """
        try:
            with self.db_manager.session_context() as session:
                transactions = session.query(TransactionModel).filter_by(
                    wallet_id=wallet_id
                ).order_by(TransactionModel.created_at.desc()).limit(limit).all()
                
                return [
                    {
                        "id": t.id,
                        "tx_hash": t.tx_hash,
                        "tx_type": t.tx_type,
                        "token_in": t.token_in,
                        "token_out": t.token_out,
                        "amount_in": str(t.amount_in) if t.amount_in else None,
                        "amount_out": str(t.amount_out) if t.amount_out else None,
                        "fee": str(t.fee),
                        "price_usd_in": str(t.price_usd_in) if t.price_usd_in else None,
                        "price_usd_out": str(t.price_usd_out) if t.price_usd_out else None,
                        "created_at": t.created_at.isoformat(),
                        "notes": t.notes
                    }
                    for t in transactions
                ]
        except Exception as e:
            logger.error(f"❌ Error getting transactions: {str(e)}")
            return []

    def update_balance(self,
                      wallet_id: int,
                      token_symbol: str,
                      balance: Decimal,
                      balance_usd: Optional[Decimal] = None) -> Dict[str, Any]:
        """
        Record or update balance snapshot
        
        Args:
            wallet_id: Wallet ID
            token_symbol: Token symbol (ETH, BTC, etc)
            balance: Token balance
            balance_usd: USD equivalent
            
        Returns:
            Created/updated balance dict
        """
        try:
            with self.db_manager.session_context() as session:
                # Verify wallet exists
                wallet = session.query(WalletModel).filter_by(id=wallet_id).first()
                if not wallet:
                    raise ValueError(f"Wallet {wallet_id} not found")
                
                # Create new balance snapshot
                balance_record = BalanceModel(
                    wallet_id=wallet_id,
                    token_symbol=token_symbol,
                    balance=balance,
                    balance_usd=balance_usd,
                    timestamp=datetime.utcnow()
                )
                session.add(balance_record)
                session.flush()
                
                logger.info(f"✅ Balance updated: {token_symbol} {balance}")
                
                return {
                    "id": balance_record.id,
                    "wallet_id": balance_record.wallet_id,
                    "token_symbol": balance_record.token_symbol,
                    "balance": str(balance_record.balance),
                    "balance_usd": str(balance_record.balance_usd) if balance_record.balance_usd else None,
                    "timestamp": balance_record.timestamp.isoformat()
                }
        except Exception as e:
            logger.error(f"❌ Error updating balance: {str(e)}")
            raise

    def get_portfolio_value(self) -> Dict[str, Any]:
        """
        Calculate total portfolio value across all wallets
        
        Returns:
            Portfolio summary dict
        """
        try:
            with self.db_manager.session_context() as session:
                # Get latest balances for each token
                subquery = session.query(
                    BalanceModel.token_symbol,
                    func.max(BalanceModel.id).label("max_id")
                ).group_by(BalanceModel.token_symbol).subquery()
                
                latest_balances = session.query(BalanceModel).join(
                    subquery,
                    (BalanceModel.token_symbol == subquery.c.token_symbol) &
                    (BalanceModel.id == subquery.c.max_id)
                ).all()
                
                total_usd = Decimal("0")
                assets = {}
                
                for balance in latest_balances:
                    if balance.balance_usd:
                        total_usd += balance.balance_usd
                    
                    assets[balance.token_symbol] = {
                        "balance": str(balance.balance),
                        "balance_usd": str(balance.balance_usd) if balance.balance_usd else "0",
                        "last_update": balance.timestamp.isoformat()
                    }
                
                wallet_count = session.query(WalletModel).count()
                transaction_count = session.query(TransactionModel).count()
                
                return {
                    "total_value_usd": str(total_usd),
                    "wallet_count": wallet_count,
                    "transaction_count": transaction_count,
                    "assets": assets,
                    "last_updated": datetime.utcnow().isoformat()
                }
        except Exception as e:
            logger.error(f"❌ Error calculating portfolio value: {str(e)}")
            return {
                "total_value_usd": "0",
                "wallet_count": 0,
                "transaction_count": 0,
                "assets": {},
                "error": str(e)
            }
