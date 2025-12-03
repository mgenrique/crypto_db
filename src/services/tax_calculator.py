"""
Tax Calculator
==============

Tax calculation service with multiple methods.
Implements FIFO, LIFO, and Average Cost methods.
"""

from sqlalchemy.orm import Session
from decimal import Decimal
from datetime import datetime
from typing import List, Dict, Any, Tuple
import logging

from src.database.models import (
    TransactionModel, TaxRecordModel, WalletModel
)

logger = logging.getLogger(__name__)


class TaxCalculator:
    """Tax calculation service"""

    def __init__(self, db_manager):
        """
        Initialize tax calculator
        
        Args:
            db_manager: DatabaseManager instance
        """
        self.db_manager = db_manager

    def calculate_fifo(self, wallet_id: int, year: int, token: Optional[str] = None) -> Dict[str, Any]:
        """
        Calculate taxes using FIFO (First In, First Out) method
        
        Args:
            wallet_id: Wallet ID
            year: Tax year
            token: Optional token filter (e.g., 'ETH')
            
        Returns:
            Tax calculation results
        """
        try:
            with self.db_manager.session_context() as session:
                # Get all BUY transactions ordered by date (FIFO = oldest first)
                buy_query = session.query(TransactionModel).filter(
                    TransactionModel.wallet_id == wallet_id,
                    TransactionModel.tx_type.in_(["buy", "transfer_in"]),
                    TransactionModel.created_at.year == year
                ).order_by(TransactionModel.created_at.asc())
                
                if token:
                    buy_query = buy_query.filter_by(token_out=token)
                
                buy_transactions = buy_query.all()
                
                # Get all SELL transactions
                sell_query = session.query(TransactionModel).filter(
                    TransactionModel.wallet_id == wallet_id,
                    TransactionModel.tx_type.in_(["sell", "swap", "transfer_out"]),
                    TransactionModel.created_at.year == year
                ).order_by(TransactionModel.created_at.asc())
                
                if token:
                    sell_query = sell_query.filter(
                        (TransactionModel.token_in == token) | (TransactionModel.token_out == token)
                    )
                
                sell_transactions = sell_query.all()
                
                # Calculate gains/losses
                total_gain_loss = Decimal("0")
                total_cost_basis = Decimal("0")
                total_proceeds = Decimal("0")
                tax_records = []
                
                cost_basis_per_unit = Decimal("0")
                remaining_buy_amount = Decimal("0")
                buy_index = 0
                
                for sell_tx in sell_transactions:
                    remaining_to_sell = sell_tx.amount_in if sell_tx.amount_in else Decimal("0")
                    
                    while remaining_to_sell > 0 and buy_index < len(buy_transactions):
                        buy_tx = buy_transactions[buy_index]
                        available_to_sell = (buy_tx.amount_out or Decimal("0")) - remaining_buy_amount
                        
                        if available_to_sell <= 0:
                            buy_index += 1
                            remaining_buy_amount = Decimal("0")
                            continue
                        
                        sell_amount = min(remaining_to_sell, available_to_sell)
                        cost_basis = sell_amount * (buy_tx.price_usd_in or Decimal("0"))
                        proceeds = sell_amount * (sell_tx.price_usd_out or Decimal("0"))
                        gain_loss = proceeds - cost_basis
                        
                        total_gain_loss += gain_loss
                        total_cost_basis += cost_basis
                        total_proceeds += proceeds
                        
                        # Create tax record
                        tax_record = TaxRecordModel(
                            wallet_id=wallet_id,
                            transaction_id=sell_tx.id,
                            gain_loss=gain_loss,
                            cost_basis=cost_basis,
                            proceeds=proceeds,
                            tax_method="FIFO",
                            year=year
                        )
                        session.add(tax_record)
                        
                        remaining_to_sell -= sell_amount
                        remaining_buy_amount += sell_amount
                    
                    if remaining_to_sell > 0:
                        logger.warning(f"⚠️  Insufficient cost basis for FIFO calculation on {sell_tx.tx_hash}")
                
                session.flush()
                
                logger.info(f"✅ FIFO tax calculated: gain/loss={total_gain_loss}")
                
                return {
                    "method": "FIFO",
                    "year": year,
                    "total_gain_loss": str(total_gain_loss),
                    "total_cost_basis": str(total_cost_basis),
                    "total_proceeds": str(total_proceeds),
                    "tax_records_count": len(tax_records),
                    "estimated_tax_usd": str(total_gain_loss * Decimal("0.21"))  # Typical rate
                }
        except Exception as e:
            logger.error(f"❌ Error calculating FIFO: {str(e)}")
            raise

    def calculate_lifo(self, wallet_id: int, year: int, token: Optional[str] = None) -> Dict[str, Any]:
        """
        Calculate taxes using LIFO (Last In, First Out) method
        
        Args:
            wallet_id: Wallet ID
            year: Tax year
            token: Optional token filter
            
        Returns:
            Tax calculation results
        """
        try:
            with self.db_manager.session_context() as session:
                # Get all BUY transactions ordered by date (LIFO = newest first)
                buy_query = session.query(TransactionModel).filter(
                    TransactionModel.wallet_id == wallet_id,
                    TransactionModel.tx_type.in_(["buy", "transfer_in"]),
                    TransactionModel.created_at.year == year
                ).order_by(TransactionModel.created_at.desc())
                
                if token:
                    buy_query = buy_query.filter_by(token_out=token)
                
                buy_transactions = buy_query.all()
                
                # Get all SELL transactions
                sell_query = session.query(TransactionModel).filter(
                    TransactionModel.wallet_id == wallet_id,
                    TransactionModel.tx_type.in_(["sell", "swap", "transfer_out"]),
                    TransactionModel.created_at.year == year
                ).order_by(TransactionModel.created_at.asc())
                
                if token:
                    sell_query = sell_query.filter(
                        (TransactionModel.token_in == token) | (TransactionModel.token_out == token)
                    )
                
                sell_transactions = sell_query.all()
                
                total_gain_loss = Decimal("0")
                total_cost_basis = Decimal("0")
                total_proceeds = Decimal("0")
                
                buy_index = 0
                remaining_buy_amount = Decimal("0")
                
                for sell_tx in sell_transactions:
                    remaining_to_sell = sell_tx.amount_in if sell_tx.amount_in else Decimal("0")
                    
                    while remaining_to_sell > 0 and buy_index < len(buy_transactions):
                        buy_tx = buy_transactions[buy_index]
                        available_to_sell = (buy_tx.amount_out or Decimal("0")) - remaining_buy_amount
                        
                        if available_to_sell <= 0:
                            buy_index += 1
                            remaining_buy_amount = Decimal("0")
                            continue
                        
                        sell_amount = min(remaining_to_sell, available_to_sell)
                        cost_basis = sell_amount * (buy_tx.price_usd_in or Decimal("0"))
                        proceeds = sell_amount * (sell_tx.price_usd_out or Decimal("0"))
                        gain_loss = proceeds - cost_basis
                        
                        total_gain_loss += gain_loss
                        total_cost_basis += cost_basis
                        total_proceeds += proceeds
                        
                        # Create tax record
                        tax_record = TaxRecordModel(
                            wallet_id=wallet_id,
                            transaction_id=sell_tx.id,
                            gain_loss=gain_loss,
                            cost_basis=cost_basis,
                            proceeds=proceeds,
                            tax_method="LIFO",
                            year=year
                        )
                        session.add(tax_record)
                        
                        remaining_to_sell -= sell_amount
                        remaining_buy_amount += sell_amount
                
                session.flush()
                
                logger.info(f"✅ LIFO tax calculated: gain/loss={total_gain_loss}")
                
                return {
                    "method": "LIFO",
                    "year": year,
                    "total_gain_loss": str(total_gain_loss),
                    "total_cost_basis": str(total_cost_basis),
                    "total_proceeds": str(total_proceeds),
                    "estimated_tax_usd": str(total_gain_loss * Decimal("0.21"))
                }
        except Exception as e:
            logger.error(f"❌ Error calculating LIFO: {str(e)}")
            raise

    def calculate_average_cost(self, wallet_id: int, year: int, token: Optional[str] = None) -> Dict[str, Any]:
        """
        Calculate taxes using Average Cost method
        
        Args:
            wallet_id: Wallet ID
            year: Tax year
            token: Optional token filter
            
        Returns:
            Tax calculation results
        """
        try:
            with self.db_manager.session_context() as session:
                # Get all transactions for the year
                buy_query = session.query(TransactionModel).filter(
                    TransactionModel.wallet_id == wallet_id,
                    TransactionModel.tx_type.in_(["buy", "transfer_in"]),
                    TransactionModel.created_at.year == year
                )
                
                if token:
                    buy_query = buy_query.filter_by(token_out=token)
                
                buy_transactions = buy_query.all()
                
                sell_query = session.query(TransactionModel).filter(
                    TransactionModel.wallet_id == wallet_id,
                    TransactionModel.tx_type.in_(["sell", "swap", "transfer_out"]),
                    TransactionModel.created_at.year == year
                )
                
                if token:
                    sell_query = sell_query.filter(
                        (TransactionModel.token_in == token) | (TransactionModel.token_out == token)
                    )
                
                sell_transactions = sell_query.all()
                
                # Calculate average cost basis
                total_bought = Decimal("0")
                total_cost = Decimal("0")
                
                for buy_tx in buy_transactions:
                    amount = buy_tx.amount_out or Decimal("0")
                    price = buy_tx.price_usd_in or Decimal("0")
                    total_bought += amount
                    total_cost += amount * price
                
                average_cost_per_unit = total_cost / total_bought if total_bought > 0 else Decimal("0")
                
                # Calculate sells at average cost
                total_gain_loss = Decimal("0")
                total_cost_basis = Decimal("0")
                total_proceeds = Decimal("0")
                
                for sell_tx in sell_transactions:
                    amount = sell_tx.amount_in or Decimal("0")
                    price = sell_tx.price_usd_out or Decimal("0")
                    
                    cost_basis = amount * average_cost_per_unit
                    proceeds = amount * price
                    gain_loss = proceeds - cost_basis
                    
                    total_gain_loss += gain_loss
                    total_cost_basis += cost_basis
                    total_proceeds += proceeds
                    
                    # Create tax record
                    tax_record = TaxRecordModel(
                        wallet_id=wallet_id,
                        transaction_id=sell_tx.id,
                        gain_loss=gain_loss,
                        cost_basis=cost_basis,
                        proceeds=proceeds,
                        tax_method="AVERAGE_COST",
                        year=year
                    )
                    session.add(tax_record)
                
                session.flush()
                
                logger.info(f"✅ Average cost tax calculated: gain/loss={total_gain_loss}")
                
                return {
                    "method": "AVERAGE_COST",
                    "year": year,
                    "average_cost_per_unit": str(average_cost_per_unit),
                    "total_gain_loss": str(total_gain_loss),
                    "total_cost_basis": str(total_cost_basis),
                    "total_proceeds": str(total_proceeds),
                    "estimated_tax_usd": str(total_gain_loss * Decimal("0.21"))
                }
        except Exception as e:
            logger.error(f"❌ Error calculating average cost: {str(e)}")
            raise

    def get_annual_summary(self, wallet_id: int, year: int) -> Dict[str, Any]:
        """
        Get annual tax summary for wallet
        
        Args:
            wallet_id: Wallet ID
            year: Tax year
            
        Returns:
            Annual tax summary
        """
        try:
            with self.db_manager.session_context() as session:
                # Get all tax records for the year
                tax_records = session.query(TaxRecordModel).filter(
                    TaxRecordModel.wallet_id == wallet_id,
                    TaxRecordModel.year == year
                ).all()
                
                # Group by method
                by_method = {}
                total_gain_loss = Decimal("0")
                
                for record in tax_records:
                    method = record.tax_method
                    if method not in by_method:
                        by_method[method] = {
                            "total_gain_loss": Decimal("0"),
                            "total_cost_basis": Decimal("0"),
                            "total_proceeds": Decimal("0"),
                            "records_count": 0
                        }
                    
                    by_method[method]["total_gain_loss"] += record.gain_loss
                    by_method[method]["total_cost_basis"] += record.cost_basis
                    by_method[method]["total_proceeds"] += record.proceeds
                    by_method[method]["records_count"] += 1
                    total_gain_loss += record.gain_loss
                
                return {
                    "wallet_id": wallet_id,
                    "year": year,
                    "total_gain_loss": str(total_gain_loss),
                    "by_method": {
                        method: {
                            "total_gain_loss": str(data["total_gain_loss"]),
                            "total_cost_basis": str(data["total_cost_basis"]),
                            "total_proceeds": str(data["total_proceeds"]),
                            "records_count": data["records_count"]
                        }
                        for method, data in by_method.items()
                    },
                    "estimated_tax_usd": str(total_gain_loss * Decimal("0.21")),
                    "generated_at": datetime.utcnow().isoformat()
                }
        except Exception as e:
            logger.error(f"❌ Error getting annual summary: {str(e)}")
            raise
