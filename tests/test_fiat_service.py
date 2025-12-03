"""Tests for FIAT deposit service"""

import pytest
from crypto_db.fiat_service import FiatDepositService
from crypto_db.platform_service import PlatformService
from crypto_db.models import DepositType


@pytest.fixture
def test_platform(db_session):
    """Create a test platform"""
    return PlatformService.create_platform(db_session, "Test Platform")


def test_create_fiat_deposit(db_session, test_platform):
    """Test creating a FIAT deposit"""
    deposit = FiatDepositService.create_deposit(
        db=db_session,
        platform_id=test_platform.id,
        deposit_type=DepositType.DEPOSIT,
        amount=10000.0,
        currency="EUR"
    )
    
    assert deposit.id is not None
    assert deposit.amount == 10000.0
    assert deposit.currency == "EUR"
    assert deposit.deposit_type == DepositType.DEPOSIT


def test_get_deposits(db_session, test_platform):
    """Test retrieving deposits"""
    FiatDepositService.create_deposit(
        db=db_session,
        platform_id=test_platform.id,
        deposit_type=DepositType.DEPOSIT,
        amount=5000.0
    )
    
    FiatDepositService.create_deposit(
        db=db_session,
        platform_id=test_platform.id,
        deposit_type=DepositType.WITHDRAWAL,
        amount=2000.0
    )
    
    all_deposits = FiatDepositService.get_deposits(db_session)
    assert len(all_deposits) == 2
    
    deposits_only = FiatDepositService.get_deposits(
        db_session, deposit_type=DepositType.DEPOSIT
    )
    assert len(deposits_only) == 1
    assert deposits_only[0].deposit_type == DepositType.DEPOSIT


def test_get_fiat_balance(db_session, test_platform):
    """Test calculating FIAT balance"""
    FiatDepositService.create_deposit(
        db=db_session,
        platform_id=test_platform.id,
        deposit_type=DepositType.DEPOSIT,
        amount=10000.0
    )
    
    FiatDepositService.create_deposit(
        db=db_session,
        platform_id=test_platform.id,
        deposit_type=DepositType.WITHDRAWAL,
        amount=3000.0
    )
    
    balance = FiatDepositService.get_balance(db_session)
    
    assert balance == 7000.0


def test_get_deposit_summary(db_session, test_platform):
    """Test getting deposit summary"""
    FiatDepositService.create_deposit(
        db=db_session,
        platform_id=test_platform.id,
        deposit_type=DepositType.DEPOSIT,
        amount=10000.0
    )
    
    FiatDepositService.create_deposit(
        db=db_session,
        platform_id=test_platform.id,
        deposit_type=DepositType.DEPOSIT,
        amount=5000.0
    )
    
    FiatDepositService.create_deposit(
        db=db_session,
        platform_id=test_platform.id,
        deposit_type=DepositType.WITHDRAWAL,
        amount=3000.0
    )
    
    summary = FiatDepositService.get_deposit_summary(db_session)
    
    assert summary["total_transactions"] == 3
    assert summary["total_deposits"] == 15000.0
    assert summary["total_withdrawals"] == 3000.0
    assert summary["net_balance"] == 12000.0
    assert summary["currency"] == "EUR"
