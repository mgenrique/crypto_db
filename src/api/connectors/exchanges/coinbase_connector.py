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
    
    async def validate_connection(self) -> bool:
        """Validate Coinbase connection"""
        try:
            self.client.get_accounts()
            self.logger.info("✅ Coinbase connection validated")
            return True
        except Exception as e:
            self.logger.error(f"❌ Connection error: {str(e)}")
            return False
    
    async def get_balance(self) -> Dict[str, Dict[str, Any]]:
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
