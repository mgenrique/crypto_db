# src/api/connectors/exchanges/coinbase_connector.py

"""
Coinbase Exchange Connector
============================

Real-time integration with Coinbase API.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from decimal import Decimal
from datetime import datetime, timedelta

try:
    from coinbase.client import Client
except ImportError:
    Client = None
from src.services.exchange_service import ExchangeService

logger = logging.getLogger(__name__)


class CoinbaseConnector:
    """Coinbase exchange connector"""
    
    def __init__(self, api_key: str, api_secret: str, passphrase: str):
        """
        Initialize Coinbase connector
        
        Args:
            api_key: API key
            api_secret: API secret
            passphrase: API passphrase
        """
        if not Client:
            raise ImportError("coinbase library not installed. pip install coinbase")
        
        self.api_key = api_key
        self.api_secret = api_secret
        self.passphrase = passphrase
        self.client = Client(api_key, api_secret, passphrase)
        self.logger = logging.getLogger(f"connector.coinbase.{api_key[:8]}")
        try:
            self._exchange_service = ExchangeService()
        except Exception:
            self._exchange_service = None
    
    async def validate_connection(self) -> bool:
        """Validate Coinbase connection"""
        try:
            self.client.get_accounts()
            self.logger.info("✅ Coinbase connection validated")
            return True
        except Exception as e:
            self.logger.error(f"❌ Connection error: {str(e)}")
            return False
    
    async def get_balance(self, persist_account_id: Optional[int] = None) -> Dict[str, Dict[str, Any]]:
        """
        Get account balances
        
        Returns:
            {
                "BTC": {"balance": "0.5", "hold": "0.1", "total": "0.6"},
                "ETH": {"balance": "10.0", "hold": "0.0", "total": "10.0"}
            }
        """
        try:
            accounts = self.client.get_accounts()
            balances = {}
            
            for account in accounts:
                currency = account['currency']
                balance = Decimal(account['balance'])
                hold = Decimal(account['hold'])
                
                if balance > 0 or hold > 0:
                    balances[currency] = {
                        "balance": str(balance),
                        "hold": str(hold),
                        "total": str(balance + hold)
                    }
            
            self.logger.info(f"✅ Balance fetched: {len(balances)} assets")
            if persist_account_id and self._exchange_service:
                try:
                    # normalize to same shape as ExchangeService expects
                    normalized = {}
                    for cur, data in balances.items():
                        normalized[cur] = {
                            "free": data.get("balance"),
                            "locked": data.get("hold") or "0",
                            "total": data.get("total") or data.get("balance"),
                        }
                    self._exchange_service.persist_balances(persist_account_id, normalized)
                except Exception as e:
                    self.logger.warning(f"Could not persist balances: {e}")

            return balances
        except Exception as e:
            self.logger.error(f"❌ Error fetching balance: {str(e)}")
            raise
    
    async def get_transactions(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get transaction history"""
        try:
            accounts = self.client.get_accounts()
            transactions = []
            
            for account in accounts:
                if account['balance'] == '0' and account['hold'] == '0':
                    continue
                
                ledger = self.client.get_account_ledger(account['id'])
                
                for entry in ledger[:limit]:
                    transactions.append({
                        "id": entry.get('id'),
                        "type": entry.get('type'),
                        "amount": entry.get('amount'),
                        "currency": entry.get('currency'),
                        "created_at": entry.get('created_at'),
                        "details": entry.get('details', {})
                    })
            
            self.logger.info(f"✅ Fetched {len(transactions)} transactions")
            return sorted(transactions, key=lambda x: x['created_at'], reverse=True)
        except Exception as e:
            self.logger.error(f"❌ Error fetching transactions: {str(e)}")
            return []
    
    async def get_fills(self, product_id: Optional[str] = None, limit: int = 100) -> List[Dict]:
        """Get trading fills"""
        try:
            fills = self.client.get_fills(product_id=product_id)
            
            return [
                {
                    "id": f['id'],
                    "order_id": f['order_id'],
                    "trade_id": f['trade_id'],
                    "product_id": f['product_id'],
                    "side": f['side'],
                    "price": f['price'],
                    "size": f['size'],
                    "fee": f['fee'],
                    "created_at": f['created_at']
                }
                for f in fills[:limit]
            ]
        except Exception as e:
            self.logger.error(f"❌ Error fetching fills: {str(e)}")
            return []

    async def get_trades(self, persist_account_id: Optional[int] = None, product_id: Optional[str] = None, limit: int = 100) -> List[Dict]:
        """Fetch recent trades/fills and optionally persist them."""
        try:
            fills = await self.get_fills(product_id=product_id, limit=limit)

            # Normalize to ExchangeService expectations
            trades = []
            for f in fills:
                try:
                    ts = f.get('created_at')
                except Exception:
                    ts = None

                trades.append({
                    "id": f.get('id'),
                    "symbol": f.get('product_id'),
                    "price": f.get('price'),
                    "qty": f.get('size'),
                    "commission": f.get('fee'),
                    "commissionAsset": None,
                    "is_buyer": True if f.get('side') == 'buy' else False,
                    "is_maker": None,
                    "timestamp": ts
                })

            if persist_account_id and self._exchange_service:
                try:
                    self._exchange_service.persist_trades(persist_account_id, trades)
                except Exception as e:
                    self.logger.warning(f"Could not persist trades: {e}")

            return trades
        except Exception as e:
            self.logger.error(f"❌ Error fetching trades: {str(e)}")
            return []

    async def get_deposit_history(self, persist_account_id: Optional[int] = None, limit: int = 200) -> List[Dict]:
        """Fetch deposit/withdrawal ledger entries and optionally persist as deposits."""
        try:
            entries = await self.get_transactions(limit=limit)
            deposits = []
            withdrawals = []

            for e in entries:
                ttype = (e.get('type') or '').lower()
                details = e.get('details') or {}
                # Heuristic: Coinbase ledger 'type' or details might indicate deposit/withdrawal
                if 'deposit' in ttype or details.get('type') == 'deposit':
                    deposits.append({
                        "id": e.get('id'),
                        "coin": e.get('currency') or details.get('currency'),
                        "amount": e.get('amount'),
                        "address": details.get('crypto_address') or details.get('address'),
                        "txid": details.get('transaction_hash') or details.get('hash'),
                        "network": details.get('network'),
                        "status": details.get('status') or 'unknown',
                        "timestamp": e.get('created_at')
                    })
                elif 'withdraw' in ttype or details.get('type') == 'withdrawal':
                    withdrawals.append({
                        "id": e.get('id'),
                        "coin": e.get('currency') or details.get('currency'),
                        "amount": e.get('amount'),
                        "address": details.get('crypto_address') or details.get('address'),
                        "txid": details.get('transaction_hash') or details.get('hash'),
                        "network": details.get('network'),
                        "status": details.get('status') or 'unknown',
                        "timestamp": e.get('created_at')
                    })

            if persist_account_id and self._exchange_service:
                try:
                    if deposits:
                        self._exchange_service.persist_deposits(persist_account_id, deposits)
                except Exception as e:
                    self.logger.warning(f"Could not persist deposits: {e}")
                try:
                    if withdrawals:
                        self._exchange_service.persist_withdrawals(persist_account_id, withdrawals)
                except Exception as e:
                    self.logger.warning(f"Could not persist withdrawals: {e}")

            return deposits, withdrawals
        except Exception as e:
            self.logger.error(f"❌ Error fetching deposit history: {str(e)}")
            return [], []
