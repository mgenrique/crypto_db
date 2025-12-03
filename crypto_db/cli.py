"""
Command-line interface for Crypto DB
"""

import click
from datetime import datetime
from tabulate import tabulate

from crypto_db.database import SessionLocal, init_db
from crypto_db.platform_service import PlatformService
from crypto_db.crypto_service import CryptoTransactionService
from crypto_db.fiat_service import FiatDepositService
from crypto_db.tax_service import SpanishTaxService
from crypto_db.models import TransactionType, DepositType
from crypto_db.price_service import PriceService


@click.group()
def cli():
    """Crypto DB - Sistema de gestión de transacciones de criptomonedas"""
    pass


@cli.command()
def init():
    """Initialize the database"""
    click.echo("Initializing database...")
    init_db()
    click.echo("✓ Database initialized successfully!")


# Platform commands
@cli.group()
def platform():
    """Manage trading platforms"""
    pass


@platform.command('add')
@click.argument('name')
@click.option('--description', '-d', help='Platform description')
def add_platform(name, description):
    """Add a new platform"""
    db = SessionLocal()
    try:
        platform = PlatformService.create_platform(db, name, description)
        click.echo(f"✓ Platform '{platform.name}' created with ID: {platform.id}")
    finally:
        db.close()


@platform.command('list')
def list_platforms():
    """List all platforms"""
    db = SessionLocal()
    try:
        platforms = PlatformService.get_all_platforms(db)
        if platforms:
            data = [[p.id, p.name, p.description or ''] for p in platforms]
            click.echo(tabulate(data, headers=['ID', 'Name', 'Description'], tablefmt='grid'))
        else:
            click.echo("No platforms found.")
    finally:
        db.close()


# Crypto transaction commands
@cli.group()
def crypto():
    """Manage cryptocurrency transactions"""
    pass


@crypto.command('add')
@click.option('--platform-id', '-p', required=True, type=int, help='Platform ID')
@click.option('--type', '-t', 'tx_type', required=True, 
              type=click.Choice(['buy', 'sell', 'transfer_in', 'transfer_out', 'stake', 'unstake', 'reward', 'fee']))
@click.option('--crypto', '-c', required=True, help='Cryptocurrency symbol (BTC, ETH, etc.)')
@click.option('--amount', '-a', required=True, type=float, help='Amount of cryptocurrency')
@click.option('--price', required=True, type=float, help='Price per unit in FIAT')
@click.option('--currency', default='EUR', help='FIAT currency')
@click.option('--fee', default=0.0, type=float, help='Transaction fee')
@click.option('--date', help='Transaction date (YYYY-MM-DD HH:MM:SS)')
@click.option('--tx-id', help='Platform transaction ID')
@click.option('--notes', help='Additional notes')
def add_crypto_transaction(platform_id, tx_type, crypto, amount, price, currency, fee, date, tx_id, notes):
    """Add a cryptocurrency transaction"""
    db = SessionLocal()
    try:
        tx_date = datetime.strptime(date, '%Y-%m-%d %H:%M:%S') if date else None
        
        transaction = CryptoTransactionService.create_transaction(
            db=db,
            platform_id=platform_id,
            transaction_type=TransactionType[tx_type.upper()],
            cryptocurrency=crypto,
            amount=amount,
            price_per_unit=price,
            fiat_currency=currency,
            fee_amount=fee,
            transaction_date=tx_date,
            transaction_id=tx_id,
            notes=notes
        )
        
        click.echo(f"✓ Transaction created with ID: {transaction.id}")
        click.echo(f"  {tx_type.upper()} {amount} {crypto} @ {price} {currency}")
        click.echo(f"  Total: {transaction.total_value} {currency}")
    finally:
        db.close()


@crypto.command('list')
@click.option('--platform-id', '-p', type=int, help='Filter by platform')
@click.option('--crypto', '-c', help='Filter by cryptocurrency')
@click.option('--limit', '-l', default=20, help='Number of transactions to show')
def list_crypto_transactions(platform_id, crypto, limit):
    """List cryptocurrency transactions"""
    db = SessionLocal()
    try:
        transactions = CryptoTransactionService.get_transactions(
            db, platform_id=platform_id, cryptocurrency=crypto
        )[:limit]
        
        if transactions:
            data = [
                [
                    tx.id,
                    tx.platform.name,
                    tx.transaction_type.value,
                    tx.cryptocurrency,
                    tx.amount,
                    f"{tx.price_per_unit:.2f}",
                    f"{tx.total_value:.2f}",
                    tx.transaction_date.strftime('%Y-%m-%d %H:%M')
                ]
                for tx in transactions
            ]
            headers = ['ID', 'Platform', 'Type', 'Crypto', 'Amount', 'Price', 'Total', 'Date']
            click.echo(tabulate(data, headers=headers, tablefmt='grid'))
        else:
            click.echo("No transactions found.")
    finally:
        db.close()


@crypto.command('balance')
@click.option('--crypto', '-c', help='Specific cryptocurrency')
def show_balance(crypto):
    """Show cryptocurrency portfolio balance"""
    db = SessionLocal()
    try:
        balance = CryptoTransactionService.get_portfolio_balance(db, crypto)
        
        if balance:
            click.echo("\n=== Portfolio Balance ===\n")
            for cryptocurrency, amount in balance.items():
                click.echo(f"{cryptocurrency}: {amount:.8f}")
        else:
            click.echo("No holdings found.")
    finally:
        db.close()


@crypto.command('price')
@click.argument('cryptocurrency')
@click.option('--currency', '-c', default='EUR', help='FIAT currency')
def get_price(cryptocurrency, currency):
    """Get current cryptocurrency price"""
    price = PriceService.get_current_price(cryptocurrency, currency)
    
    if price:
        click.echo(f"{cryptocurrency.upper()}: {price:.2f} {currency.upper()}")
    else:
        click.echo(f"Could not fetch price for {cryptocurrency}")


# FIAT commands
@cli.group()
def fiat():
    """Manage FIAT deposits and withdrawals"""
    pass


@fiat.command('add')
@click.option('--platform-id', '-p', required=True, type=int, help='Platform ID')
@click.option('--type', '-t', 'deposit_type', required=True, 
              type=click.Choice(['deposit', 'withdrawal']))
@click.option('--amount', '-a', required=True, type=float, help='Amount')
@click.option('--currency', default='EUR', help='Currency')
@click.option('--date', help='Transaction date (YYYY-MM-DD HH:MM:SS)')
@click.option('--tx-id', help='Transaction ID')
@click.option('--notes', help='Additional notes')
def add_fiat_transaction(platform_id, deposit_type, amount, currency, date, tx_id, notes):
    """Add a FIAT deposit or withdrawal"""
    db = SessionLocal()
    try:
        tx_date = datetime.strptime(date, '%Y-%m-%d %H:%M:%S') if date else None
        
        deposit = FiatDepositService.create_deposit(
            db=db,
            platform_id=platform_id,
            deposit_type=DepositType[deposit_type.upper()],
            amount=amount,
            currency=currency,
            transaction_date=tx_date,
            transaction_id=tx_id,
            notes=notes
        )
        
        click.echo(f"✓ FIAT transaction created with ID: {deposit.id}")
        click.echo(f"  {deposit_type.upper()} {amount} {currency}")
    finally:
        db.close()


@fiat.command('balance')
@click.option('--platform-id', '-p', type=int, help='Filter by platform')
@click.option('--currency', default='EUR', help='Currency')
def show_fiat_balance(platform_id, currency):
    """Show FIAT balance"""
    db = SessionLocal()
    try:
        balance = FiatDepositService.get_balance(db, platform_id, currency)
        
        platform_name = "All platforms"
        if platform_id:
            platform = PlatformService.get_platform(db, platform_id)
            platform_name = platform.name if platform else f"Platform {platform_id}"
        
        click.echo(f"\n{platform_name}: {balance:.2f} {currency}")
    finally:
        db.close()


# Tax commands
@cli.group()
def tax():
    """Tax reporting and compliance"""
    pass


@tax.command('report')
@click.option('--year', '-y', required=True, type=int, help='Tax year')
def generate_tax_report(year):
    """Generate Spanish tax report"""
    db = SessionLocal()
    try:
        click.echo(f"Generating tax report for {year}...")
        
        report = SpanishTaxService.generate_tax_report(db, year)
        
        click.echo(f"\n=== Spanish Tax Report {year} ===\n")
        click.echo(f"Total Gains: {report.total_gains:.2f} EUR")
        click.echo(f"Total Losses: {report.total_losses:.2f} EUR")
        click.echo(f"Net Result: {report.net_result:.2f} EUR")
        
        if report.net_result > 0:
            tax_liability = SpanishTaxService.calculate_tax_liability(report.net_result)
            click.echo(f"\nEstimated Tax: {tax_liability['tax_owed']:.2f} EUR")
            click.echo(f"Effective Rate: {tax_liability['effective_rate']:.1%}")
        
        click.echo(f"\n✓ Report saved with ID: {report.id}")
    finally:
        db.close()


@tax.command('gains')
@click.option('--year', '-y', required=True, type=int, help='Tax year')
def show_capital_gains(year):
    """Calculate capital gains for a year"""
    db = SessionLocal()
    try:
        gains_data = SpanishTaxService.calculate_capital_gains(db, year)
        
        click.echo(f"\n=== Capital Gains {year} ===\n")
        click.echo(f"Total Gains: {gains_data['total_gains']:.2f} EUR")
        click.echo(f"Total Losses: {gains_data['total_losses']:.2f} EUR")
        click.echo(f"Net Result: {gains_data['net_result']:.2f} EUR")
        
        if gains_data['transactions']:
            click.echo(f"\nTransactions: {len(gains_data['transactions'])}")
            
        if gains_data['remaining_holdings']:
            click.echo("\nRemaining Holdings:")
            for crypto, amount in gains_data['remaining_holdings'].items():
                click.echo(f"  {crypto}: {amount:.8f}")
    finally:
        db.close()


if __name__ == '__main__':
    cli()
