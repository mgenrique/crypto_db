# src/api/connectors/oracles/coingecko_connector.py

"""
CoinGecko Price Oracle
======================

Real-time price data and market data from CoinGecko.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from decimal import Decimal
import aiohttp

logger = logging.getLogger(__name__)


class CoinGeckoOracle:
    """CoinGecko price oracle"""
    
    def __init__(self):
        """Initialize CoinGecko oracle"""
        self.base_url = "https://api.coingecko.com/api/v3"
        self.logger = logging.getLogger("oracle.coingecko")
        self.cache = {}
        self.cache_ttl = 300  # 5 minutes
    
    async def get_price(self, token_id: str, vs_currency: str = "usd") -> Optional[Decimal]:
        """Get token price"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/simple/price",
                    params={
                        "ids": token_id,
                        "vs_currencies": vs_currency,
                        "include_market_cap": "true",
                        "include_24hr_vol": "true"
                    }
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        price = data.get(token_id, {}).get(vs_currency)
                        
                        if price:
                            self.logger.info(f"✅ {token_id.upper()}: ${price}")
                            return Decimal(str(price))
                        else:
                            raise Exception(f"Price not found for {token_id}")
                    else:
                        raise Exception(f"API error: {resp.status}")
        except Exception as e:
            self.logger.error(f"❌ Error fetching price: {str(e)}")
            return None
    
    async def get_prices_batch(self, token_ids: List[str], vs_currency: str = "usd") -> Dict[str, Decimal]:
        """Get multiple token prices"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/simple/price",
                    params={
                        "ids": ",".join(token_ids),
                        "vs_currencies": vs_currency
                    }
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        
                        prices = {
                            token_id: Decimal(str(data[token_id][vs_currency]))
                            for token_id in token_ids
                            if token_id in data
                        }
                        
                        self.logger.info(f"✅ Fetched {len(prices)} prices")
                        return prices
                    else:
                        raise Exception(f"API error: {resp.status}")
        except Exception as e:
            self.logger.error(f"❌ Error fetching prices: {str(e)}")
            return {}
    
    async def get_market_cap(self, token_id: str) -> Optional[Dict[str, Any]]:
        """Get market cap data"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/simple/price",
                    params={
                        "ids": token_id,
                        "vs_currencies": "usd",
                        "include_market_cap": "true",
                        "include_24hr_vol": "true",
                        "include_24hr_change": "true"
                    }
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data.get(token_id)
                    else:
                        raise Exception(f"API error: {resp.status}")
        except Exception as e:
            self.logger.error(f"❌ Error fetching market data: {str(e)}")
            return None
