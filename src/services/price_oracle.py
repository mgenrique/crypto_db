"""
Lightweight Price Oracle using CoinGecko's public API with simple in-memory caching.

Provides:
- get_price_usd(symbol: str) -> Optional[float]

Mapping of common symbols to CoinGecko ids is used (ETH -> ethereum, BTC -> bitcoin, MATIC -> polygon-pos, SOL -> solana, AVAX -> avalanche-2).
The function is defensive and returns None when price can't be resolved.
"""

import time
import logging
from typing import Optional
import requests
from src.utils.config_loader import ConfigLoader

_CONFIG = ConfigLoader()

logger = logging.getLogger(__name__)

# Conservative fallback mapping for common symbols/ids. This will be
# extended/overridden by values read from YAML configuration at runtime so
# the canonical source of truth can become the YAML files.
_FALLBACK_SYMBOL_MAP = {
    "ETH": "ethereum",
    "BTC": "bitcoin",
    "MATIC": "polygon-pos",
    "SOL": "solana",
    "AVAX": "avalanche-2",
    "USDT": "tether",
    "USDC": "usd-coin",
    "BNB": "binancecoin",
    "DAI": "dai",
    "LINK": "chainlink",
    "LTC": "litecoin",
    "BCH": "bitcoin-cash",
    "DOT": "polkadot",
    "ADA": "cardano",
    "XRP": "ripple",
    "UNI": "uniswap",
    "AAVE": "aave",
    "WBTC": "wrapped-bitcoin",
    "FTM": "fantom",
    "SUSHI": "sushi",
    # wrapped/chain variants that are safe to include by default
    "WETH": "weth",
    "WETH_POLYGON": "weth",
    "WETH_ARBITRUM": "weth",
    "WETH_OPTIMISM": "weth",
    "WETH_BSC": "weth",
    "WBTC_POLYGON": "wrapped-bitcoin",
    "WBTC_ARBITRUM": "wrapped-bitcoin",
    "WBTC_OPTIMISM": "wrapped-bitcoin",
    "USDC_POLYGON": "usd-coin",
    "USDT_POLYGON": "tether",
    "USDC_SOLANA": "usd-coin",
    "USDT_SOLANA": "tether",
    "USDC_BSC": "usd-coin",
    "USDT_BSC": "tether",
    "WBNB": "wbnb",
    "WBNB_BSC": "wbnb",
    "WETH.E": "weth",
    "WBTC.W": "wrapped-bitcoin",
}


# Build final mapping using YAML tokens first (preferred), falling back to
# the conservative hardcoded map for symbols not present in YAML.
SYMBOL_TO_COINGECKO_ID = _FALLBACK_SYMBOL_MAP.copy()
try:
    cfg = ConfigLoader()
    tokens = cfg.get_tokens() or {}
    for sym, info in tokens.items():
        # prefer explicit `coingecko_id` in YAML, otherwise fallback to lowercased symbol
        cg = info.get("coingecko_id") if isinstance(info, dict) else None
        if not cg:
            cg = sym.lower()
        SYMBOL_TO_COINGECKO_ID[sym.upper()] = cg
except Exception:
    # If config cannot be loaded for any reason, keep the fallback mapping
    logger.debug("Failed to build SYMBOL_TO_COINGECKO_ID from YAML; using fallback mapping")

_CACHE = {}
_CACHE_TTL = 60  # seconds
_HISTORICAL_CACHE_TTL = 60 * 60  # 1 hour for historical lookups
_RATE_LIMIT_LAST_CALL = 0.0
_RATE_LIMIT_MIN_INTERVAL = None  # seconds between calls, computed from config


def _fetch_prices(ids: str, vs_currency: str = "usd"):
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={ids}&vs_currencies={vs_currency}"
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.warning(f"CoinGecko fetch failed: {e}")
        return {}


def _ensure_rate_limit():
    """Ensure minimum interval between external CoinGecko calls based on config."""
    global _RATE_LIMIT_LAST_CALL, _RATE_LIMIT_MIN_INTERVAL
    if _RATE_LIMIT_MIN_INTERVAL is None:
        # compute from config (requests per minute)
        try:
            cfg = _CONFIG.get_price_fetcher_config()
            rl = int(cfg.get('coingecko', {}).get('rate_limit', cfg.get('rate_limit', 10)))
            if rl <= 0:
                rl = 10
            _RATE_LIMIT_MIN_INTERVAL = 60.0 / float(rl)
        except Exception:
            _RATE_LIMIT_MIN_INTERVAL = 6.0

    now = time.time()
    elapsed = now - _RATE_LIMIT_LAST_CALL
    if elapsed < _RATE_LIMIT_MIN_INTERVAL:
        to_sleep = _RATE_LIMIT_MIN_INTERVAL - elapsed
        time.sleep(to_sleep)
    _RATE_LIMIT_LAST_CALL = time.time()


def get_price(symbol: str, vs_currency: str = "usd") -> Optional[float]:
    """Return latest price for the given symbol in the requested vs_currency (e.g., 'eur', 'usd')."""
    if not symbol:
        return None
    s = symbol.upper()
    cg_id = SYMBOL_TO_COINGECKO_ID.get(s)
    if not cg_id:
        return None

    cache_key = f"{cg_id}:{vs_currency}"
    now = time.time()
    entry = _CACHE.get(cache_key)
    if entry and now - entry[0] < _CACHE_TTL:
        return entry[1]

    # First consult DB-backed cache if available
    try:
        from src.database.manager import get_db_manager
        from src.database.models import PriceCache, PriceMapping
        dbm = get_db_manager()
        # check cache for latest value (ts_minute = current minute)
        ts_min = int(time.time() // 60 * 60)
        with dbm.session_context() as session:
            cached = session.query(PriceCache).filter_by(coingecko_id=cg_id, vs_currency=vs_currency, ts_minute=ts_min).first()
            if cached and cached.price is not None:
                return float(cached.price)
    except Exception:
        # DB not available or error; fallback to API
        pass

    data = _fetch_prices(cg_id, vs_currency=vs_currency)
    price = None
    if data and cg_id in data and vs_currency in data[cg_id]:
        try:
            price = float(data[cg_id][vs_currency])
        except Exception:
            price = None

    _CACHE[cache_key] = (now, price)

    # persist to DB cache
    try:
        from src.database.manager import get_db_manager
        from src.database.models import PriceCache
        dbm = get_db_manager()
        ts_min = int(time.time() // 60 * 60)
        with dbm.session_context() as session:
            existing = session.query(PriceCache).filter_by(coingecko_id=cg_id, vs_currency=vs_currency, ts_minute=ts_min).first()
            if existing:
                existing.price = price
                existing.fetched_at = now_utc()
            else:
                pc = PriceCache(coingecko_id=cg_id, vs_currency=vs_currency, ts_minute=ts_min, price=price)
                session.add(pc)
    except Exception:
        pass
    return price


def get_price_fiat(symbol: str) -> Optional[float]:
    """Return price in configured fiat currency (from ConfigLoader)."""
    fiat = _CONFIG.get_fiat_currency() or "EUR"
    return get_price(symbol, vs_currency=fiat.lower())


def _fetch_price_range(cg_id: str, vs_currency: str, from_unix: int, to_unix: int):
    """Fetch price series from CoinGecko market_chart/range and return list of prices.

    Returns list of [ts_ms, price] or None on failure.
    """
    url = (
        f"https://api.coingecko.com/api/v3/coins/{cg_id}/market_chart/range"
        f"?vs_currency={vs_currency}&from={from_unix}&to={to_unix}"
    )
    try:
        _ensure_rate_limit()
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        prices = data.get("prices", [])
        if not prices:
            return None
        return prices
    except Exception as e:
        logger.debug(f"CoinGecko range fetch failed for {cg_id}: {e}")
        return None


def get_price_at(symbol: str, when_ts: int, vs_currency: str = None) -> Optional[float]:
    """Return price for `symbol` at UNIX timestamp `when_ts` (seconds).

    Strategy:
    - Resolve symbol -> coingecko id
    - Try market_chart/range with a +/- 1 hour window and pick nearest timestamp
    - If that fails, fall back to /coins/{id}/history?date=DD-MM-YYYY which gives day-level price
    - Cache results keyed by cg_id:vs_currency:when_ts (rounded to minute)
    """
    if not symbol:
        return None
    s = symbol.upper()
    cg_id = SYMBOL_TO_COINGECKO_ID.get(s)
    # If symbol not in static mapping and symbol looks like a contract address, try DB mapping or CoinGecko contract endpoint
    if not cg_id:
        # simple heuristic for Ethereum-style contract addresses
        if isinstance(symbol, str) and symbol.startswith("0x") and len(symbol) >= 40:
            try:
                from src.database.manager import get_db_manager
                from src.database.models import PriceMapping
                dbm = get_db_manager()
                with dbm.session_context() as session:
                    pm = session.query(PriceMapping).filter_by(contract_address=symbol.lower()).first()
                    if pm:
                        cg_id = pm.coingecko_id
            except Exception:
                cg_id = None

            # if still missing, try CoinGecko contract lookup and persist mapping
            if not cg_id:
                try:
                    _ensure_rate_limit()
                    # Try multiple CoinGecko platform slugs in order of likelihood.
                    # The platform slug will be persisted in PriceMapping.network so
                    # it can be used later. If a platform does not support the
                    # address lookup, the request will typically 404 and we move on.
                    platforms = [
                        "ethereum",
                        "polygon-pos",
                        "binance-smart-chain",
                        "arbitrum-one",
                        "avalanche",
                        "base",
                        "solana",
                    ]
                    for platform in platforms:
                        try:
                            url = f"https://api.coingecko.com/api/v3/coins/{platform}/contract/{symbol.lower()}"
                            resp = requests.get(url, timeout=10)
                            if resp.status_code == 200:
                                data = resp.json()
                                cg_id = data.get("id")
                                if cg_id:
                                    # Map CoinGecko platform slug to our config network name
                                    try:
                                        from src.utils.config_loader import ConfigLoader
                                        cfg = ConfigLoader()

                                        def _platform_to_network(slug: str) -> str:
                                            # Start from configurable aliases in YAML, falling
                                            # back to a small conservative builtin map.
                                            try:
                                                aliases = _CONFIG.get_platform_aliases()
                                            except Exception:
                                                aliases = {}

                                            builtin = {
                                                "polygon-pos": "polygon",
                                                "binance-smart-chain": "bsc",
                                                "arbitrum-one": "arbitrum",
                                                "avalanche": "avalanche",
                                                "base": "base",
                                                "ethereum": "ethereum",
                                                "solana": "solana",
                                            }

                                            # Merge: YAML overrides builtin
                                            merged = builtin.copy()
                                            merged.update(aliases or {})

                                            # prefer explicit alias if it exists in config and is available
                                            candidate = merged.get(slug)
                                            avail = _CONFIG.get_available_networks()
                                            if candidate and candidate in avail:
                                                return candidate

                                            # otherwise, if slug itself matches a network key, return it
                                            if slug in avail:
                                                return slug

                                            # as a last resort, try simplified slug (strip suffixes)
                                            simple = slug.split("-")[0]
                                            if simple in avail:
                                                return simple

                                            # fallback to mapped alias even if not in available networks
                                            if candidate:
                                                return candidate

                                            # final fallback to original slug
                                            return slug

                                        mapped_network = _platform_to_network(platform)
                                    except Exception:
                                        mapped_network = platform

                                    # persist mapping with mapped network name (or platform slug)
                                    try:
                                        from src.database.manager import get_db_manager
                                        from src.database.models import PriceMapping
                                        dbm = get_db_manager()
                                        with dbm.session_context() as session:
                                            pm = PriceMapping(symbol=None, network=mapped_network, contract_address=symbol.lower(), coingecko_id=cg_id, source="coin_gecko_contract")
                                            session.add(pm)
                                    except Exception:
                                        pass
                                break
                        except Exception:
                            # try next platform
                            continue
                except Exception:
                    cg_id = None
    if not cg_id:
        return None

    fiat = vs_currency or (_CONFIG.get_fiat_currency() or "EUR")
    vs = fiat.lower()

    # round timestamp to minute for caching stability
    key_ts = int(when_ts // 60 * 60)
    when_ms = int(when_ts * 1000)
    cache_key = f"hist:{cg_id}:{vs}:{key_ts}"
    now = time.time()
    entry = _CACHE.get(cache_key)
    if entry and now - entry[0] < _HISTORICAL_CACHE_TTL:
        return entry[1]

    # Consult DB-backed cache first
    try:
        from src.database.manager import get_db_manager
        from src.database.models import PriceCache
        dbm = get_db_manager()
        with dbm.session_context() as session:
            pc = session.query(PriceCache).filter_by(coingecko_id=cg_id, vs_currency=vs, ts_minute=key_ts).first()
            if pc and pc.price is not None:
                _CACHE[cache_key] = (now, float(pc.price))
                return float(pc.price)
    except Exception:
        pass

    # try market_chart range +/- 1 hour
    from_unix = max(0, key_ts - 3600)
    to_unix = key_ts + 3600
    try:
        prices = _fetch_price_range(cg_id, vs, from_unix, to_unix)
        if prices:
            # find nearest by comparing milliseconds to the requested time (ms)
            nearest = min(prices, key=lambda p: abs(int(p[0]) - when_ms))
            price = float(nearest[1])
            _CACHE[cache_key] = (now, price)
            # persist into DB cache
            try:
                from src.database.manager import get_db_manager
                from src.database.models import PriceCache
                dbm = get_db_manager()
                with dbm.session_context() as session:
                    existing = session.query(PriceCache).filter_by(coingecko_id=cg_id, vs_currency=vs, ts_minute=key_ts).first()
                    if existing:
                        existing.price = price
                        existing.fetched_at = now_utc()
                    else:
                        session.add(PriceCache(coingecko_id=cg_id, vs_currency=vs, ts_minute=key_ts, price=price))
            except Exception:
                pass
            return price
    except Exception:
        pass

    # fallback to /history (day-level)
    try:
        date_str = time.strftime('%d-%m-%Y', time.gmtime(key_ts))
        url = f"https://api.coingecko.com/api/v3/coins/{cg_id}/history?date={date_str}"
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        market = data.get('market_data', {})
        current_price = market.get('current_price', {})
        if vs in current_price:
            price = float(current_price[vs])
            _CACHE[cache_key] = (now, price)
            # persist into DB cache
            try:
                from src.database.manager import get_db_manager
                from src.database.models import PriceCache
                dbm = get_db_manager()
                with dbm.session_context() as session:
                    existing = session.query(PriceCache).filter_by(coingecko_id=cg_id, vs_currency=vs, ts_minute=key_ts).first()
                    if existing:
                        existing.price = price
                        existing.fetched_at = now_utc()
                    else:
                        session.add(PriceCache(coingecko_id=cg_id, vs_currency=vs, ts_minute=key_ts, price=price))
            except Exception:
                pass
            return price
    except Exception as e:
        logger.debug(f"CoinGecko history fetch failed for {cg_id} date {date_str}: {e}")

    _CACHE[cache_key] = (now, None)
    return None
