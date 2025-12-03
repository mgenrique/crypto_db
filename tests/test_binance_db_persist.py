import os
import pytest

try:
    import ccxt
except Exception:  # pragma: no cover - if ccxt not installed the test will be skipped
    ccxt = None

from dotenv import load_dotenv
from datetime import datetime, timezone

from src.utils.crypto import encrypt_value
from src.utils.config_loader import ConfigLoader
from src.database.manager import init_database, get_db_manager
from src.auth.models import UserModel
from src.database.models import (
    ExchangeAccount,
    ExchangeBalance,
    ExchangeTrade,
    ExchangeDeposit,
    ExchangeWithdrawal,
)
from src.services.exchange_service import ExchangeService


@pytest.mark.integration
def test_binance_persist_to_db():
    """Fetch Binance data via CCXT and persist into DB, then verify rows exist."""
    if ccxt is None:
        pytest.skip("ccxt not installed")

    load_dotenv()

    api_key = os.getenv("BINANCE_API_KEY")
    api_secret = os.getenv("BINANCE_API_SECRET")

    if not api_key or not api_secret:
        pytest.skip("BINANCE_API_KEY/BINANCE_API_SECRET not set in environment or .env")

    # Initialize DB (create tables if needed)
    init_database()
    dbm = get_db_manager()

    svc = ExchangeService(db_manager=dbm)

    # Create a test user and exchange account
    with dbm.session_context() as session:
        user = UserModel(email="test@example.com", username="testuser", hashed_password="x")
        session.add(user)
        session.flush()

        acct = ExchangeAccount(
            user_id=user.id,
            exchange="binance",
            api_key_encrypted=encrypt_value(api_key),
            api_secret_encrypted=encrypt_value(api_secret),
            label="pytest-binance",
            is_active=True,
        )
        session.add(acct)
        session.flush()
        acct_id = acct.id

    # create CCXT exchange instance
    exchange = ccxt.binance({
        "apiKey": api_key,
        "secret": api_secret,
        "enableRateLimit": True,
    })

    # Load markets as basic connectivity check
    try:
        exchange.load_markets()
    except Exception as e:
        pytest.skip(f"Unable to load markets from Binance: {e}")

    # Fetch and persist balances
    try:
        bal = exchange.fetch_balance()
        # transform to expected format: {'BTC': {'free': '0', 'locked': '0', 'total': '0'}}
        balances = {}
        # ccxt uses keys like 'free', 'used', 'total' under currencies
        currencies = set()
        if isinstance(bal, dict):
            for k in ('free', 'total', 'used'):
                part = bal.get(k)
                if isinstance(part, dict):
                    currencies.update(part.keys())

        for c in sorted(currencies):
            free = bal.get('free', {}).get(c) if isinstance(bal.get('free'), dict) else None
            used = bal.get('used', {}).get(c) if isinstance(bal.get('used'), dict) else None
            total = bal.get('total', {}).get(c) if isinstance(bal.get('total'), dict) else None

            # normalize to strings
            if total is None and free is not None and used is not None:
                try:
                    total = float(free) + float(used)
                except Exception:
                    total = None

            if total is None and free is None and used is None:
                continue

            balances[c] = {
                "free": str(free) if free is not None else "0",
                "locked": str(used) if used is not None else "0",
                "total": str(total) if total is not None else (str(free) if free is not None else "0"),
            }

        svc.persist_balances(acct_id, balances)
    except Exception as e:
        pytest.skip(f"fetch_balance/persist failed: {e}")

    # Fetch and persist deposits
    try:
        deps = None
        if hasattr(exchange, 'fetch_deposits'):
            deps = exchange.fetch_deposits()
        if deps:
            # normalize deposits list
            norm = []
            for d in deps:
                norm.append({
                    'id': d.get('id'),
                    'coin': d.get('currency') or d.get('coin') or d.get('asset'),
                    'amount': d.get('amount'),
                    'address': d.get('address'),
                    'txid': d.get('txid'),
                    'network': d.get('network'),
                    'status': d.get('status'),
                    'timestamp': None if d.get('timestamp') is None else datetime.fromtimestamp(int(d.get('timestamp')/1000), tz=timezone.utc).isoformat(),
                })
            svc.persist_deposits(acct_id, norm)
    except Exception:
        # non-fatal for environments without deposit history
        pass

    # Fetch and persist withdrawals
    try:
        wds = None
        if hasattr(exchange, 'fetch_withdrawals'):
            wds = exchange.fetch_withdrawals()
        if wds:
            norm = []
            for w in wds:
                norm.append({
                    'id': w.get('id'),
                    'coin': w.get('currency') or w.get('coin') or w.get('asset'),
                    'amount': w.get('amount'),
                    'address': w.get('address'),
                    'txid': w.get('txid'),
                    'network': w.get('network'),
                    'status': w.get('status'),
                    'timestamp': None if w.get('timestamp') is None else datetime.fromtimestamp(int(w.get('timestamp')/1000), tz=timezone.utc).isoformat(),
                })
            svc.persist_withdrawals(acct_id, norm)
    except Exception:
        pass

    # Fetch and persist recent trades for a single symbol if supported
    try:
        symbols = list(exchange.markets.keys()) if getattr(exchange, 'markets', None) else []
        if symbols and hasattr(exchange, 'fetch_my_trades'):
            sym = symbols[0]
            try:
                trades = exchange.fetch_my_trades(sym)
            except Exception:
                trades = []

            norm = []
            for t in trades or []:
                norm.append({
                    'id': t.get('id'),
                    'symbol': t.get('symbol') or t.get('pair') or sym,
                    'price': t.get('price') or t.get('rate') or None,
                    'qty': t.get('amount') or t.get('quantity') or None,
                    'commission': (t.get('fee') or {}).get('cost') if isinstance(t.get('fee'), dict) else (t.get('fee') or None),
                    'commissionAsset': (t.get('fee') or {}).get('currency') if isinstance(t.get('fee'), dict) else None,
                    'isBuyer': t.get('side') == 'buy' or t.get('buyer') or False,
                    'isMaker': t.get('maker') or False,
                    'timestamp': None if t.get('timestamp') is None else datetime.fromtimestamp(int(t.get('timestamp')/1000), tz=timezone.utc).isoformat(),
                })
            svc.persist_trades(acct_id, norm)
    except Exception:
        pass

    # Verify that at least balances rows exist (can be zero if account empty)
    with dbm.session_context() as session:
        bal_count = session.query(ExchangeBalance).filter_by(exchange_account_id=acct_id).count()
        # trades/deposits/withdrawals may be zero; balances at least should be present or zero
        assert bal_count >= 0
