"""Seed the `price_mappings` table with builtin symbol -> CoinGecko id mappings.

This script is idempotent: it inserts mappings that don't exist and updates
the `coingecko_id` for existing symbol/network rows if they differ. It uses
the `SYMBOL_TO_COINGECKO_ID` mapping from `src.services.price_oracle` as the
canonical source of builtin mappings.

Usage:
    python scripts/seed_price_mappings.py
"""
import logging
import os
import sys

# Ensure project root is on sys.path so `from src...` imports work when the
# script is executed directly from `scripts/`.
root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if root not in sys.path:
    sys.path.insert(0, root)

from src.services import price_oracle
from src.database.manager import get_db_manager
from src.database.models import PriceMapping
from src.utils.time import now_utc

logger = logging.getLogger(__name__)


def seed_builtin_mappings():
    dbm = get_db_manager()
    added = 0
    updated = 0
    skipped = 0

    # Use the builtin SYMBOL_TO_COINGECKO_ID mapping
    mapping = getattr(price_oracle, "SYMBOL_TO_COINGECKO_ID", {})

    with dbm.session_context() as session:
        for sym, cg_id in mapping.items():
            sym_u = sym.upper()
            # We treat builtin mappings as network-agnostic by default
            existing = session.query(PriceMapping).filter_by(symbol=sym_u, network=None).first()
            if existing:
                if existing.coingecko_id != cg_id:
                    existing.coingecko_id = cg_id
                    existing.source = existing.source or "builtin"
                    existing.created_at = existing.created_at or now_utc()
                    updated += 1
                else:
                    skipped += 1
            else:
                pm = PriceMapping(
                    symbol=sym_u,
                    network=None,
                    contract_address=None,
                    coingecko_id=cg_id,
                    source="builtin",
                    created_at=now_utc(),
                )
                session.add(pm)
                added += 1

    logger.info(f"Seeded price_mappings: added={added}, updated={updated}, skipped={skipped}")


def seed_additional_mappings():
    """Seed network/contract specific mappings.

    This will attempt to use a `CONTRACT_TO_COINGECKO` mapping from
    `src.services.price_oracle` if present. Otherwise it falls back to a small
    builtin list of well-known token contracts (primarily Ethereum and
    Polygon) to seed into the DB. The function is idempotent: it upserts by
    `contract_address`+`network` when possible.
    """
    dbm = get_db_manager()
    added = 0
    updated = 0
    skipped = 0

    # Try to use a mapping provided by the price_oracle module, if any.
    contract_mapping = getattr(price_oracle, "CONTRACT_TO_COINGECKO", None)

    if contract_mapping and isinstance(contract_mapping, dict):
        candidates = []
        for (network, contract), cg_id in contract_mapping.items():
            candidates.append({
                "symbol": None,
                "coingecko_id": cg_id,
                "network": network,
                "contract_address": contract,
            })
    else:
        # Small, safe fallback list of common token contracts.
        candidates = [
            {"symbol": "USDC", "coingecko_id": "usd-coin", "network": "ethereum", "contract_address": "0xA0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"},
            {"symbol": "USDT", "coingecko_id": "tether", "network": "ethereum", "contract_address": "0xdac17f958d2ee523a2206206994597c13d831ec7"},
            {"symbol": "DAI",  "coingecko_id": "dai", "network": "ethereum", "contract_address": "0x6b175474e89094c44da98b954eedeac495271d0f"},
            {"symbol": "WBTC", "coingecko_id": "wrapped-bitcoin", "network": "ethereum", "contract_address": "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599"},
            {"symbol": "WETH", "coingecko_id": "weth", "network": "ethereum", "contract_address": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"},
            {"symbol": "USDC", "coingecko_id": "usd-coin", "network": "polygon", "contract_address": "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"},
        ]

    with dbm.session_context() as session:
        for item in candidates:
            contract = item.get("contract_address")
            network = item.get("network")
            cg_id = item.get("coingecko_id")
            symbol = item.get("symbol")

            if not contract or not network:
                continue

            contract_norm = contract.lower()
            existing = session.query(PriceMapping).filter_by(contract_address=contract_norm, network=network).first()
            if existing:
                if existing.coingecko_id != cg_id:
                    existing.coingecko_id = cg_id
                    existing.source = existing.source or "builtin_contract"
                    updated += 1
                else:
                    skipped += 1
            else:
                pm = PriceMapping(
                    symbol=(symbol.upper() if symbol else None),
                    network=network,
                    contract_address=contract_norm,
                    coingecko_id=cg_id,
                    source="builtin_contract",
                    created_at=now_utc(),
                )
                session.add(pm)
                added += 1

    logger.info(f"Seeded additional price_mappings: added={added}, updated={updated}, skipped={skipped}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    seed_builtin_mappings()
    seed_additional_mappings()
