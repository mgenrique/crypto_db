"""Tests for crypto transaction service"""

import pytest
from datetime import datetime
from crypto_db.crypto_service import CryptoTransactionService
from crypto_db.platform_service import PlatformService
from crypto_db.models import TransactionType


@pytest.fixture
def test_platform(db_session):
    """Create a test platform"""
    return PlatformService.create_platform(db_session, "Test Platform")


def test_create_crypto_transaction(db_session, test_platform):
    """Test creating a cryptocurrency transaction"""
    transaction = CryptoTransactionService.create_transaction(
        db=db_session,
        platform_id=test_platform.id,
        transaction_type=TransactionType.BUY,
        cryptocurrency="BTC",
        amount=0.5,
        price_per_unit=45000.0,
        fiat_currency="EUR",
        fee_amount=50.0,
    )

    assert transaction.id is not None
    assert transaction.cryptocurrency == "BTC"
    assert transaction.amount == 0.5
    assert transaction.price_per_unit == 45000.0
    assert transaction.total_value == 22500.0
    assert transaction.fee_amount == 50.0


def test_get_transactions(db_session, test_platform):
    """Test retrieving transactions"""
    CryptoTransactionService.create_transaction(
        db=db_session,
        platform_id=test_platform.id,
        transaction_type=TransactionType.BUY,
        cryptocurrency="BTC",
        amount=1.0,
        price_per_unit=40000.0,
    )

    CryptoTransactionService.create_transaction(
        db=db_session,
        platform_id=test_platform.id,
        transaction_type=TransactionType.BUY,
        cryptocurrency="ETH",
        amount=10.0,
        price_per_unit=2500.0,
    )

    all_transactions = CryptoTransactionService.get_transactions(db_session)
    assert len(all_transactions) == 2

    btc_transactions = CryptoTransactionService.get_transactions(db_session, cryptocurrency="BTC")
    assert len(btc_transactions) == 1
    assert btc_transactions[0].cryptocurrency == "BTC"


def test_get_portfolio_balance(db_session, test_platform):
    """Test calculating portfolio balance"""
    # Buy BTC
    CryptoTransactionService.create_transaction(
        db=db_session,
        platform_id=test_platform.id,
        transaction_type=TransactionType.BUY,
        cryptocurrency="BTC",
        amount=1.0,
        price_per_unit=40000.0,
    )

    # Sell some BTC
    CryptoTransactionService.create_transaction(
        db=db_session,
        platform_id=test_platform.id,
        transaction_type=TransactionType.SELL,
        cryptocurrency="BTC",
        amount=0.3,
        price_per_unit=45000.0,
    )

    # Buy ETH
    CryptoTransactionService.create_transaction(
        db=db_session,
        platform_id=test_platform.id,
        transaction_type=TransactionType.BUY,
        cryptocurrency="ETH",
        amount=10.0,
        price_per_unit=2500.0,
    )

    balance = CryptoTransactionService.get_portfolio_balance(db_session)

    assert "BTC" in balance
    assert balance["BTC"] == 0.7
    assert "ETH" in balance
    assert balance["ETH"] == 10.0


def test_get_transaction_summary(db_session, test_platform):
    """Test getting transaction summary"""
    CryptoTransactionService.create_transaction(
        db=db_session,
        platform_id=test_platform.id,
        transaction_type=TransactionType.BUY,
        cryptocurrency="BTC",
        amount=1.0,
        price_per_unit=40000.0,
        fee_amount=100.0,
    )

    CryptoTransactionService.create_transaction(
        db=db_session,
        platform_id=test_platform.id,
        transaction_type=TransactionType.SELL,
        cryptocurrency="BTC",
        amount=0.5,
        price_per_unit=50000.0,
        fee_amount=50.0,
    )

    summary = CryptoTransactionService.get_transaction_summary(db_session)

    assert summary["total_transactions"] == 2
    assert summary["total_invested"] == 40000.0
    assert summary["total_sold"] == 25000.0
    assert summary["total_fees"] == 150.0
    assert summary["net_position"] == 40000.0 - 25000.0 - 150.0
