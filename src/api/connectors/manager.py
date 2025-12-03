# src/api/connectors/manager.py

"""
Connector Manager
=================

Orchestrates all connector instances.
"""

import logging
import os
import asyncio
import time
from typing import Dict, List, Optional, Any
from enum import Enum
from src.api.connectors.tokens.bridged_token_detector import BridgedTokenDetector
from src.api.connectors.tokens.wrapped_token_detector import WrappedTokenDetector
from src.database.manager import get_db_manager
from src.database.models import ExchangeAccount
from src.database.models import BlockchainWallet, WalletBalance
from src.utils.crypto import decrypt_value
from src.api.connectors.exchanges.binance_connector import BinanceConnector
from src.api.connectors.exchanges.coinbase_connector import CoinbaseConnector
from src.api.connectors.exchanges.kraken_connector import KrakenConnector
from src.services.exchange_service import ExchangeService
from src.api.connectors.wallets.metamask_connector import MetamaskConnector
from src.api.connectors.wallets.phantom_connector import PhantomConnector
from src.services.price_oracle import get_price_at
from decimal import Decimal
from src.utils.time import now_utc

logger = logging.getLogger(__name__)


class ConnectorType(str, Enum):
    """Connector types"""
    EXCHANGE = "exchange"
    BLOCKCHAIN = "blockchain"
    WALLET = "wallet"
    DEFI = "defi"
    ORACLE = "oracle"


class ConnectorManager:
    """Manages all connectors"""
    
    def __init__(self):
        """Initialize connector manager"""
        self.connectors = {}
        self.bridged_detector = BridgedTokenDetector()
        self.wrapped_detector = WrappedTokenDetector()
        self.logger = logging.getLogger("connector.manager")
        # Background sync control attributes
        self._bg_task = None
        self._stop_event = None
        self._exchange_service = ExchangeService()
        # Track accounts that recently failed authentication to avoid log spam
        self._invalid_accounts: Dict[int, Dict[str, Any]] = {}
        # Cooldown in seconds to skip accounts after auth failure
        self._invalid_account_cooldown = 60 * 60  # 1 hour
    
    def register_exchange(self, name: str, connector):
        """Register exchange connector"""
        self.connectors[f"exchange:{name}"] = connector
        self.logger.info(f"✅ Registered exchange: {name}")
    
    def register_blockchain(self, name: str, connector):
        """Register blockchain connector"""
        self.connectors[f"blockchain:{name}"] = connector
        self.logger.info(f"✅ Registered blockchain: {name}")
    
    def register_wallet(self, name: str, connector):
        """Register wallet connector"""
        self.connectors[f"wallet:{name}"] = connector
        self.logger.info(f"✅ Registered wallet: {name}")
    
    def register_defi(self, name: str, connector):
        """Register DeFi connector"""
        self.connectors[f"defi:{name}"] = connector
        self.logger.info(f"✅ Registered DeFi: {name}")
        
    
    def get_connector(self, connector_type: str, name: str):
        """Get connector by type and name"""
        key = f"{connector_type}:{name}"
        return self.connectors.get(key)
    
    async def get_all_balances(self) -> Dict[str, Dict[str, Any]]:
        """Get all balances from all connectors"""
        all_balances = {}
        
        for key, connector in self.connectors.items():
            try:
                balances = await connector.get_balance()
                all_balances[key] = balances
            except Exception as e:
                self.logger.error(f"Error getting balance from {key}: {str(e)}")
        
        return all_balances
    
    async def analyze_tokens(self, balances: Dict[str, Any], network: str) -> Dict[str, Any]:
        """
        Analyze balances for bridged and wrapped tokens
        
        Args:
            balances: Token balances
            network: Network name
        
        Returns:
            Analysis with categorized tokens
        """
        try:
            analysis = {
                "canonical": {},
                "bridged": {},
                "wrapped": {},
                "other": balances
            }
            
            # Detect bridged tokens
            bridged = await self.bridged_detector.detect_all_bridged_tokens(balances, network)
            analysis["bridged"] = bridged
            
            # Detect wrapped tokens
            wrapped = await self.wrapped_detector.detect_all_wrapped_tokens(balances, network)
            analysis["wrapped"] = wrapped
            
            # Remove detected tokens from "other"
            for addr in list(bridged.keys()) + list(wrapped.keys()):
                analysis["other"].pop(addr, None)
            
            self.logger.info(f"✅ Token analysis complete")
            return analysis
        except Exception as e:
            self.logger.error(f"❌ Error analyzing tokens: {str(e)}")
            return {"error": str(e)}        

    async def _background_sync_loop(self, interval_seconds: int = 300):
        """Background loop to sync exchange accounts periodically.

        - Iterates active `ExchangeAccount` rows
        - Decrypts stored API keys using `decrypt_value`
        - Constructs the appropriate connector (currently supports `binance`)
        - Calls connector methods with `persist_account_id` to persist data
        """
        dbm = get_db_manager()
        while True:
            try:
                with dbm.session_context() as session:
                    accounts = session.query(ExchangeAccount).filter_by(is_active=True).all()

                for acct in accounts:
                    # Skip accounts that failed auth recently to reduce noise
                    invalid_info = self._invalid_accounts.get(acct.id)
                    if invalid_info:
                        last_failed = invalid_info.get('last_failed', 0)
                        if (time.time() - last_failed) < self._invalid_account_cooldown:
                            self.logger.debug(f"Skipping ExchangeAccount {acct.id} due to recent auth failures")
                            continue
                        else:
                            # cooldown expired
                            del self._invalid_accounts[acct.id]

                    try:
                        api_key = decrypt_value(acct.api_key_encrypted) or ""
                        api_secret = decrypt_value(acct.api_secret_encrypted) or ""

                        if not api_key or not api_secret:
                            self.logger.warning(f"ExchangeAccount {acct.id} missing decrypted keys, skipping")
                            continue

                        # Map exchange name to connector
                        exch = acct.exchange.lower()
                        if exch == "binance":
                            try:
                                connector = BinanceConnector(api_key, api_secret)
                            except Exception as e:
                                self.logger.error(f"Could not init Binance connector for account {acct.id}: {e}")
                                continue

                            # Fetch and persist balances, deposits, withdrawals, recent trades
                            try:
                                await connector.get_balance(persist_account_id=acct.id)
                            except Exception as e:
                                self.logger.warning(f"Failed fetching balances for acct {acct.id}: {e}")

                            try:
                                await connector.get_deposit_history(persist_account_id=acct.id)
                            except Exception as e:
                                self.logger.warning(f"Failed fetching deposits for acct {acct.id}: {e}")

                            try:
                                await connector.get_withdraw_history(persist_account_id=acct.id)
                            except Exception as e:
                                self.logger.warning(f"Failed fetching withdrawals for acct {acct.id}: {e}")

                            # Recent trades across a few symbols (connector handles rate-limiting)
                            try:
                                await connector.get_all_trades(limit=50, )
                            except Exception as e:
                                self.logger.warning(f"Failed fetching trades for acct {acct.id}: {e}")
                        elif exch == "coinbase":
                            # Coinbase additionally requires a passphrase; try to read it from the ExchangeAccount if present,
                            # otherwise fall back to environment variable `COINBASE_API_PASSPHRASE`.
                            passphrase = None
                            if hasattr(acct, 'api_passphrase_encrypted') and acct.api_passphrase_encrypted:
                                try:
                                    passphrase = decrypt_value(acct.api_passphrase_encrypted)
                                except Exception:
                                    passphrase = None
                            if not passphrase:
                                passphrase = os.getenv('COINBASE_API_PASSPHRASE', '')

                            try:
                                connector = CoinbaseConnector(api_key, api_secret, passphrase)
                            except Exception as e:
                                self.logger.error(f"Could not init Coinbase connector for account {acct.id}: {e}")
                                continue

                            try:
                                await connector.get_balance(persist_account_id=acct.id)
                            except Exception as e:
                                self.logger.warning(f"Failed fetching balances for Coinbase acct {acct.id}: {e}")

                            try:
                                await connector.get_trades(persist_account_id=acct.id, limit=200)
                            except Exception as e:
                                self.logger.warning(f"Failed fetching trades for Coinbase acct {acct.id}: {e}")

                            try:
                                await connector.get_deposit_history(persist_account_id=acct.id, limit=200)
                            except Exception as e:
                                self.logger.warning(f"Failed fetching deposit/withdraw history for Coinbase acct {acct.id}: {e}")

                        elif exch == "kraken":
                            try:
                                connector = KrakenConnector(api_key, api_secret)
                            except Exception as e:
                                self.logger.error(f"Could not init Kraken connector for account {acct.id}: {e}")
                                continue

                            try:
                                await connector.get_balance(persist_account_id=acct.id)
                            except Exception as e:
                                self.logger.warning(f"Failed fetching balances for Kraken acct {acct.id}: {e}")

                            try:
                                await connector.get_trades(persist_account_id=acct.id, limit=200)
                            except Exception as e:
                                self.logger.warning(f"Failed fetching trades for Kraken acct {acct.id}: {e}")

                            try:
                                await connector.get_deposit_history(persist_account_id=acct.id, limit=200)
                            except Exception as e:
                                self.logger.warning(f"Failed fetching deposit/withdraw history for Kraken acct {acct.id}: {e}")

                        else:
                            self.logger.debug(f"No persistence-enabled connector for {exch}")

                        # small pause between accounts to avoid bursts
                        await asyncio.sleep(0.5)
                    except Exception as e:
                        # Detect authentication-related errors and mark account to skip for a cooldown
                        msg = str(e).lower()
                        is_auth_error = False
                        if (('invalid' in msg and ('api' in msg or 'key' in msg or 'apikey' in msg))
                                or 'signature' in msg
                                or '401' in msg
                                or 'unauthorized' in msg):
                            is_auth_error = True

                        if is_auth_error:
                            self._invalid_accounts[acct.id] = {"last_failed": time.time(), "reason": msg}
                            self.logger.warning(f"🔒 Skipping ExchangeAccount {acct.id} for {self._invalid_account_cooldown}s due to auth error: {e}")
                        else:
                            self.logger.error(f"Error processing account {acct.id}: {e}")

                # --- Wallet sync: iterate active blockchain wallets and persist a snapshot
                try:
                    with dbm.session_context() as session:
                        wallets = session.query(BlockchainWallet).filter_by(is_active=True).all()

                    # lightweight native token mapping
                    NATIVE_TOKEN = {
                        "ethereum": "ETH",
                        "arbitrum": "ETH",
                        "base": "ETH",
                        "optimism": "ETH",
                        "polygon": "MATIC",
                        "avalanche": "AVAX",
                        "solana": "SOL",
                    }

                    for w in wallets:
                        try:
                            token = NATIVE_TOKEN.get(w.network, "NATIVE")
                            balance = Decimal('0')

                            if w.wallet_type == 'metamask':
                                conn = MetamaskConnector(w.address)
                                # Metamask connector currently doesn't return balances; we persist native token placeholder
                                balance = Decimal('0')
                                token = NATIVE_TOKEN.get(w.network, token)
                            elif w.wallet_type == 'phantom':
                                try:
                                    conn = PhantomConnector(w.address, network=w.network)
                                except ValueError as e:
                                    self.logger.debug(f"Skipping wallet {w.id}: {e}")
                                    continue

                                if w.network == 'solana':
                                    resp = await conn.get_solana_balance()
                                    balance = Decimal(str(resp.get('balance_sol') or resp.get('balance') or '0'))
                                    token = 'SOL'
                                else:
                                    # fallback: no balance endpoint for non-solana in simplified connector
                                    await conn.get_wallet_info()
                                    balance = Decimal('0')
                                    token = NATIVE_TOKEN.get(w.network, token)
                            else:
                                # unknown wallet type -> skip
                                self.logger.debug(f"No wallet connector for type {w.wallet_type}")
                                continue

                            # compute USD and configured FIAT using price oracle
                            try:
                                # use current time for balance valuations
                                now_ts = int(time.time())
                                p_usd = get_price_at(token, now_ts, vs_currency='usd')
                                balance_usd = (Decimal(p_usd) * balance) if (p_usd is not None) else None
                            except Exception:
                                balance_usd = None

                            try:
                                now_ts = int(time.time())
                                p_fiat = get_price_at(token, now_ts)
                                balance_fiat = (Decimal(p_fiat) * balance) if (p_fiat is not None) else None
                            except Exception:
                                balance_fiat = None

                            # persist snapshot
                            with dbm.session_context() as session:
                                wb = WalletBalance(
                                    wallet_id=w.id,
                                    token=token,
                                    balance=str(balance),
                                    balance_usd=balance_usd,
                                    balance_fiat=balance_fiat,
                                    timestamp=now_utc()
                                )
                                session.add(wb)

                            await asyncio.sleep(0.2)
                        except Exception as e:
                            self.logger.error(f"Error syncing wallet {w.id}: {e}")
                except Exception as e:
                    self.logger.error(f"Wallet sync error: {e}")

                # Sleep until next interval
                await asyncio.sleep(interval_seconds)
            except asyncio.CancelledError:
                self.logger.info("Background sync task cancelled")
                break
            except Exception as e:
                self.logger.error(f"Background sync loop error: {e}")
                # Backoff before retrying
                await asyncio.sleep(min(60, interval_seconds))

    def start_background_sync(self, interval_seconds: int = 300):
        """Start the background sync task. Safe to call multiple times."""
        if self._bg_task and not self._bg_task.done():
            self.logger.info("Background sync already running")
            return

        loop = None
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop:
            self._bg_task = loop.create_task(self._background_sync_loop(interval_seconds))
            self.logger.info("Background sync started (asyncio loop)")
        else:
            # Create a new event loop in a background thread
            def _run_loop():
                new_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(new_loop)
                self._bg_task = new_loop.create_task(self._background_sync_loop(interval_seconds))
                try:
                    new_loop.run_forever()
                finally:
                    pending = asyncio.all_tasks(loop=new_loop)
                    for t in pending:
                        t.cancel()
                    new_loop.run_until_complete(new_loop.shutdown_asyncgens())
                    new_loop.close()

            import threading
            t = threading.Thread(target=_run_loop, daemon=True)
            t.start()
            self.logger.info("Background sync started (threaded loop)")

    def stop_background_sync(self):
        """Stop the background sync task if running."""
        if self._bg_task and not self._bg_task.done():
            try:
                self._bg_task.cancel()
                self.logger.info("Requested cancellation of background sync task")
            except Exception:
                pass
        else:
            self.logger.info("No background sync task to stop")
