"""Tests for Spanish tax service"""

import pytest
from datetime import datetime
from crypto_db.tax_service import SpanishTaxService
from crypto_db.crypto_service import CryptoTransactionService
from crypto_db.platform_service import PlatformService
from crypto_db.models import TransactionType


@pytest.fixture
def test_platform(db_session):
    """Create a test platform"""
    return PlatformService.create_platform(db_session, "Test Platform")


def test_calculate_capital_gains_simple(db_session, test_platform):
    """Test simple capital gains calculation"""
    # Buy BTC at 40,000
    CryptoTransactionService.create_transaction(
        db=db_session,
        platform_id=test_platform.id,
        transaction_type=TransactionType.BUY,
        cryptocurrency="BTC",
        amount=1.0,
        price_per_unit=40000.0,
        transaction_date=datetime(2024, 1, 15)
    )
    
    # Sell BTC at 50,000
    CryptoTransactionService.create_transaction(
        db=db_session,
        platform_id=test_platform.id,
        transaction_type=TransactionType.SELL,
        cryptocurrency="BTC",
        amount=1.0,
        price_per_unit=50000.0,
        transaction_date=datetime(2024, 6, 15)
    )
    
    gains_data = SpanishTaxService.calculate_capital_gains(db_session, 2024)
    
    assert gains_data["total_gains"] == 10000.0
    assert gains_data["total_losses"] == 0.0
    assert gains_data["net_result"] == 10000.0
    assert len(gains_data["transactions"]) == 1


def test_calculate_capital_gains_fifo(db_session, test_platform):
    """Test FIFO method in capital gains calculation"""
    # Buy 1 BTC at 40,000
    CryptoTransactionService.create_transaction(
        db=db_session,
        platform_id=test_platform.id,
        transaction_type=TransactionType.BUY,
        cryptocurrency="BTC",
        amount=1.0,
        price_per_unit=40000.0,
        transaction_date=datetime(2024, 1, 15)
    )
    
    # Buy 1 BTC at 45,000
    CryptoTransactionService.create_transaction(
        db=db_session,
        platform_id=test_platform.id,
        transaction_type=TransactionType.BUY,
        cryptocurrency="BTC",
        amount=1.0,
        price_per_unit=45000.0,
        transaction_date=datetime(2024, 2, 15)
    )
    
    # Sell 1.5 BTC at 50,000 (should use FIFO)
    CryptoTransactionService.create_transaction(
        db=db_session,
        platform_id=test_platform.id,
        transaction_type=TransactionType.SELL,
        cryptocurrency="BTC",
        amount=1.5,
        price_per_unit=50000.0,
        transaction_date=datetime(2024, 6, 15)
    )
    
    gains_data = SpanishTaxService.calculate_capital_gains(db_session, 2024)
    
    # Should sell: 1 BTC @ 40,000 + 0.5 BTC @ 45,000 = 62,500 cost basis
    # Sale: 1.5 BTC @ 50,000 = 75,000
    # Gain: 75,000 - 62,500 = 12,500
    assert gains_data["net_result"] == 12500.0
    assert gains_data["remaining_holdings"]["BTC"] == 0.5


def test_calculate_tax_liability(db_session):
    """Test Spanish tax liability calculation"""
    # Test first bracket (19%)
    liability = SpanishTaxService.calculate_tax_liability(5000.0)
    assert liability["tax_owed"] == 5000.0 * 0.19
    assert liability["effective_rate"] == 0.19
    
    # Test multiple brackets
    liability = SpanishTaxService.calculate_tax_liability(10000.0)
    expected_tax = (6000.0 * 0.19) + (4000.0 * 0.21)
    assert abs(liability["tax_owed"] - expected_tax) < 0.01
    
    # Test no gains
    liability = SpanishTaxService.calculate_tax_liability(0.0)
    assert liability["tax_owed"] == 0.0


def test_generate_tax_report(db_session, test_platform):
    """Test tax report generation"""
    # Buy and sell BTC
    CryptoTransactionService.create_transaction(
        db=db_session,
        platform_id=test_platform.id,
        transaction_type=TransactionType.BUY,
        cryptocurrency="BTC",
        amount=1.0,
        price_per_unit=40000.0,
        transaction_date=datetime(2024, 1, 15)
    )
    
    CryptoTransactionService.create_transaction(
        db=db_session,
        platform_id=test_platform.id,
        transaction_type=TransactionType.SELL,
        cryptocurrency="BTC",
        amount=1.0,
        price_per_unit=50000.0,
        transaction_date=datetime(2024, 6, 15)
    )
    
    report = SpanishTaxService.generate_tax_report(db_session, 2024)
    
    assert report.id is not None
    assert report.tax_year == 2024
    assert report.total_gains == 10000.0
    assert report.net_result == 10000.0
    assert report.report_data is not None
