#!/usr/bin/env python
"""
Example script demonstrating the Crypto DB system

This script shows how to use all major features of the system:
- Platform management
- Cryptocurrency transactions
- FIAT deposits
- Portfolio tracking
- Tax calculations
"""

from datetime import datetime
from crypto_db.database import SessionLocal, init_db
from crypto_db.platform_service import PlatformService
from crypto_db.crypto_service import CryptoTransactionService
from crypto_db.fiat_service import FiatDepositService
from crypto_db.tax_service import SpanishTaxService
from crypto_db.price_service import PriceService
from crypto_db.models import TransactionType, DepositType


def main():
    """Run example workflow"""

    print("=" * 60)
    print("Crypto DB - Example Workflow")
    print("=" * 60)

    # Initialize database
    print("\n1. Initializing database...")
    init_db()
    print("   ✓ Database initialized")

    # Create session
    db = SessionLocal()

    try:
        # Create platforms
        print("\n2. Creating platforms...")
        binance = PlatformService.create_platform(db, "Binance", "Binance Exchange")
        coinbase = PlatformService.create_platform(db, "Coinbase", "Coinbase Exchange")
        print(f"   ✓ Created: {binance.name} (ID: {binance.id})")
        print(f"   ✓ Created: {coinbase.name} (ID: {coinbase.id})")

        # Add FIAT deposit
        print("\n3. Adding FIAT deposits...")
        deposit = FiatDepositService.create_deposit(
            db=db,
            platform_id=binance.id,
            deposit_type=DepositType.DEPOSIT,
            amount=50000.0,
            currency="EUR",
            transaction_date=datetime(2024, 1, 10, 9, 0, 0),
            notes="Initial deposit",
        )
        print(f"   ✓ Deposited {deposit.amount} {deposit.currency} to {binance.name}")

        # Buy BTC
        print("\n4. Buying cryptocurrency...")
        btc_buy1 = CryptoTransactionService.create_transaction(
            db=db,
            platform_id=binance.id,
            transaction_type=TransactionType.BUY,
            cryptocurrency="BTC",
            amount=1.0,
            price_per_unit=40000.0,
            fiat_currency="EUR",
            fee_amount=100.0,
            transaction_date=datetime(2024, 1, 15, 10, 30, 0),
            notes="First BTC purchase",
        )
        print(
            f"   ✓ Bought {btc_buy1.amount} {btc_buy1.cryptocurrency} "
            f"@ {btc_buy1.price_per_unit} EUR"
        )

        btc_buy2 = CryptoTransactionService.create_transaction(
            db=db,
            platform_id=binance.id,
            transaction_type=TransactionType.BUY,
            cryptocurrency="BTC",
            amount=0.5,
            price_per_unit=42000.0,
            fiat_currency="EUR",
            fee_amount=50.0,
            transaction_date=datetime(2024, 2, 20, 14, 0, 0),
            notes="Second BTC purchase",
        )
        print(
            f"   ✓ Bought {btc_buy2.amount} {btc_buy2.cryptocurrency} "
            f"@ {btc_buy2.price_per_unit} EUR"
        )

        # Buy ETH
        eth_buy = CryptoTransactionService.create_transaction(
            db=db,
            platform_id=coinbase.id,
            transaction_type=TransactionType.BUY,
            cryptocurrency="ETH",
            amount=10.0,
            price_per_unit=2500.0,
            fiat_currency="EUR",
            fee_amount=75.0,
            transaction_date=datetime(2024, 3, 10, 11, 0, 0),
            notes="ETH purchase",
        )
        print(
            f"   ✓ Bought {eth_buy.amount} {eth_buy.cryptocurrency} "
            f"@ {eth_buy.price_per_unit} EUR"
        )

        # Sell some BTC
        print("\n5. Selling cryptocurrency...")
        btc_sell = CryptoTransactionService.create_transaction(
            db=db,
            platform_id=binance.id,
            transaction_type=TransactionType.SELL,
            cryptocurrency="BTC",
            amount=1.0,
            price_per_unit=50000.0,
            fiat_currency="EUR",
            fee_amount=80.0,
            transaction_date=datetime(2024, 6, 15, 15, 30, 0),
            notes="Partial BTC sale",
        )
        print(
            f"   ✓ Sold {btc_sell.amount} {btc_sell.cryptocurrency} "
            f"@ {btc_sell.price_per_unit} EUR"
        )

        # Check portfolio balance
        print("\n6. Portfolio balance:")
        balance = CryptoTransactionService.get_portfolio_balance(db)
        for crypto, amount in balance.items():
            print(f"   {crypto}: {amount:.8f}")

        # Check FIAT balance
        print("\n7. FIAT balance:")
        fiat_balance = FiatDepositService.get_balance(db, currency="EUR")
        print(f"   EUR: {fiat_balance:.2f}")

        # Transaction summary
        print("\n8. Transaction summary:")
        summary = CryptoTransactionService.get_transaction_summary(db)
        print(f"   Total transactions: {summary['total_transactions']}")
        print(f"   Total invested: {summary['total_invested']:.2f} EUR")
        print(f"   Total sold: {summary['total_sold']:.2f} EUR")
        print(f"   Total fees: {summary['total_fees']:.2f} EUR")

        # Calculate capital gains
        print("\n9. Capital gains calculation (2024):")
        gains = SpanishTaxService.calculate_capital_gains(db, 2024)
        print(f"   Total gains: {gains['total_gains']:.2f} EUR")
        print(f"   Total losses: {gains['total_losses']:.2f} EUR")
        print(f"   Net result: {gains['net_result']:.2f} EUR")

        # Calculate tax liability
        print("\n10. Tax liability:")
        if gains["net_result"] > 0:
            tax = SpanishTaxService.calculate_tax_liability(gains["net_result"])
            print(f"   Taxable amount: {tax['taxable_amount']:.2f} EUR")
            print(f"   Tax owed: {tax['tax_owed']:.2f} EUR")
            print(f"   Effective rate: {tax['effective_rate']:.1%}")

            print("\n   Tax breakdown by bracket:")
            for bracket in tax["breakdown"]:
                print(
                    f"   - {bracket['bracket']} EUR: "
                    f"{bracket['amount']:.2f} @ {bracket['rate']:.0%} = "
                    f"{bracket['tax']:.2f} EUR"
                )
        else:
            print("   No tax owed (losses or break-even)")

        # Generate tax report
        print("\n11. Generating tax report...")
        report = SpanishTaxService.generate_tax_report(db, 2024)
        print(f"   ✓ Report generated with ID: {report.id}")

        # Get current prices (if API is accessible)
        print("\n12. Current cryptocurrency prices:")
        try:
            btc_price = PriceService.get_current_price("BTC", "EUR")
            eth_price = PriceService.get_current_price("ETH", "EUR")
            if btc_price:
                print(f"   BTC: {btc_price:.2f} EUR")
            if eth_price:
                print(f"   ETH: {eth_price:.2f} EUR")
        except Exception as e:
            print(f"   ⚠ Could not fetch prices: {e}")

        print("\n" + "=" * 60)
        print("Example workflow completed successfully!")
        print("=" * 60)

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback

        traceback.print_exc()

    finally:
        db.close()


if __name__ == "__main__":
    main()
