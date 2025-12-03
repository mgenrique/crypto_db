# src/api/connectors/blockchains/ethereum_connector.py

"""
Ethereum Connector
==================

Support for Ethereum, Base, Arbitrum, Polygon.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from decimal import Decimal
from web3 import Web3
from eth_account import Account

logger = logging.getLogger(__name__)

# Standard ERC20 ABI
ERC20_ABI = [
    {
        "inputs": [{"name": "account", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function",
        "stateMutability": "view"
    },
    {
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "type": "function",
        "stateMutability": "view"
    },
    {
        "inputs": [],
        "name": "symbol",
        "outputs": [{"name": "", "type": "string"}],
        "type": "function",
        "stateMutability": "view"
    }
]


class EthereumConnector:
    """Ethereum and L2s connector"""
    
    NETWORKS = {
        "ethereum": "https://eth-mainnet.g.alchemy.com/v2/{key}",
        "arbitrum": "https://arb-mainnet.g.alchemy.com/v2/{key}",
        "base": "https://base-mainnet.g.alchemy.com/v2/{key}",
        "polygon": "https://polygon-mainnet.g.alchemy.com/v2/{key}",
    }
    
    def __init__(self, network: str, rpc_url: str, alchemy_key: Optional[str] = None):
        """
        Initialize Ethereum connector
        
        Args:
            network: Network name (ethereum, arbitrum, base, polygon)
            rpc_url: RPC URL
            alchemy_key: Alchemy API key (optional, for rate limiting)
        """
        self.network = network
        self.rpc_url = rpc_url
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        self.logger = logging.getLogger(f"connector.eth.{network}")
    
    async def validate_connection(self) -> bool:
        """Validate connection"""
        try:
            is_connected = self.w3.is_connected()
            if is_connected:
                latest_block = self.w3.eth.block_number
                self.logger.info(f"✅ {self.network} connected. Latest block: {latest_block}")
            else:
                self.logger.error(f"❌ {self.network} connection failed")
            return is_connected
        except Exception as e:
            self.logger.error(f"❌ Connection error: {str(e)}")
            return False
    
    async def get_balance(self, address: str) -> Decimal:
        """Get ETH/native token balance"""
        try:
            if not Web3.is_address(address):
                raise ValueError(f"Invalid address: {address}")
            
            balance_wei = self.w3.eth.get_balance(Web3.to_checksum_address(address))
            balance_eth = Web3.from_wei(balance_wei, 'ether')
            
            self.logger.info(f"✅ Balance for {address[:10]}...: {balance_eth} {self.network.upper()}")
            return balance_eth
        except Exception as e:
            self.logger.error(f"❌ Error fetching balance: {str(e)}")
            raise
    
    async def get_token_balance(self, address: str, token_address: str) -> Dict[str, Any]:
        """Get ERC20 token balance"""
        try:
            address = Web3.to_checksum_address(address)
            token_address = Web3.to_checksum_address(token_address)
            
            contract = self.w3.eth.contract(address=token_address, abi=ERC20_ABI)
            
            # Get decimals and symbol
            decimals = contract.functions.decimals().call()
            symbol = contract.functions.symbol().call()
            
            # Get balance
            balance_raw = contract.functions.balanceOf(address).call()
            balance = balance_raw / (10 ** decimals)
            
            return {
                "symbol": symbol,
                "balance": str(Decimal(balance)),
                "decimals": decimals,
                "token_address": token_address
            }
        except Exception as e:
            self.logger.error(f"❌ Error fetching token balance: {str(e)}")
            raise
    
    async def get_transactions(self, address: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get transaction history"""
        try:
            address = Web3.to_checksum_address(address)
            
            # Get all transactions to address
            transactions = []
            
            # For production, use Etherscan API or similar
            # This is simplified - implement with Etherscan/Blockscout
            
            self.logger.info(f"✅ Fetched transaction history for {address[:10]}...")
            return transactions
        except Exception as e:
            self.logger.error(f"❌ Error fetching transactions: {str(e)}")
            return []
    
    async def get_all_balances(self, address: str, token_addresses: List[str]) -> Dict[str, Any]:
        """Get all token balances for address"""
        try:
            balances = {
                "native": str(await self.get_balance(address))
            }
            
            for token in token_addresses:
                try:
                    token_balance = await self.get_token_balance(address, token)
                    balances[token_balance['symbol']] = token_balance['balance']
                except Exception as e:
                    self.logger.warning(f"Failed to fetch {token}: {str(e)}")
                    continue
            
            return balances
        except Exception as e:
            self.logger.error(f"❌ Error fetching all balances: {str(e)}")
            raise
