# src/api/connectors/exchanges/binance_connector.py

"""
Binance Exchange Connector
===========================

Real-time integration with Binance API.
Completa con todas las funcionalidades.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from decimal import Decimal
from datetime import datetime, timedelta
import time

try:
    from binance.client import Client as BinanceClient
    from binance.exceptions import BinanceAPIException, BinanceOrderException
except ImportError:
    BinanceClient = None
    BinanceAPIException = None
    BinanceOrderException = None

logger = logging.getLogger(__name__)


class BinanceConnector:
    """Binance exchange connector - COMPLETO"""
    
    def __init__(self, api_key: str, api_secret: str, testnet: bool = False):
        """
        Initialize Binance connector
        
        Args:
            api_key: Binance API key
            api_secret: Binance API secret
            testnet: Use testnet (default: False)
        """
        if not BinanceClient:
            raise ImportError("python-binance not installed. pip install python-binance")
        
        self.api_key = api_key
        self.api_secret = api_secret
        self.testnet = testnet
        
        if testnet:
            self.client = BinanceClient(
                api_key=api_key,
                api_secret=api_secret,
                testnet=True
            )
        else:
            self.client = BinanceClient(api_key=api_key, api_secret=api_secret)
        
        self.logger = logging.getLogger(f"connector.binance.{api_key[:8]}")
    
    async def validate_connection(self) -> bool:
        """Validate Binance connection"""
        try:
            self.client.get_account()
            self.logger.info("✅ Binance connection validated")
            return True
        except BinanceAPIException as e:
            self.logger.error(f"❌ Binance API error: {str(e)}")
            return False
        except Exception as e:
            self.logger.error(f"❌ Connection error: {str(e)}")
            return False
    
    async def get_balance(self) -> Dict[str, Dict[str, Any]]:
        """
        Get account balances
        
        Returns:
            {
                "BTC": {"free": "0.5", "locked": "0.1", "total": "0.6"},
                "ETH": {"free": "10.0", "locked": "0.0", "total": "10.0"}
            }
        """
        try:
            account = self.client.get_account()
            balances = {}
            
            for balance in account['balances']:
                token = balance['asset']
                free = Decimal(balance['free'])
                locked = Decimal(balance['locked'])
                
                total = free + locked
                if total > 0:
                    balances[token] = {
                        "free": str(free),
                        "locked": str(locked),
                        "total": str(total)
                    }
            
            self.logger.info(f"✅ Balance fetched: {len(balances)} assets")
            return balances
        except BinanceAPIException as e:
            self.logger.error(f"❌ Error fetching balance: {str(e)}")
            raise
        except Exception as e:
            self.logger.error(f"❌ Error fetching balance: {str(e)}")
            raise
    
    async def get_asset_balance(self, asset: str) -> Optional[Dict[str, str]]:
        """Get balance for specific asset"""
        try:
            account = self.client.get_account()
            
            for balance in account['balances']:
                if balance['asset'] == asset:
                    return {
                        "free": balance['free'],
                        "locked": balance['locked'],
                        "total": str(Decimal(balance['free']) + Decimal(balance['locked']))
                    }
            
            return None
        except Exception as e:
            self.logger.error(f"❌ Error fetching {asset} balance: {str(e)}")
            return None
    
    async def get_trading_fees(self) -> Dict[str, Any]:
        """Get trading fees"""
        try:
            fees = self.client.get_trade_fee()
            
            fee_summary = {
                "maker": "0",
                "taker": "0",
                "details": []
            }
            
            if fees:
                maker_fees = []
                taker_fees = []
                
                for fee_info in fees:
                    maker_fees.append(Decimal(fee_info.get('makerCommission', 0)))
                    taker_fees.append(Decimal(fee_info.get('takerCommission', 0)))
                    
                    fee_summary["details"].append({
                        "symbol": fee_info.get('symbol'),
                        "maker": fee_info.get('makerCommission'),
                        "taker": fee_info.get('takerCommission')
                    })
                
                if maker_fees:
                    fee_summary["maker"] = str(max(maker_fees))
                if taker_fees:
                    fee_summary["taker"] = str(max(taker_fees))
            
            self.logger.info(f"✅ Trading fees fetched")
            return fee_summary
        except Exception as e:
            self.logger.error(f"❌ Error fetching fees: {str(e)}")
            raise
    
    async def get_deposit_address(self, coin: str, network: Optional[str] = None) -> Optional[Dict[str, str]]:
        """Get deposit address for coin"""
        try:
            if network:
                address = self.client.get_deposit_address(coin=coin, network=network)
            else:
                address = self.client.get_deposit_address(coin=coin)
            
            return {
                "coin": coin,
                "address": address.get('address'),
                "tag": address.get('tag'),
                "network": network or address.get('network')
            }
        except Exception as e:
            self.logger.error(f"❌ Error getting deposit address: {str(e)}")
            return None
    
    async def get_withdraw_history(self, coin: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get withdrawal history"""
        try:
            params = {"limit": limit}
            if coin:
                params["coin"] = coin
            
            history = self.client.get_withdraw_history(**params)
            
            return [
                {
                    "id": tx['id'],
                    "coin": tx['coin'],
                    "amount": tx['amount'],
                    "address": tx['address'],
                    "status": tx['status'],  # 0: pending, 1: success
                    "timestamp": datetime.fromtimestamp(tx['applyTime'] / 1000).isoformat(),
                    "txid": tx.get('txId'),
                    "network": tx.get('network')
                }
                for tx in history
            ]
        except Exception as e:
            self.logger.error(f"❌ Error fetching withdraw history: {str(e)}")
            return []
    
    async def get_deposit_history(self, coin: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get deposit history"""
        try:
            params = {"limit": limit}
            if coin:
                params["coin"] = coin
            
            history = self.client.get_deposit_history(**params)
            
            return [
                {
                    "id": tx['id'],
                    "coin": tx['coin'],
                    "amount": tx['amount'],
                    "address": tx['address'],
                    "status": tx['status'],  # 0: pending, 1: success
                    "timestamp": datetime.fromtimestamp(tx['insertTime'] / 1000).isoformat(),
                    "txid": tx.get('txId'),
                    "network": tx.get('network')
                }
                for tx in history
            ]
        except Exception as e:
            self.logger.error(f"❌ Error fetching deposit history: {str(e)}")
            return []
    
    async def get_trades(self, symbol: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get trades for symbol"""
        try:
            trades = self.client.get_my_trades(symbol=symbol, limit=limit)
            
            return [
                {
                    "id": t['id'],
                    "symbol": t['symbol'],
                    "price": t['price'],
                    "qty": t['qty'],
                    "commission": t['commission'],
                    "commissionAsset": t['commissionAsset'],
                    "is_buyer": t['isBuyer'],
                    "is_maker": t['isMaker'],
                    "timestamp": datetime.fromtimestamp(t['time'] / 1000).isoformat()
                }
                for t in trades
            ]
        except Exception as e:
            self.logger.error(f"❌ Error fetching trades: {str(e)}")
            return []
    
    async def get_all_trades(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent trades across all symbols"""
        try:
            # Get user trades (requires account read permissions)
            exchange_info = self.client.get_exchange_info()
            symbols = [s['symbol'] for s in exchange_info['symbols'] if s['status'] == 'TRADING']
            
            all_trades = []
            
            for symbol in symbols[:50]:  # Limit to first 50 to avoid rate limiting
                try:
                    trades = await self.get_trades(symbol, limit=5)
                    all_trades.extend(trades)
                    await asyncio.sleep(0.1)  # Rate limiting
                except Exception as e:
                    self.logger.warning(f"Could not fetch trades for {symbol}: {str(e)}")
                    continue
            
            # Sort by timestamp descending
            all_trades.sort(key=lambda x: x['timestamp'], reverse=True)
            
            self.logger.info(f"✅ Fetched {len(all_trades)} trades")
            return all_trades[:limit]
        except Exception as e:
            self.logger.error(f"❌ Error fetching all trades: {str(e)}")
            return []
    
    async def get_price(self, symbol: str) -> Optional[str]:
        """Get current price for symbol"""
        try:
            ticker = self.client.get_ticker(symbol=symbol)
            return ticker['lastPrice']
        except Exception as e:
            self.logger.error(f"❌ Error fetching price: {str(e)}")
            return None
    
    async def get_all_prices(self) -> Dict[str, str]:
        """Get all trading pair prices"""
        try:
            prices = self.client.get_all_tickers()
            return {p['symbol']: p['price'] for p in prices}
        except Exception as e:
            self.logger.error(f"❌ Error fetching prices: {str(e)}")
            return {}
    
    async def get_ticker(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get 24hr ticker data"""
        try:
            ticker = self.client.get_ticker(symbol=symbol)
            
            return {
                "symbol": ticker['symbol'],
                "price": ticker['lastPrice'],
                "high24h": ticker['highPrice'],
                "low24h": ticker['lowPrice'],
                "volume24h": ticker['volume'],
                "change24h": ticker['priceChangePercent']
            }
        except Exception as e:
            self.logger.error(f"❌ Error fetching ticker: {str(e)}")
            return None
    
    async def get_account_info(self) -> Dict[str, Any]:
        """Get detailed account information"""
        try:
            account = self.client.get_account()
            
            return {
                "maker_commission": account['makerCommission'],
                "taker_commission": account['takerCommission'],
                "buyer_commission": account['buyerCommission'],
                "seller_commission": account['sellerCommission'],
                "can_trade": account['canTrade'],
                "can_withdraw": account['canWithdraw'],
                "can_deposit": account['canDeposit'],
                "update_time": datetime.fromtimestamp(account['updateTime'] / 1000).isoformat(),
                "balances_count": len(account['balances'])
            }
        except Exception as e:
            self.logger.error(f"❌ Error fetching account info: {str(e)}")
            raise
