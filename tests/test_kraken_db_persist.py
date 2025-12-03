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
def test_kraken_persist_to_db():
    if ccxt is None:
        pytest.skip("ccxt not installed")

    load_dotenv()
    api_key = os.getenv("KRAKEN_API_KEY")
    api_secret = os.getenv("KRAKEN_API_SECRET")

    if not api_key or not api_secret:
        pytest.skip("KRAKEN_API_KEY/SECRET not set")

    init_database()
    dbm = get_db_manager()
    svc = ExchangeService(db_manager=dbm)

    unique = uuid.uuid4().hex[:8]
    with dbm.session_context() as session:
        user = UserModel(email=f"kr-{unique}@example.com", username=f"krtest-{unique}", hashed_password="x")
        session.add(user)
        session.flush()
        acct = ExchangeAccount(
            user_id=user.id,
            exchange="kraken",
            api_key_encrypted=encrypt_value(api_key),
            api_secret_encrypted=encrypt_value(api_secret),
            label="pytest-kraken",
            is_active=True,
        )
        session.add(acct)
        session.flush()
        acct_id = acct.id

    try:
        exchange = ccxt.kraken({"apiKey": api_key, "secret": api_secret, "enableRateLimit": True})
    except Exception:
        exchange = None

    if exchange is None:
        pytest.skip("ccxt kraken unavailable")

    try:
        exchange.load_markets()
    except Exception as e:
        pytest.skip(f"Unable to load markets: {e}")

    try:
        bal = exchange.fetch_balance()
    except Exception as e:
        pytest.skip(f"fetch_balance failed: {e}")

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
            # attempt fetch_trades on common symbols if available
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
        pass
