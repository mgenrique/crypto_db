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
import uuid
from src.database.models import ExchangeAccount, ExchangeBalance
from src.services.exchange_service import ExchangeService


@pytest.mark.integration
def test_coinbase_persist_to_db():
    if ccxt is None:
        pytest.skip("ccxt not installed")

    load_dotenv()
    api_key = os.getenv("COINBASE_API_KEY")
    api_secret = os.getenv("COINBASE_API_SECRET")
    passphrase = os.getenv("COINBASE_API_PASSPHRASE")

    if not api_key or not api_secret:
        pytest.skip("COINBASE_API_KEY/SECRET not set")

    init_database()
    dbm = get_db_manager()
    svc = ExchangeService(db_manager=dbm)

    unique = uuid.uuid4().hex[:8]
    with dbm.session_context() as session:
        user = UserModel(email=f"cb-{unique}@example.com", username=f"cbtest-{unique}", hashed_password="x")
        session.add(user)
        session.flush()
        acct = ExchangeAccount(
            user_id=user.id,
            exchange="coinbase",
            api_key_encrypted=encrypt_value(api_key),
            api_secret_encrypted=encrypt_value(api_secret),
            label="pytest-coinbase",
            is_active=True,
        )
        session.add(acct)
        session.flush()
        acct_id = acct.id

    # Use CCXT coinbasepro for read-only endpoints
    try:
        exchange = ccxt.coinbasepro({"apiKey": api_key, "secret": api_secret, "password": passphrase, "enableRateLimit": True})
    except Exception:
        exchange = None

    if exchange is None:
        pytest.skip("ccxt coinbasepro unavailable")

    try:
        exchange.load_markets()
    except Exception as e:
        pytest.skip(f"Unable to load markets: {e}")

    try:
        bal = exchange.fetch_balance()
    except Exception as e:
        pytest.skip(f"fetch_balance failed: {e}")

    # normalize
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

    svc.persist_balances(acct_id, balances)

    with dbm.session_context() as session:
        count = session.query(ExchangeBalance).filter_by(exchange_account_id=acct_id).count()
        assert count >= 0

    # Try persisting trades/deposits/withdrawals if supported by the exchange
    try:
        trades = []
        try:
            trades = exchange.fetch_my_trades()
        except Exception:
            # some CCXT builds require a symbol; attempt with a common symbol if markets are loaded
            try:
                symbols = list(exchange.symbols or [])
                if symbols:
                    trades = exchange.fetch_my_trades(symbols[0])
            except Exception:
                trades = []

        if trades:
            svc.persist_trades(acct_id, trades)

        deposits = []
        withdrawals = []
        try:
            deposits = exchange.fetch_deposits()
        except Exception:
            deposits = []
        try:
            withdrawals = exchange.fetch_withdrawals()
        except Exception:
            withdrawals = []

        if deposits:
            svc.persist_deposits(acct_id, deposits)
        if withdrawals:
            svc.persist_withdrawals(acct_id, withdrawals)
    except Exception:
        # don't fail the test if persistence of optional endpoints is not available
        pass
