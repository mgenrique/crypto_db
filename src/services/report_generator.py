"""
Report Generator
================

Report generation service for portfolio and tax reports.
"""

from sqlalchemy.orm import Session
from sqlalchemy import func
from decimal import Decimal
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import logging
import json

from src.database.models import (
    WalletModel, TransactionModel, BalanceModel, TaxRecordModel
)

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Report generation service"""

    def __init__(self, db_manager):
        """
        Initialize report generator
        
        Args:
            db_manager: DatabaseManager instance
        """
        self.db_manager = db_manager

    def generate_portfolio_summary(self, wallet_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Generate portfolio summary report
        
        Args:
            wallet_id: Optional wallet filter
            
        Returns:
            Portfolio summary report
        """
        try:
            with self.db_manager.session_context() as session:
                # Get wallets
                wallet_query = session.query(WalletModel)
                if wallet_id:
                    wallet_query = wallet_query.filter_by(id=wallet_id)
                
                wallets = wallet_query.all()
                
                # Get latest balances
                subquery = session.query(
                    BalanceModel.wallet_id,
                    BalanceModel.token_symbol,
                    func.max(BalanceModel.id).label("max_id")
                ).group_by(BalanceModel.wallet_id, BalanceModel.token_symbol).subquery()
                
                latest_balances = session.query(BalanceModel).join(
                    subquery,
                    (BalanceModel.wallet_id == subquery.c.wallet_id) &
                    (BalanceModel.token_symbol == subquery.c.token_symbol) &
                    (BalanceModel.id == subquery.c.max_id)
                ).all()
                
                # Calculate portfolio
                portfolio_by_wallet = {}
                total_value = Decimal("0")
                
                for balance in latest_balances:
                    if balance.wallet_id not in portfolio_by_wallet:
                        portfolio_by_wallet[balance.wallet_id] = {
                            "tokens": {},
                            "total_usd": Decimal("0")
                        }
                    
                    balance_usd = balance.balance_usd or Decimal("0")
                    portfolio_by_wallet[balance.wallet_id]["tokens"][balance.token_symbol] = {
                        "balance": str(balance.balance),
                        "balance_usd": str(balance_usd),
                        "last_update": balance.timestamp.isoformat()
                    }
                    portfolio_by_wallet[balance.wallet_id]["total_usd"] += balance_usd
                    total_value += balance_usd
                
                # Count metrics
                total_wallets = len(wallets)
                total_transactions = session.query(TransactionModel).count()
                total_tokens = session.query(func.count(func.distinct(BalanceModel.token_symbol))).scalar()
                
                logger.info(f"✅ Portfolio summary generated")
                
                return {
                    "report_type": "portfolio_summary",
                    "generated_at": datetime.utcnow().isoformat(),
                    "total_value_usd": str(total_value),
                    "summary": {
                        "wallets_count": total_wallets,
                        "transactions_count": total_transactions,
                        "unique_tokens": total_tokens or 0
                    },
                    "portfolio_by_wallet": {
                        str(wallet_id): {
                            "total_usd": str(data["total_usd"]),
                            "tokens": data["tokens"]
                        }
                        for wallet_id, data in portfolio_by_wallet.items()
                    }
                }
        except Exception as e:
            logger.error(f"❌ Error generating portfolio summary: {str(e)}")
            raise

    def generate_asset_breakdown(self, wallet_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Generate asset allocation breakdown report
        
        Args:
            wallet_id: Optional wallet filter
            
        Returns:
            Asset breakdown report
        """
        try:
            with self.db_manager.session_context() as session:
                # Get latest balances
                subquery = session.query(
                    BalanceModel.token_symbol,
                    func.max(BalanceModel.id).label("max_id")
                )
                
                if wallet_id:
                    subquery = subquery.filter_by(wallet_id=wallet_id)
                
                subquery = subquery.group_by(BalanceModel.token_symbol).subquery()
                
                latest_balances = session.query(BalanceModel).join(
                    subquery,
                    (BalanceModel.token_symbol == subquery.c.token_symbol) &
                    (BalanceModel.id == subquery.c.max_id)
                ).all()
                
                # Calculate breakdown
                total_usd = Decimal("0")
                assets = {}
                
                for balance in latest_balances:
                    balance_usd = balance.balance_usd or Decimal("0")
                    total_usd += balance_usd
                    assets[balance.token_symbol] = {
                        "balance": str(balance.balance),
                        "balance_usd": str(balance_usd)
                    }
                
                # Calculate percentages
                for token, data in assets.items():
                    if total_usd > 0:
                        percentage = (Decimal(data["balance_usd"]) / total_usd) * 100
                        data["percentage"] = f"{percentage:.2f}%"
                    else:
                        data["percentage"] = "0%"
                
                logger.info(f"✅ Asset breakdown generated")
                
                return {
                    "report_type": "asset_breakdown",
                    "generated_at": datetime.utcnow().isoformat(),
                    "total_value_usd": str(total_usd),
                    "assets": sorted(
                        assets.items(),
                        key=lambda x: float(x["balance_usd"]),
                        reverse=True
                    )
                }
        except Exception as e:
            logger.error(f"❌ Error generating asset breakdown: {str(e)}")
            raise

    def generate_transaction_report(self,
                                   wallet_id: Optional[int] = None,
                                   start_date: Optional[datetime] = None,
                                   end_date: Optional[datetime] = None,
                                   limit: int = 1000) -> Dict[str, Any]:
        """
        Generate transaction activity report
        
        Args:
            wallet_id: Optional wallet filter
            start_date: Optional start date
            end_date: Optional end date
            limit: Maximum transactions to include
            
        Returns:
            Transaction report
        """
        try:
            with self.db_manager.session_context() as session:
                query = session.query(TransactionModel)
                
                if wallet_id:
                    query = query.filter_by(wallet_id=wallet_id)
                
                if start_date:
                    query = query.filter(TransactionModel.created_at >= start_date)
                
                if end_date:
                    query = query.filter(TransactionModel.created_at <= end_date)
                
                transactions = query.order_by(
                    TransactionModel.created_at.desc()
                ).limit(limit).all()
                
                # Count by type
                type_counts = {}
                total_fees = Decimal("0")
                
                for tx in transactions:
                    type_counts[tx.tx_type] = type_counts.get(tx.tx_type, 0) + 1
                    total_fees += tx.fee
                
                logger.info(f"✅ Transaction report generated: {len(transactions)} transactions")
                
                return {
                    "report_type": "transaction_activity",
                    "generated_at": datetime.utcnow().isoformat(),
                    "summary": {
                        "total_transactions": len(transactions),
                        "by_type": type_counts,
                        "total_fees": str(total_fees)
                    },
                    "transactions": [
                        {
                            "id": tx.id,
                            "tx_hash": tx.tx_hash,
                            "tx_type": tx.tx_type,
                            "token_in": tx.token_in,
                            "token_out": tx.token_out,
                            "amount_in": str(tx.amount_in) if tx.amount_in else None,
                            "amount_out": str(tx.amount_out) if tx.amount_out else None,
                            "fee": str(tx.fee),
                            "created_at": tx.created_at.isoformat()
                        }
                        for tx in transactions
                    ]
                }
        except Exception as e:
            logger.error(f"❌ Error generating transaction report: {str(e)}")
            raise

    def generate_tax_report(self,
                           wallet_id: int,
                           year: int,
                           tax_method: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate tax calculation report
        
        Args:
            wallet_id: Wallet ID
            year: Tax year
            tax_method: Optional filter by method ('FIFO', 'LIFO', 'AVERAGE_COST')
            
        Returns:
            Tax report
        """
        try:
            with self.db_manager.session_context() as session:
                query = session.query(TaxRecordModel).filter(
                    TaxRecordModel.wallet_id == wallet_id,
                    TaxRecordModel.year == year
                )
                
                if tax_method:
                    query = query.filter_by(tax_method=tax_method)
                
                tax_records = query.all()
                
                # Summarize
                total_gain_loss = Decimal("0")
                total_cost_basis = Decimal("0")
                total_proceeds = Decimal("0")
                
                by_method = {}
                
                for record in tax_records:
                    total_gain_loss += record.gain_loss
                    total_cost_basis += record.cost_basis
                    total_proceeds += record.proceeds
                    
                    method = record.tax_method
                    if method not in by_method:
                        by_method[method] = {
                            "count": 0,
                            "gain_loss": Decimal("0"),
                            "cost_basis": Decimal("0"),
                            "proceeds": Decimal("0")
                        }
                    
                    by_method[method]["count"] += 1
                    by_method[method]["gain_loss"] += record.gain_loss
                    by_method[method]["cost_basis"] += record.cost_basis
                    by_method[method]["proceeds"] += record.proceeds
                
                # US federal tax rate (can be parameterized)
                tax_rate = Decimal("0.21")  # Long-term capital gains
                estimated_tax = total_gain_loss * tax_rate
                
                logger.info(f"✅ Tax report generated for {year}")
                
                return {
                    "report_type": "tax_calculation",
                    "generated_at": datetime.utcnow().isoformat(),
                    "wallet_id": wallet_id,
                    "year": year,
                    "summary": {
                        "total_transactions": len(tax_records),
                        "total_gain_loss": str(total_gain_loss),
                        "total_cost_basis": str(total_cost_basis),
                        "total_proceeds": str(total_proceeds),
                        "estimated_tax_rate": f"{float(tax_rate * 100)}%",
                        "estimated_tax_usd": str(estimated_tax)
                    },
                    "by_method": {
                        method: {
                            "transaction_count": data["count"],
                            "gain_loss": str(data["gain_loss"]),
                            "cost_basis": str(data["cost_basis"]),
                            "proceeds": str(data["proceeds"])
                        }
                        for method, data in by_method.items()
                    }
                }
        except Exception as e:
            logger.error(f"❌ Error generating tax report: {str(e)}")
            raise

    def generate_comprehensive_report(self, wallet_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Generate comprehensive report with all data
        
        Args:
            wallet_id: Optional wallet filter
            
        Returns:
            Comprehensive report
        """
        try:
            portfolio = self.generate_portfolio_summary(wallet_id)
            breakdown = self.generate_asset_breakdown(wallet_id)
            transactions = self.generate_transaction_report(wallet_id)
            
            return {
                "report_type": "comprehensive",
                "generated_at": datetime.utcnow().isoformat(),
                "sections": {
                    "portfolio_summary": portfolio,
                    "asset_breakdown": breakdown,
                    "transaction_activity": transactions
                }
            }
        except Exception as e:
            logger.error(f"❌ Error generating comprehensive report: {str(e)}")
            raise
