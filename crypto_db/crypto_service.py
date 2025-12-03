"""
Service layer for managing cryptocurrency transactions
"""

from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, case

from crypto_db.models import CryptoTransaction, TransactionType


class CryptoTransactionService:
    """Service for managing cryptocurrency transactions"""

    @staticmethod
    def create_transaction(
        db: Session,
        platform_id: int,
        transaction_type: TransactionType,
        cryptocurrency: str,
        amount: float,
        price_per_unit: float,
        fiat_currency: str = "EUR",
        fee_amount: float = 0.0,
        fee_currency: str = "EUR",
        transaction_date: Optional[datetime] = None,
        transaction_id: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> CryptoTransaction:
        """
        Create a new cryptocurrency transaction
        """
        if transaction_date is None:
            transaction_date = datetime.utcnow()

        total_value = amount * price_per_unit

        transaction = CryptoTransaction(
            platform_id=platform_id,
            transaction_type=transaction_type,
            cryptocurrency=cryptocurrency.upper(),
            amount=amount,
            price_per_unit=price_per_unit,
            fiat_currency=fiat_currency,
            total_value=total_value,
            fee_amount=fee_amount,
            fee_currency=fee_currency,
            transaction_date=transaction_date,
            transaction_id=transaction_id,
            notes=notes,
        )

        db.add(transaction)
        db.commit()
        db.refresh(transaction)

        return transaction

    @staticmethod
    def get_transactions(
        db: Session,
        platform_id: Optional[int] = None,
        cryptocurrency: Optional[str] = None,
        transaction_type: Optional[TransactionType] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[CryptoTransaction]:
        """
        Get transactions with optional filtering
        """
        query = db.query(CryptoTransaction)

        if platform_id:
            query = query.filter(CryptoTransaction.platform_id == platform_id)
        if cryptocurrency:
            query = query.filter(CryptoTransaction.cryptocurrency == cryptocurrency.upper())
        if transaction_type:
            query = query.filter(CryptoTransaction.transaction_type == transaction_type)
        if start_date:
            query = query.filter(CryptoTransaction.transaction_date >= start_date)
        if end_date:
            query = query.filter(CryptoTransaction.transaction_date <= end_date)

        return query.order_by(CryptoTransaction.transaction_date.desc()).all()

    @staticmethod
    def get_portfolio_balance(db: Session, cryptocurrency: Optional[str] = None) -> dict:
        """
        Calculate current portfolio balance for each cryptocurrency
        """
        query = db.query(
            CryptoTransaction.cryptocurrency,
            func.sum(
                case(
                    (
                        CryptoTransaction.transaction_type.in_(
                            [
                                TransactionType.BUY,
                                TransactionType.TRANSFER_IN,
                                TransactionType.REWARD,
                                TransactionType.STAKE,
                            ]
                        ),
                        CryptoTransaction.amount,
                    ),
                    (
                        CryptoTransaction.transaction_type.in_(
                            [
                                TransactionType.SELL,
                                TransactionType.TRANSFER_OUT,
                                TransactionType.FEE,
                                TransactionType.UNSTAKE,
                            ]
                        ),
                        -CryptoTransaction.amount,
                    ),
                    else_=0,
                )
            ).label("balance"),
        ).group_by(CryptoTransaction.cryptocurrency)

        if cryptocurrency:
            query = query.filter(CryptoTransaction.cryptocurrency == cryptocurrency.upper())

        results = query.all()

        return {crypto: float(balance) for crypto, balance in results if balance > 0}

    @staticmethod
    def get_transaction_summary(
        db: Session, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ) -> dict:
        """
        Get summary of transactions for a period
        """
        query = db.query(CryptoTransaction)

        if start_date:
            query = query.filter(CryptoTransaction.transaction_date >= start_date)
        if end_date:
            query = query.filter(CryptoTransaction.transaction_date <= end_date)

        transactions = query.all()

        total_invested = sum(
            t.total_value for t in transactions if t.transaction_type in [TransactionType.BUY]
        )

        total_sold = sum(
            t.total_value for t in transactions if t.transaction_type in [TransactionType.SELL]
        )

        total_fees = sum(t.fee_amount for t in transactions)

        return {
            "total_transactions": len(transactions),
            "total_invested": total_invested,
            "total_sold": total_sold,
            "total_fees": total_fees,
            "net_position": total_invested - total_sold - total_fees,
        }
