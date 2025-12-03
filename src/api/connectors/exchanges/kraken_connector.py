# src/api/connectors/exchanges/kraken_connector.py

"""
Kraken Exchange Connector
==========================

Real-time integration with Kraken API.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from decimal import Decimal
import time
from datetime import datetime

try:
    import krakenex
except ImportError:
    krakenex = None
from src.services.exchange_service import ExchangeService

logger = logging.getLogger(__name__)


class KrakenConnector:
    """Kraken exchange connector"""
    
    def __init__(self, api_key: str, api_secret: str):
        """
        Initialize Kraken connector
        
        Args:
            api_key: API key
            api_secret: API secret
        """
        if not krakenex:
            raise ImportError("krakenex library not installed. pip install krakenex")
        
        self.api_key = api_key
        self.api_secret = api_secret
        self.client = krakenex.API(key=api_key, secret=api_secret)
        self.logger = logging.getLogger(f"connector.kraken.{api_key[:8]}")
        try:
            self._exchange_service = ExchangeService()
        except Exception:
            self._exchange_service = None
    
    async def validate_connection(self) -> bool:
        """Validate Kraken connection"""
        try:
            result = self.client.query_private('Balance')
            if result:  # Check for errors
                self.logger.error(f"❌ Kraken error: {result}")
                return False
            
            self.logger.info("✅ Kraken connection validated")
            return True
        except Exception as e:
            self.logger.error(f"❌ Connection error: {str(e)}")
            return False
    
    async def get_balance(self, persist_account_id: Optional[int] = None) -> Dict[str, Dict[str, Any]]:
        """
        Get account balances
        
        Returns: {
            "BTC": {"balance": "0.5"},
            "ETH": {"balance": "10.0"}
        }
        """
        try:
            result = self.client.query_private('Balance')
            
            if result:
                raise Exception(f"Kraken error: {result}")
            
            balances = {}
            
            for asset, balance in result.items():
                # Kraken uses prefixes like 'X' for crypto, 'Z' for fiat
                clean_asset = asset.lstrip('XZ')
                balance_value = Decimal(balance)
                
                if balance_value > 0:
                    balances[clean_asset] = {
                        "balance": str(balance_value)
                    }
            
            self.logger.info(f"✅ Balance fetched: {len(balances)} assets")
            if persist_account_id and self._exchange_service:
                try:
                    normalized = {}
                    for asset, data in balances.items():
                        # Kraken returns {'BTC': {'balance': '1.0'}}
                        normalized[asset] = {
                            "free": data.get("balance"),
                            "locked": "0",
                            "total": data.get("balance"),
                        }
                    self._exchange_service.persist_balances(persist_account_id, normalized)
                except Exception as e:
                    self.logger.warning(f"Could not persist balances: {e}")

            return balances
        except Exception as e:
            self.logger.error(f"❌ Error fetching balance: {str(e)}")
            raise
    
    async def get_transactions(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get ledger entries"""
        try:
            result = self.client.query_private('QueryLedgers', {'trades': True})
            
            if result:
                raise Exception(f"Kraken error: {result}")
            
            transactions = []
            
            for ledger_id, entry in result.items():
                transactions.append({
                    "id": ledger_id,
                    "type": entry.get('type'),
                    "asset": entry.get('asset'),
                    "amount": entry.get('amount'),
                    "fee": entry.get('fee'),
                    "balance": entry.get('balance'),
                    "timestamp": datetime.fromtimestamp(entry.get('time')).isoformat()
                })
            
            # Sort by timestamp descending
            transactions.sort(key=lambda x: x['timestamp'], reverse=True)
            
            self.logger.info(f"✅ Fetched {len(transactions[:limit])} transactions")
            return transactions[:limit]
        except Exception as e:
            self.logger.error(f"❌ Error fetching transactions: {str(e)}")
            return []
    
    async def get_trades(self, persist_account_id: Optional[int] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get trading history"""
        try:
            result = self.client.query_private('TradesHistory')
            
            if result:
                raise Exception(f"Kraken error: {result}")
            
            trades = []

            for trade_id, trade in result.items():
                ts = None
                try:
                    ts = datetime.fromtimestamp(trade.get('time')).isoformat()
                except Exception:
                    ts = None

                trades.append({
                    "id": trade_id,
                    "symbol": trade.get('pair'),
                    "type": trade.get('type'),
                    "ordertype": trade.get('ordertype'),
                    "price": trade.get('price'),
                    "cost": trade.get('cost'),
                    "fee": trade.get('fee'),
                    "qty": trade.get('vol'),
                    "timestamp": ts
                })
            # Attempt to expose fiat-valued fields when pair is fiat-quoted (eg XBTUSD)
            fiat_identifiers = ['USD', 'EUR', 'GBP']
            for tr in trades:
                pair = tr.get('symbol') or ''
                for f in fiat_identifiers:
                    if f in pair:
                        # Kraken 'price' and 'cost' are in quote asset; expose as fiat when quote is fiat
                        try:
                            if tr.get('price'):
                                tr['price_fiat'] = tr.get('price')
                                tr['price_fiat_currency'] = f
                        except Exception:
                            pass
                        break

            trades.sort(key=lambda x: x.get('timestamp') or '', reverse=True)

            self.logger.info(f"✅ Fetched {len(trades[:limit])} trades")

            # Persist if requested
            if persist_account_id and hasattr(self, '_exchange_service') and self._exchange_service:
                try:
                    # note: pass a copy of the list
                    self._exchange_service.persist_trades(persist_account_id, trades[:limit])
                except Exception:
                    # persistence shouldn't break retrieval
                    self.logger.debug("Could not persist kraken trades (no account id or error)")

            return trades[:limit]
        except Exception as e:
            self.logger.error(f"❌ Error fetching trades: {str(e)}")
            return []

    async def get_deposit_history(self, persist_account_id: Optional[int] = None, limit: int = 200) -> List[Dict[str, Any]]:
        """Fetch deposit ledger entries and optionally persist them."""
        try:
            entries = await self.get_transactions(limit=limit)
            deposits = []
            withdrawals = []

            for e in entries:
                ttype = (e.get('type') or '').lower()
                if 'deposit' in ttype:
                    deposits.append({
                        "id": e.get('id'),
                        "coin": e.get('asset') or e.get('asset'),
                        "amount": e.get('amount'),
                        "address": None,
                        "txid": None,
                        "network": None,
                        "status": None,
                        "timestamp": e.get('timestamp') or e.get('time')
                    })
                elif 'withdraw' in ttype or 'withdrawal' in ttype:
                    withdrawals.append({
                        "id": e.get('id'),
                        "coin": e.get('asset') or e.get('asset'),
                        "amount": e.get('amount'),
                        "address": None,
                        "txid": None,
                        "network": None,
                        "status": None,
                        "timestamp": e.get('timestamp') or e.get('time')
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
