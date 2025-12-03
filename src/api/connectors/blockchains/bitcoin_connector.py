# src/api/connectors/blockchains/bitcoin_connector.py

"""
Bitcoin Connector
=================

Bitcoin blockchain monitoring via Blockchain.com or similar API.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from decimal import Decimal
import aiohttp

logger = logging.getLogger(__name__)


class BitcoinConnector:
    """Bitcoin blockchain connector"""
    
    def __init__(self):
        """Initialize Bitcoin connector"""
        self.base_url = "https://blockchain.info"
        self.logger = logging.getLogger("connector.bitcoin")
    
    async def validate_connection(self) -> bool:
        """Validate connection"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/ticker") as resp:
                    if resp.status == 200:
                        self.logger.info("✅ Bitcoin API connection validated")
                        return True
                    else:
                        self.logger.error(f"❌ Bitcoin API error: {resp.status}")
                        return False
        except Exception as e:
            self.logger.error(f"❌ Connection error: {str(e)}")
            return False
    
    async def get_balance(self, address: str) -> Dict[str, Any]:
        """Get Bitcoin address balance"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/q/addressbalance/{address}") as resp:
                    if resp.status == 200:
                        balance_satoshi = int(await resp.text())
                        balance_btc = balance_satoshi / 100_000_000
                        
                        self.logger.info(f"✅ Balance for {address[:10]}...: {balance_btc} BTC")
                        
                        return {
                            "address": address,
                            "balance_satoshi": balance_satoshi,
                            "balance_btc": str(Decimal(balance_btc))
                        }
                    else:
                        raise Exception(f"API error: {resp.status}")
        except Exception as e:
            self.logger.error(f"❌ Error fetching balance: {str(e)}")
            raise
    
    async def get_transactions(self, address: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get Bitcoin address transactions"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/address/{address}?format=json"
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        
                        transactions = []
                        
                        for tx in data.get('txs', [])[:limit]:
                            transactions.append({
                                "tx_hash": tx['hash'],
                                "time": tx['time'],
                                "input_count": len(tx.get('inputs', [])),
                                "output_count": len(tx.get('outputs', [])),
                                "fee": tx.get('fee'),
                                "size": tx.get('size')
                            })
                        
                        self.logger.info(f"✅ Fetched {len(transactions)} transactions")
                        return transactions
                    else:
                        raise Exception(f"API error: {resp.status}")
        except Exception as e:
            self.logger.error(f"❌ Error fetching transactions: {str(e)}")
            return []
