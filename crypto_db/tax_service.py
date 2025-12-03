"""
Spanish tax compliance and reporting service
"""

from datetime import datetime
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
import json

from crypto_db.models import CryptoTransaction, FiatDeposit, TaxReport, TransactionType, DepositType


class SpanishTaxService:
    """
    Service for Spanish tax compliance and reporting

    Spanish tax considerations for cryptocurrencies:
    - Gains from crypto sales are subject to capital gains tax
    - Tax rates: 19% (up to 6,000€), 21% (6,000-50,000€), 23% (50,000-200,000€), 26% (200,000+)
    - FIFO (First In, First Out) method for cost basis calculation
    - Annual reporting required (Modelo 100 - IRPF)
    - Declaration of foreign assets if holdings > 50,000€ (Modelo 720)
    """

    TAX_BRACKETS = [(6000, 0.19), (50000, 0.21), (200000, 0.23), (float("inf"), 0.26)]

    @staticmethod
    def calculate_capital_gains(db: Session, tax_year: int) -> Dict:
        """
        Calculate capital gains for a tax year using FIFO method
        """
        start_date = datetime(tax_year, 1, 1)
        end_date = datetime(tax_year, 12, 31, 23, 59, 59)

        # Get all transactions for the tax year
        transactions = (
            db.query(CryptoTransaction)
            .filter(
                CryptoTransaction.transaction_date >= start_date,
                CryptoTransaction.transaction_date <= end_date,
            )
            .order_by(CryptoTransaction.transaction_date)
            .all()
        )

        # Track cost basis for each cryptocurrency using FIFO
        holdings = {}  # {crypto: [(amount, cost_per_unit, date), ...]}
        gains_losses = []

        for tx in transactions:
            crypto = tx.cryptocurrency

            if crypto not in holdings:
                holdings[crypto] = []

            if tx.transaction_type == TransactionType.BUY:
                # Add to holdings
                holdings[crypto].append(
                    {
                        "amount": tx.amount,
                        "cost_per_unit": tx.price_per_unit,
                        "date": tx.transaction_date,
                        "total_cost": tx.total_value,
                    }
                )

            elif tx.transaction_type == TransactionType.SELL:
                # Calculate gain/loss using FIFO
                remaining_to_sell = tx.amount
                sale_price_per_unit = tx.price_per_unit
                total_cost_basis = 0.0

                while remaining_to_sell > 0 and holdings[crypto]:
                    oldest = holdings[crypto][0]

                    if oldest["amount"] <= remaining_to_sell:
                        # Use entire lot
                        total_cost_basis += oldest["total_cost"]
                        remaining_to_sell -= oldest["amount"]
                        holdings[crypto].pop(0)
                    else:
                        # Use partial lot
                        proportion = remaining_to_sell / oldest["amount"]
                        total_cost_basis += oldest["total_cost"] * proportion
                        oldest["amount"] -= remaining_to_sell
                        oldest["total_cost"] -= oldest["total_cost"] * proportion
                        remaining_to_sell = 0

                sale_proceeds = tx.total_value
                gain_loss = sale_proceeds - total_cost_basis - tx.fee_amount

                gains_losses.append(
                    {
                        "cryptocurrency": crypto,
                        "sale_date": tx.transaction_date,
                        "amount_sold": tx.amount,
                        "sale_proceeds": sale_proceeds,
                        "cost_basis": total_cost_basis,
                        "fees": tx.fee_amount,
                        "gain_loss": gain_loss,
                    }
                )

        # Calculate totals
        total_gains = sum(gl["gain_loss"] for gl in gains_losses if gl["gain_loss"] > 0)
        total_losses = sum(abs(gl["gain_loss"]) for gl in gains_losses if gl["gain_loss"] < 0)
        net_gain_loss = total_gains - total_losses

        return {
            "tax_year": tax_year,
            "total_gains": total_gains,
            "total_losses": total_losses,
            "net_result": net_gain_loss,
            "transactions": gains_losses,
            "remaining_holdings": {
                crypto: sum(h["amount"] for h in lots) for crypto, lots in holdings.items() if lots
            },
        }

    @staticmethod
    def calculate_tax_liability(net_gains: float) -> Dict:
        """
        Calculate tax liability based on Spanish tax brackets
        """
        if net_gains <= 0:
            return {"taxable_amount": 0, "tax_owed": 0, "effective_rate": 0, "breakdown": []}

        tax_owed = 0
        remaining = net_gains
        breakdown = []

        prev_bracket = 0
        for bracket_limit, rate in SpanishTaxService.TAX_BRACKETS:
            bracket_amount = min(remaining, bracket_limit - prev_bracket)

            if bracket_amount > 0:
                tax_for_bracket = bracket_amount * rate
                tax_owed += tax_for_bracket

                breakdown.append(
                    {
                        "bracket": f"{prev_bracket} - {bracket_limit if bracket_limit != float('inf') else '∞'}",
                        "amount": bracket_amount,
                        "rate": rate,
                        "tax": tax_for_bracket,
                    }
                )

                remaining -= bracket_amount
                prev_bracket = bracket_limit

            if remaining <= 0:
                break

        effective_rate = (tax_owed / net_gains) if net_gains > 0 else 0

        return {
            "taxable_amount": net_gains,
            "tax_owed": tax_owed,
            "effective_rate": effective_rate,
            "breakdown": breakdown,
        }

    @staticmethod
    def generate_tax_report(db: Session, tax_year: int, report_type: str = "annual") -> TaxReport:
        """
        Generate comprehensive tax report for Spanish compliance
        """
        # Calculate capital gains
        gains_data = SpanishTaxService.calculate_capital_gains(db, tax_year)

        # Calculate tax liability
        tax_liability = SpanishTaxService.calculate_tax_liability(gains_data["net_result"])

        # Include FIAT movements
        start_date = datetime(tax_year, 1, 1)
        end_date = datetime(tax_year, 12, 31, 23, 59, 59)

        fiat_deposits = (
            db.query(FiatDeposit)
            .filter(
                FiatDeposit.transaction_date >= start_date, FiatDeposit.transaction_date <= end_date
            )
            .all()
        )

        fiat_summary = {
            "total_deposits": sum(
                d.amount for d in fiat_deposits if d.deposit_type == DepositType.DEPOSIT
            ),
            "total_withdrawals": sum(
                d.amount for d in fiat_deposits if d.deposit_type == DepositType.WITHDRAWAL
            ),
        }

        # Combine all data
        report_data = {
            "capital_gains": gains_data,
            "tax_liability": tax_liability,
            "fiat_movements": fiat_summary,
        }

        # Create tax report record
        tax_report = TaxReport(
            tax_year=tax_year,
            report_type=report_type,
            total_gains=gains_data["total_gains"],
            total_losses=gains_data["total_losses"],
            net_result=gains_data["net_result"],
            report_data=json.dumps(report_data, default=str),
            notes=f"Spanish tax report for {tax_year}",
        )

        db.add(tax_report)
        db.commit()
        db.refresh(tax_report)

        return tax_report

    @staticmethod
    def check_modelo_720_requirement(db: Session) -> bool:
        """
        Check if Modelo 720 reporting is required (foreign assets > 50,000€)
        """
        # This would need real-time valuation of all holdings
        # Simplified check for now
        from crypto_db.crypto_service import CryptoTransactionService

        portfolio = CryptoTransactionService.get_portfolio_balance(db)

        # Would need to multiply by current prices and sum
        # For now, return False as default
        return False
