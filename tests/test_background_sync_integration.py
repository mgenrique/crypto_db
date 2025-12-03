import asyncio
import os
import pytest
from src.database.manager import init_database, get_db_manager
try:
    from dotenv import load_dotenv
    # load .env from repo root so test can pick up credentials
    load_dotenv()
except Exception:
    # If python-dotenv is not installed, continue — test will read environment directly
    pass
from src.api.connectors.manager import ConnectorManager
from src.database.models import ExchangeAccount, BlockchainWallet
from src.auth.models import UserModel
from src.utils.crypto import encrypt_value
from decimal import Decimal
from datetime import datetime


class FakeExchangeConnector:
    def __init__(self, name="fake"):
        self.name = name

    async def get_balance(self, persist_account_id=None):
        # Return a couple of token balances including a token with a contract
        balances = {
            "ETH": {"free": "0.5", "locked": "0", "total": "0.5"},
            "USDC": {"free": "1000", "locked": "0", "total": "1000", "contractAddress": "0xA0b86991c6218b36c1d19d4a2e9eb0ce3606eb48", "network": "ethereum"}
        }
        if persist_account_id:
            # allow ExchangeService to persist
            await asyncio.get_event_loop().run_in_executor(None, lambda: None)
        return balances

    async def get_deposit_history(self, persist_account_id=None, limit=100):
        now = datetime.utcnow().isoformat()
        deposits = [
            {"id": "d1", "coin": "USDC", "amount": "1000", "address": "0xabc", "txid": "tx1", "network": "ethereum", "status": "completed", "timestamp": now}
        ]
        return deposits

    async def get_withdraw_history(self, persist_account_id=None, limit=100):
        now = datetime.utcnow().isoformat()
        withdrawals = [
            {"id": "w1", "coin": "ETH", "amount": "0.1", "address": "0xdef", "txid": "tx2", "network": "ethereum", "status": "completed", "timestamp": now}
        ]

        return withdrawals

    async def get_trades(self, symbol=None, limit=100, persist_account_id=None):
        now = datetime.utcnow().isoformat()
        return [{"id": "t1", "symbol": "ETHUSDC", "price": "2000", "qty": "0.1", "commission": "0.001", "commissionAsset": "USDC", "isBuyer": True, "isMaker": False, "timestamp": now}]


class FakePhantomConnector:
    def __init__(self, address, network=None):
        self.address = address
        self.network = network

    async def get_solana_balance(self):
        return {"balance_sol": "2.5", "balance": "2.5"}

    async def get_wallet_info(self):
        return {"address": self.address}


def test_background_sync_integration(tmp_path):
    """Integration-style test: initialize DB, register fake connectors and persist data as background sync would.

    This test wraps the async flow with `asyncio.run()` so it can run without pytest-asyncio.
    """

    async def _main():
        # Initialize DB (creates tables and seeds price_mappings)
        init_database()

        dbm = get_db_manager()

        # Create a user and exchange accounts + wallets
        with dbm.session_context() as session:
            import uuid
            unique_email = f"test+{uuid.uuid4().hex}@example.com"
            user = UserModel(email=unique_email, username=f"testuser_{uuid.uuid4().hex[:6]}", hashed_password="x")
            session.add(user)
            session.flush()

            # Create exchange accounts for binance, coinbase, kraken
            accounts = []
            for exch in ("binance", "coinbase", "kraken"):
                acct = ExchangeAccount(user_id=user.id, exchange=exch, api_key_encrypted=encrypt_value("k"), api_secret_encrypted=encrypt_value("s"), is_active=True)
                session.add(acct)
                session.flush()
                accounts.append(acct)

            # Create a Solana wallet
            w = BlockchainWallet(user_id=user.id, address="SoMeFAkEAddress", network="solana", wallet_type="phantom", is_active=True)
            session.add(w)
            session.flush()

        # Always attempt to instantiate real connectors. Fail early if credentials missing.
        manager = ConnectorManager()

        # Binance
        bin_key = os.getenv('BINANCE_API_KEY')
        bin_secret = os.getenv('BINANCE_API_SECRET')
        if not bin_key or not bin_secret:
            pytest.skip("BINANCE_API_KEY and BINANCE_API_SECRET not set; skipping integration against real Binance connector")
        try:
            from src.api.connectors.exchanges.binance_connector import BinanceConnector
            manager.register_exchange('binance', BinanceConnector(bin_key, bin_secret))
        except Exception as e:
            pytest.fail(f"Could not initialize BinanceConnector: {e}")

        # Coinbase
        cb_key = os.getenv('COINBASE_API_KEY')
        cb_secret = os.getenv('COINBASE_API_SECRET')
        cb_pass = os.getenv('COINBASE_API_PASSPHRASE') or os.getenv('COINBASE_API_PASSPHRASE_ENV')
        if not cb_key or not cb_secret or not cb_pass:
            pytest.skip("COINBASE API credentials not set; skipping integration against real Coinbase connector")
        try:
            from src.api.connectors.exchanges.coinbase_connector import CoinbaseConnector
            manager.register_exchange('coinbase', CoinbaseConnector(cb_key, cb_secret, cb_pass))
        except Exception as e:
            pytest.fail(f"Could not initialize CoinbaseConnector: {e}")

        # Kraken
        kr_key = os.getenv('KRAKEN_API_KEY')
        kr_secret = os.getenv('KRAKEN_API_SECRET')
        if not kr_key or not kr_secret:
            pytest.skip("KRAKEN_API_KEY and KRAKEN_API_SECRET not set; skipping integration against real Kraken connector")
        try:
            from src.api.connectors.exchanges.kraken_connector import KrakenConnector
            manager.register_exchange('kraken', KrakenConnector(kr_key, kr_secret))
        except Exception as e:
            pytest.fail(f"Could not initialize KrakenConnector: {e}")

        # For each exchange account in DB, find the registered connector and call persistence methods
        with dbm.session_context() as session:
            accts = session.query(ExchangeAccount).filter_by(is_active=True).all()

        # Run exchange syncs
        for acct in accts:
            conn = manager.get_connector('exchange', acct.exchange)
            if not conn:
                continue
            # call methods and then explicitly persist via ExchangeService for our fakes
            from src.services.exchange_service import ExchangeService
            es = ExchangeService()

            balances = await conn.get_balance(persist_account_id=acct.id)
            try:
                es.persist_balances(acct.id, balances)
            except Exception:
                pass

            deposits = await conn.get_deposit_history(persist_account_id=acct.id)
            try:
                es.persist_deposits(acct.id, deposits)
            except Exception:
                pass

            withdrawals = await conn.get_withdraw_history(persist_account_id=acct.id)
            try:
                es.persist_withdrawals(acct.id, withdrawals)
            except Exception:
                pass

            trades = await conn.get_trades(persist_account_id=acct.id)
            try:
                es.persist_trades(acct.id, trades)
            except Exception:
                pass

        # Run wallet sync: instantiate fake phantom connector and persist a wallet balance
        with dbm.session_context() as session:
            wallets = session.query(BlockchainWallet).filter_by(is_active=True).all()

        for w in wallets:
            if w.wallet_type == 'phantom' and w.network == 'solana':
                conn = FakePhantomConnector(w.address, network=w.network)
                resp = await conn.get_solana_balance()
                # Persist a WalletBalance snapshot directly
                from src.database.models import WalletBalance
                with dbm.session_context() as session:
                    wb = WalletBalance(wallet_id=w.id, token='SOL', balance=str(resp.get('balance')), balance_usd=None, balance_fiat=None, timestamp=datetime.utcnow())
                    session.add(wb)

        # Finally, assert that the DB contains persisted rows
        with dbm.session_context() as session:
            # exchange balances
            from src.database.models import ExchangeBalance, ExchangeTrade, ExchangeDeposit, ExchangeWithdrawal, WalletBalance

            eb_count = session.query(ExchangeBalance).count()
            et_count = session.query(ExchangeTrade).count()
            dep_count = session.query(ExchangeDeposit).count()
            wd_count = session.query(ExchangeWithdrawal).count()
            wb_count = session.query(WalletBalance).count()

            assert eb_count > 0, "Expected at least one ExchangeBalance persisted"
            assert et_count > 0, "Expected at least one ExchangeTrade persisted"
            assert dep_count > 0, "Expected at least one ExchangeDeposit persisted"
            assert wd_count > 0, "Expected at least one ExchangeWithdrawal persisted"
            assert wb_count > 0, "Expected at least one WalletBalance persisted"

    asyncio.run(_main())
