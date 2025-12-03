"""Test helpers for DB seeding and common fixtures."""
from src.database.manager import get_db_manager
from src.database.models import ExchangeAccount, BlockchainWallet
from src.utils.time import now_utc


def create_exchange_account(session, user_id: int = 1, exchange: str = "binance", **kwargs):
    ea = ExchangeAccount(
        user_id=user_id,
        exchange=exchange,
        api_key_encrypted=kwargs.get("api_key_encrypted", "x"),
        api_secret_encrypted=kwargs.get("api_secret_encrypted", "x"),
        label=kwargs.get("label", "test acct"),
        is_active=kwargs.get("is_active", True),
        created_at=now_utc(),
    )
    session.add(ea)
    session.flush()
    return ea


def create_blockchain_wallet(session, user_id: int = 1, address: str = "0x" + "1" * 40, network: str = "ethereum", wallet_type: str = "metamask"):
    w = BlockchainWallet(
        user_id=user_id,
        address=address,
        network=network,
        wallet_type=wallet_type,
        label="test wallet",
        is_active=True,
        created_at=now_utc(),
    )
    session.add(w)
    session.flush()
    return w
