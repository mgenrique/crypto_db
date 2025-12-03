# src/api/connectors/base_connector.py

"""
Base Connector Class
====================

Abstract base for all exchange/blockchain connectors.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from decimal import Decimal
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class BaseConnector(ABC):
    """Abstract base connector"""
    
    def __init__(self, name: str):
        self.name = name
        self.logger = logging.getLogger(f"connector.{name}")
    
    @abstractmethod
    async def validate_connection(self) -> bool:
        """Validate connector connection"""
        pass
    
    @abstractmethod
    async def get_balance(self) -> Dict[str, Dict[str, Any]]:
        """Get account balance"""
        pass
    
    @abstractmethod
    async def get_transactions(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get transaction history"""
        pass


class ExchangeConnector(BaseConnector):
    """Base for exchange connectors (Binance, Coinbase, Kraken)"""
    
    async def get_balance(self) -> Dict[str, Dict[str, Any]]:
        """
        Returns: {
            "BTC": {"free": "0.5", "locked": "0.1", "total": "0.6"},
            "ETH": {"free": "10.0", "locked": "0.0", "total": "10.0"}
        }
        """
        pass
    
    async def get_trading_fees(self) -> Dict[str, Any]:
        """Get trading fees"""
        pass


class BlockchainConnector(BaseConnector):
    """Base for blockchain connectors (Ethereum, Bitcoin, Solana)"""
    
    def __init__(self, name: str, rpc_url: str):
        super().__init__(name)
        self.rpc_url = rpc_url
    
    async def get_balance(self, address: str) -> Decimal:
        """Get balance for address"""
        pass
    
    async def get_token_balance(self, address: str, token_address: str) -> Decimal:
        """Get ERC20/SPL token balance"""
        pass
    
    async def get_transactions(self, address: str, limit: int = 100) -> List[Dict]:
        """Get transaction history"""
        pass


class WalletConnector(BaseConnector):
    """Base for wallet connectors (Metamask, Phantom, Ledger)"""
    
    async def get_addresses(self) -> List[str]:
        """Get managed addresses"""
        pass
    
    async def sign_transaction(self, tx: Dict) -> str:
        """Sign transaction"""
        pass


class DeFiConnector(BaseConnector):
    """Base for DeFi protocol connectors"""
    
    async def get_positions(self, address: str) -> List[Dict[str, Any]]:
        """Get user positions in protocol"""
        pass
    
    async def get_pool_info(self, pool_address: str) -> Dict[str, Any]:
        """Get pool information"""
        pass
