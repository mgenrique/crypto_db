"""
Script: Persist wallet balances for METAMASK_* and PHANTOM_* env vars

- Reads env vars starting with METAMASK_ and PHANTOM_
- Creates `BlockchainWallet` rows for each address (if missing)
- Uses connectors to fetch balances when available and writes `WalletBalance` rows

Run with: `python -m scripts.persist_wallet_balances` or `python scripts/persist_wallet_balances.py`
"""

import os
import sys
import asyncio
from dotenv import load_dotenv

# Ensure project root is on sys.path so `from src...` imports work when the
# script is executed directly from `scripts/`.
root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if root not in sys.path:
    sys.path.insert(0, root)

from src.database import init_database, get_db_manager
from src.database.models import BlockchainWallet, WalletBalance
from src.utils.time import now_utc
from src.api.connectors.wallets.metamask_connector import MetamaskConnector
from src.api.connectors.wallets.phantom_connector import PhantomConnector
from src.services.price_oracle import get_price_usd, get_price_fiat
from decimal import Decimal

# Map networks to native token symbols when possible
NATIVE_TOKEN = {
    "ethereum": "ETH",
    "arbitrum": "ETH",
    "base": "ETH",
    "optimism": "ETH",
    "polygon": "MATIC",
    "avalanche": "AVAX",
    "solana": "SOL",
}


def find_env_wallets(prefix: str):
    """Yield (env_key, network, address) for env vars with given prefix."""
    for k, v in os.environ.items():
        if not k.startswith(prefix):
            continue
        addr = v.strip()
        if not addr:
            continue
        # network part after prefix_ (e.g., METAMASK_ETHEREUM -> ETHEREUM)
        parts = k.split("_", 1)
        network = parts[1].lower() if len(parts) > 1 else ""
        yield k, network, addr


async def persist_metamask(wallet_address: str, network: str, dbm, user_id: int):
    # ensure blockchain wallet exists
    with dbm.session_context() as session:
        w = session.query(BlockchainWallet).filter_by(address=wallet_address, network=network).first()
        if not w:
            w = BlockchainWallet(address=wallet_address, network=network, wallet_type='metamask', user_id=user_id)
            session.add(w)
            session.flush()
        wallet_id = w.id

    # MetamaskConnector doesn't provide chain RPC in this simplified connector,
    # so we'll use the connector for address validation and persist a zero/default balance
    conn = MetamaskConnector(wallet_address)
    addrs = await conn.get_addresses()

    # choose token
    token = NATIVE_TOKEN.get(network, "NATIVE")
    balance = "0"

    with dbm.session_context() as session:
        # compute USD equivalent when possible
        try:
            price_usd = get_price_usd(token)
            balance_usd = (Decimal(balance) * Decimal(price_usd)) if price_usd is not None else None
        except Exception:
            balance_usd = None

        try:
            price_fiat = get_price_fiat(token)
            balance_fiat = (Decimal(balance) * Decimal(price_fiat)) if price_fiat is not None else None
        except Exception:
            balance_fiat = None

        wb = WalletBalance(wallet_id=wallet_id, token=token, balance=str(balance), balance_usd=balance_usd, balance_fiat=balance_fiat, timestamp=now_utc())
        session.add(wb)

    print(f"Persisted Metamask {network} {wallet_address[:8]}... -> token={token} balance={balance}")


async def persist_phantom(wallet_address: str, network: str, dbm, user_id: int):
    with dbm.session_context() as session:
        w = session.query(BlockchainWallet).filter_by(address=wallet_address, network=network).first()
        if not w:
            w = BlockchainWallet(address=wallet_address, network=network, wallet_type='phantom', user_id=user_id)
            session.add(w)
            session.flush()
        wallet_id = w.id

    balance = "0"
    token = NATIVE_TOKEN.get(network, "NATIVE")

    try:
        conn = PhantomConnector(wallet_address, network=network)
        if network == "solana":
            resp = await conn.get_solana_balance()
            # resp: {"address":..., "balance_sol": "0", "balance_lamports": 0, "network": "solana"}
            balance = str(resp.get('balance_sol') or resp.get('balance') or 0)
            token = "SOL"
        else:
            # fallback: use get_wallet_info (no balance provided in this simplified connector)
            await conn.get_wallet_info()
            balance = "0"
    except ValueError as e:
        # Unsupported network from connector
        print(f"Skipping Phantom {network} for {wallet_address[:8]}...: {e}")
        return
    except Exception as e:
        print(f"Warning: phantom connector failed for {wallet_address} on {network}: {e}")

    with dbm.session_context() as session:
        try:
            price_usd = get_price_usd(token)
            balance_usd = (Decimal(balance) * Decimal(price_usd)) if price_usd is not None else None
        except Exception:
            balance_usd = None

        try:
            price_fiat = get_price_fiat(token)
            balance_fiat = (Decimal(balance) * Decimal(price_fiat)) if price_fiat is not None else None
        except Exception:
            balance_fiat = None

        wb = WalletBalance(wallet_id=wallet_id, token=token, balance=str(balance), balance_usd=balance_usd, balance_fiat=balance_fiat, timestamp=now_utc())
        session.add(wb)

    print(f"Persisted Phantom {network} {wallet_address[:8]}... -> token={token} balance={balance}")


async def main():
    load_dotenv()
    init_database()
    dbm = get_db_manager()

    # Determine owner id for imported blockchain wallets. In single-user mode
    # there is no `users` table; use a fixed owner id from env (default 0).
    try:
        system_user_id = int(os.getenv('WALLET_SYNC_USER_ID', '0'))
    except Exception:
        system_user_id = 0

    tasks = []

    # Metamask envs
    for k, network, addr in find_env_wallets('METAMASK_'):
        tasks.append(persist_metamask(addr, network, dbm, system_user_id))

    # Phantom envs
    for k, network, addr in find_env_wallets('PHANTOM_'):
        tasks.append(persist_phantom(addr, network, dbm, system_user_id))

    if not tasks:
        print("No METAMASK_* or PHANTOM_* env vars set (or they are empty). Nothing to do.")
        return

    await asyncio.gather(*tasks)


if __name__ == '__main__':
    asyncio.run(main())
