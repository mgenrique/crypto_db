"""
Service layer for managing FIAT deposits and withdrawals
"""

from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, case

from crypto_db.models import FiatDeposit, DepositType


class FiatDepositService:
    """Service for managing FIAT deposits and withdrawals"""

    @staticmethod
    def create_deposit(
        db: Session,
        platform_id: int,
        deposit_type: DepositType,
        amount: float,
        currency: str = "EUR",
        transaction_date: Optional[datetime] = None,
        transaction_id: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> FiatDeposit:
        """
        Create a new FIAT deposit or withdrawal
        """
        if transaction_date is None:
            transaction_date = datetime.utcnow()

        deposit = FiatDeposit(
            platform_id=platform_id,
            deposit_type=deposit_type,
            amount=amount,
            currency=currency,
            transaction_date=transaction_date,
            transaction_id=transaction_id,
            notes=notes,
        )

        db.add(deposit)
        db.commit()
        db.refresh(deposit)

        return deposit

    @staticmethod
    def get_deposits(
        db: Session,
        platform_id: Optional[int] = None,
        deposit_type: Optional[DepositType] = None,
        currency: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[FiatDeposit]:
        """
        Get FIAT deposits with optional filtering
        """
        query = db.query(FiatDeposit)

        if platform_id:
            query = query.filter(FiatDeposit.platform_id == platform_id)
        if deposit_type:
            query = query.filter(FiatDeposit.deposit_type == deposit_type)
        if currency:
            query = query.filter(FiatDeposit.currency == currency)
        if start_date:
            query = query.filter(FiatDeposit.transaction_date >= start_date)
        if end_date:
            query = query.filter(FiatDeposit.transaction_date <= end_date)

        return query.order_by(FiatDeposit.transaction_date.desc()).all()

    @staticmethod
    def get_balance(db: Session, platform_id: Optional[int] = None, currency: str = "EUR") -> float:
        """
        Calculate FIAT balance for a platform
        """
        query = db.query(
            func.sum(
                case(
                    (FiatDeposit.deposit_type == DepositType.DEPOSIT, FiatDeposit.amount),
                    (FiatDeposit.deposit_type == DepositType.WITHDRAWAL, -FiatDeposit.amount),
                    else_=0,
                )
            )
        ).filter(FiatDeposit.currency == currency)

        if platform_id:
            query = query.filter(FiatDeposit.platform_id == platform_id)

        result = query.scalar()

        return float(result) if result else 0.0

    @staticmethod
    def get_deposit_summary(
        db: Session,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        currency: str = "EUR",
    ) -> dict:
        """
        Get summary of FIAT deposits for a period
        """
        query = db.query(FiatDeposit).filter(FiatDeposit.currency == currency)

        if start_date:
            query = query.filter(FiatDeposit.transaction_date >= start_date)
        if end_date:
            query = query.filter(FiatDeposit.transaction_date <= end_date)

        deposits = query.all()

        total_deposits = sum(d.amount for d in deposits if d.deposit_type == DepositType.DEPOSIT)

        total_withdrawals = sum(
            d.amount for d in deposits if d.deposit_type == DepositType.WITHDRAWAL
        )

        return {
            "total_transactions": len(deposits),
            "total_deposits": total_deposits,
            "total_withdrawals": total_withdrawals,
            "net_balance": total_deposits - total_withdrawals,
            "currency": currency,
        }
