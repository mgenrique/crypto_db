import os
import json
from dotenv import load_dotenv

load_dotenv()

try:
    import ccxt
except Exception as e:
    print(json.dumps({"error": "ccxt not installed", "detail": str(e)}))
    raise


SENSITIVE_KEYS = {
    "apiKey",
    "secret",
    "id",
    "txid",
    "address",
    "withdrawalId",
    "depositId",
    "orderId",
    "clientOrderId",
    "signature",
    "info",
}


def mask_value(v):
    if v is None:
        return None
    if isinstance(v, (int, float, bool)):
        return v
    s = str(v)
    if len(s) > 64:
        return s[:6] + '...' + s[-6:]
    return s


def sanitize(obj):
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            lk = k.lower()
            if k in SENSITIVE_KEYS or any(sub in lk for sub in ("key", "secret", "token", "passwd")):
                out[k] = "***MASKED***"
            elif k == "info" and isinstance(v, dict):
                # show keys but mask values
                out[k] = {kk: ("***MASKED***" if isinstance(vv, (str, dict, list)) else vv) for kk, vv in v.items()}
            else:
                out[k] = sanitize(v)
        return out
    elif isinstance(obj, list):
        return [sanitize(i) for i in obj]
    else:
        # primitive
        if isinstance(obj, str):
            # mask long-looking tokens
            if obj.startswith("sk_") or len(obj) > 128:
                return "***MASKED***"
            return obj
        return obj


def main():
    api_key = os.getenv("BINANCE_API_KEY")
    api_secret = os.getenv("BINANCE_API_SECRET")

    if not api_key or not api_secret:
        print(json.dumps({"skipped": "BINANCE_API_KEY/BINANCE_API_SECRET not set"}))
        return

    exchange = ccxt.binance({
        "apiKey": api_key,
        "secret": api_secret,
        "enableRateLimit": True,
    })

    out = {}

    try:
        exchange.load_markets()
        out["markets_loaded"] = True
    except Exception as e:
        out["markets_error"] = str(e)

    # fetch balance
    try:
        bal = exchange.fetch_balance()
        out["balance"] = sanitize(bal)
    except Exception as e:
        out["balance_error"] = str(e)

    # deposits
    try:
        if hasattr(exchange, "fetch_deposits"):
            deps = exchange.fetch_deposits()
            out["deposits"] = sanitize(deps)
        else:
            out["deposits"] = "not_supported"
    except Exception as e:
        out["deposits_error"] = str(e)

    # withdrawals
    try:
        if hasattr(exchange, "fetch_withdrawals"):
            wds = exchange.fetch_withdrawals()
            out["withdrawals"] = sanitize(wds)
        else:
            out["withdrawals"] = "not_supported"
    except Exception as e:
        out["withdrawals_error"] = str(e)

    # trades (my trades) for first market
    try:
        symbols = list(exchange.markets.keys()) if getattr(exchange, "markets", None) else []
        if symbols and hasattr(exchange, "fetch_my_trades"):
            sym = symbols[0]
            tr = exchange.fetch_my_trades(sym)
            out["my_trades_sample_symbol"] = sym
            out["my_trades"] = sanitize(tr[:10]) if isinstance(tr, list) else sanitize(tr)
        else:
            out["my_trades"] = "not_supported_or_no_markets"
    except Exception as e:
        out["my_trades_error"] = str(e)

    print(json.dumps(out, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
