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

try:
    import krakenex
except ImportError:
    krakenex = None

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
    
    async def get_balance(self) -> Dict[str, Dict[str, Any]]:
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
    
    async def get_trades(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get trading history"""
        try:
            result = self.client.query_private('TradesHistory')
            
            if result:
                raise Exception(f"Kraken error: {result}")
            
            trades = []
            
            for trade_id, trade in result.items():
                trades.append({
                    "id": trade_id,
                    "pair": trade.get('pair'),
                    "type": trade.get('type'),
                    "ordertype": trade.get('ordertype'),
                    "price": trade.get('price'),
                    "cost": trade.get('cost'),
                    "fee": trade.get('fee'),
                    "vol": trade.get('vol'),
                    "time": datetime.fromtimestamp(trade.get('time')).isoformat()
                })
            
            trades.sort(key=lambda x: x['time'], reverse=True)
            
            self.logger.info(f"✅ Fetched {len(trades[:limit])} trades")
            return trades[:limit]
        except Exception as e:
            self.logger.error(f"❌ Error fetching trades: {str(e)}")
            return []
