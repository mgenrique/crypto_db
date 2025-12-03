import os
import pytest

try:
    import ccxt
except Exception:
    ccxt = None

from dotenv import load_dotenv

from src.utils.crypto import encrypt_value
from src.database.manager import init_database, get_db_manager
from src.auth.models import UserModel
from src.database.models import ExchangeAccount, ExchangeBalance
from src.services.exchange_service import ExchangeService


@pytest.mark.integration
def test_binance_debug_persist():
    """Debug test: verify Binance returns balances and why they may not reach DB.

    Steps:
    - Fetch balances via CCXT and verify data presence
    - Persist via ExchangeService
    - Query DB for inserted rows and print debug info if missing
    """
    if ccxt is None:
        pytest.skip("ccxt not installed")

    load_dotenv()
    api_key = os.getenv("BINANCE_API_KEY")
    api_secret = os.getenv("BINANCE_API_SECRET")
    if not api_key or not api_secret:
        pytest.skip("BINANCE_API_KEY/BINANCE_API_SECRET not set")

    # Initialize DB and service
    init_database()
    dbm = get_db_manager()
    svc = ExchangeService(db_manager=dbm)

    # Create a test user and exchange account
    with dbm.session_context() as session:
        user = UserModel(email="debug@example.com", username="debuguser", hashed_password="x")
        session.add(user)
        session.flush()
        acct = ExchangeAccount(
            user_id=user.id,
            exchange="binance",
            api_key_encrypted=encrypt_value(api_key),
            api_secret_encrypted=encrypt_value(api_secret),
            label="debug-binance",
            is_active=True,
        )
        session.add(acct)
        session.flush()
        acct_id = acct.id

    # Fetch balances using CCXT
    exchange = ccxt.binance({"apiKey": api_key, "secret": api_secret, "enableRateLimit": True})
    try:
        exchange.load_markets()
    except Exception as e:
        pytest.skip(f"Unable to load markets: {e}")

    try:
        bal = exchange.fetch_balance()
    except Exception as e:
        pytest.skip(f"fetch_balance failed: {e}")

    # Build balances dict for ExchangeService
    balances = {}
    currencies = set()
    if isinstance(bal, dict):
        for k in ("free", "total", "used"):
            part = bal.get(k)
            if isinstance(part, dict):
                currencies.update(part.keys())

    for c in sorted(currencies):
        free = bal.get('free', {}).get(c) if isinstance(bal.get('free'), dict) else None
        used = bal.get('used', {}).get(c) if isinstance(bal.get('used'), dict) else None
        total = bal.get('total', {}).get(c) if isinstance(bal.get('total'), dict) else None
        if total is None and free is not None and used is not None:
            try:
                total = float(free) + float(used)
            except Exception:
                total = None
        if total is None and free is None and used is None:
            continue
        balances[c] = {"free": str(free or 0), "locked": str(used or 0), "total": str(total or free or 0)}

    # Ensure Binance returned something meaningful
    has_nonzero = any(float(v['total']) > 0 for v in balances.values()) if balances else False
    assert balances, "Binance returned no balance entries"

    # Persist balances and inspect DB
    try:
        svc.persist_balances(acct_id, balances)
    except Exception as e:
        pytest.fail(f"persist_balances raised exception: {e}")

    with dbm.session_context() as session:
        # Count rows in exchange_balances for this account
        count = session.query(ExchangeBalance).filter_by(exchange_account_id=acct_id).count()
        if count == 0:
            # Debug output to help root-cause analysis
            db_url = str(dbm.engine.url)
            pytest.fail(
                f"No rows inserted into exchange_balances (account {acct_id}).\n"
                f"DB url: {db_url}\n"
                f"Balances fetched (sample): {dict(list(balances.items())[:10])}\n"
                f"Has non-zero balance: {has_nonzero}\n"
            )

    # If we reach here, persistence succeeded
    assert count > 0
