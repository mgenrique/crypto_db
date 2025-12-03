"""Tests for platform service"""

import pytest
from crypto_db.platform_service import PlatformService


def test_create_platform(db_session):
    """Test creating a platform"""
    platform = PlatformService.create_platform(
        db_session, name="Binance", description="Binance Exchange"
    )

    assert platform.id is not None
    assert platform.name == "Binance"
    assert platform.description == "Binance Exchange"


def test_get_platform(db_session):
    """Test retrieving a platform"""
    platform = PlatformService.create_platform(db_session, "Coinbase")

    retrieved = PlatformService.get_platform(db_session, platform.id)

    assert retrieved is not None
    assert retrieved.id == platform.id
    assert retrieved.name == "Coinbase"


def test_get_platform_by_name(db_session):
    """Test retrieving a platform by name"""
    PlatformService.create_platform(db_session, "Kraken")

    platform = PlatformService.get_platform_by_name(db_session, "Kraken")

    assert platform is not None
    assert platform.name == "Kraken"


def test_get_all_platforms(db_session):
    """Test retrieving all platforms"""
    PlatformService.create_platform(db_session, "Binance")
    PlatformService.create_platform(db_session, "Coinbase")
    PlatformService.create_platform(db_session, "Kraken")

    platforms = PlatformService.get_all_platforms(db_session)

    assert len(platforms) == 3
    assert all(p.name in ["Binance", "Coinbase", "Kraken"] for p in platforms)


def test_update_platform(db_session):
    """Test updating a platform"""
    platform = PlatformService.create_platform(db_session, "Test Platform")

    updated = PlatformService.update_platform(
        db_session, platform.id, name="Updated Platform", description="New description"
    )

    assert updated.name == "Updated Platform"
    assert updated.description == "New description"


def test_delete_platform(db_session):
    """Test deleting a platform"""
    platform = PlatformService.create_platform(db_session, "To Delete")

    result = PlatformService.delete_platform(db_session, platform.id)

    assert result is True

    retrieved = PlatformService.get_platform(db_session, platform.id)
    assert retrieved is None
