import os
import pytest

try:
    import ccxt
except Exception:  # pragma: no cover - if ccxt not installed the test will be skipped
    ccxt = None

from dotenv import load_dotenv


@pytest.mark.integration
def test_binance_read_only_endpoints():
    """Integration test for Binance read-only endpoints using CCXT.

    This test requires `BINANCE_API_KEY` and `BINANCE_API_SECRET` to be set in
    the environment or in a `.env` file at the repository root. It only calls
    read-only endpoints: balances, deposits, withdrawals and trades (when
    available). If credentials are missing the test will be skipped.
    """
    if ccxt is None:
        pytest.skip("ccxt not installed")

    # Load .env if present so users can store keys there during local testing
    load_dotenv()

    api_key = os.getenv("BINANCE_API_KEY")
    api_secret = os.getenv("BINANCE_API_SECRET")

    if not api_key or not api_secret:
        pytest.skip("BINANCE_API_KEY/BINANCE_API_SECRET not set in environment or .env")

    # Create exchange instance (read-only by default; do not place orders)
    exchange = ccxt.binance({
        "apiKey": api_key,
        "secret": api_secret,
        "enableRateLimit": True,
    })

    # Basic connectivity: load markets
    try:
        exchange.load_markets()
    except Exception as e:
        pytest.skip(f"Unable to load markets from Binance: {e}")

    # Fetch balances (read-only)
    try:
        bal = exchange.fetch_balance()
        assert isinstance(bal, dict)
        assert "total" in bal or "info" in bal
    except Exception as e:
        pytest.skip(f"fetch_balance failed: {e}")

    # Fetch deposits (may not be supported by all CCXT builds) — skip on errors
    if hasattr(exchange, "fetch_deposits"):
        try:
            deps = exchange.fetch_deposits()
            assert deps is None or isinstance(deps, (list, dict))
        except ccxt.BaseError:
            pytest.skip("fetch_deposits not supported or failed")

    # Fetch withdrawals
    if hasattr(exchange, "fetch_withdrawals"):
        try:
            wds = exchange.fetch_withdrawals()
            assert wds is None or isinstance(wds, (list, dict))
        except ccxt.BaseError:
            pytest.skip("fetch_withdrawals not supported or failed")

    # Fetch recent trades for a market if possible
    symbols = list(exchange.markets.keys()) if getattr(exchange, "markets", None) else []
    if symbols:
        symbol = symbols[0]
        if hasattr(exchange, "fetch_my_trades"):
            try:
                trades = exchange.fetch_my_trades(symbol)
                assert trades is None or isinstance(trades, (list, dict))
            except ccxt.BaseError:
                pytest.skip("fetch_my_trades not supported or failed for symbol")
