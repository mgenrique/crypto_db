# src/api/connectors/tokens/wrapped_token_detector.py

"""
Wrapped Token Detector
======================

Detects and tracks wrapped tokens (WETH, WMATIC, etc.).
Maps wrapper contracts and underlying tokens.
"""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class WrappedTokenInfo:
    """Wrapped token information"""
    wrapper_address: str
    wrapper_symbol: str
    underlying_token: str
    underlying_symbol: str
    chain: str
    wrap_ratio: float = 1.0  # Usually 1:1
    is_standard: bool = True


class WrappedTokenDetector:
    """Detects and manages wrapped tokens"""
    
    # Standard wrapped tokens
    STANDARD_WRAPPED_TOKENS = {
        "ethereum": {
            "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2": {  # WETH
                "name": "Wrapped Ether",
                "symbol": "WETH",
                "underlying": "ETH",
                "decimals": 18,
                "type": "native-wrapper"
            },
        },
        "polygon": {
            "0x9c9e5fd8bbc25984b178fdce147279496620f2d4": {  # WMATIC
                "name": "Wrapped Matic",
                "symbol": "WMATIC",
                "underlying": "MATIC",
                "decimals": 18,
                "type": "native-wrapper"
            },
            "0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619": {  # WETH
                "name": "Wrapped Ether",
                "symbol": "WETH",
                "underlying": "ETH",
                "decimals": 18,
                "type": "erc20-wrapper"
            },
        },
        "arbitrum": {
            "0x82af49447d8a07ea3a69db793ffe2755812b36a4": {  # WETH
                "name": "Wrapped Ether",
                "symbol": "WETH",
                "underlying": "ETH",
                "decimals": 18,
                "type": "native-wrapper"
            },
        },
        "base": {
            "0x4200000000000000000000000000000000000006": {  # WETH
                "name": "Wrapped Ether",
                "symbol": "WETH",
                "underlying": "ETH",
                "decimals": 18,
                "type": "native-wrapper"
            },
        },
        "optimism": {
            "0x4200000000000000000000000000000000000006": {  # WETH
                "name": "Wrapped Ether",
                "symbol": "WETH",
                "underlying": "ETH",
                "decimals": 18,
                "type": "native-wrapper"
            },
        },
        "solana": {
            # Solana uses different format
            "So11111111111111111111111111111111111111112": {  # wSOL
                "name": "Wrapped SOL",
                "symbol": "wSOL",
                "underlying": "SOL",
                "decimals": 9,
                "type": "native-wrapper"
            },
        }
    }
    
    # Wrapped token suffixes
    WRAPPED_PATTERNS = {
        "w": {"type": "wrapped", "example": "WETH"},
        "wrapped": {"type": "wrapped", "example": "WRAPPED-ETH"},
        "w-": {"type": "wrapped", "example": "W-ETH"},
    }
    
    def __init__(self):
        """Initialize wrapped token detector"""
        self.logger = logging.getLogger("detector.wrapped_tokens")
    
    async def detect_wrapped_token(self, 
                                  token_address: str,
                                  network: str) -> Optional[WrappedTokenInfo]:
        """
        Detect if token is wrapped
        
        Args:
            token_address: Token contract address
            network: Network name
        
        Returns:
            WrappedTokenInfo or None
        """
        try:
            token_address = token_address.lower()
            
            # Check in known wrapped tokens
            if network in self.STANDARD_WRAPPED_TOKENS:
                tokens = self.STANDARD_WRAPPED_TOKENS[network]
                
                if token_address in tokens:
                    data = tokens[token_address]
                    
                    self.logger.info(f"✅ Detected wrapped token: {data['symbol']} on {network}")
                    
                    return WrappedTokenInfo(
                        wrapper_address=token_address,
                        wrapper_symbol=data["symbol"],
                        underlying_token=data["underlying"],
                        underlying_symbol=data["underlying"],
                        chain=network,
                        wrap_ratio=1.0,
                        is_standard=True
                    )
            
            return None
        except Exception as e:
            self.logger.error(f"❌ Error detecting wrapped token: {str(e)}")
            return None
    
    async def detect_all_wrapped_tokens(self,
                                       balances: Dict[str, Any],
                                       network: str) -> Dict[str, WrappedTokenInfo]:
        """
        Detect all wrapped tokens in balance dict
        
        Args:
            balances: Token balances dict
            network: Network name
        
        Returns:
            Dict of detected wrapped tokens
        """
        try:
            wrapped_tokens = {}
            
            for token_address, balance_info in balances.items():
                wrapped_info = await self.detect_wrapped_token(token_address, network)
                if wrapped_info:
                    wrapped_tokens[token_address] = wrapped_info
            
            self.logger.info(f"✅ Detected {len(wrapped_tokens)} wrapped tokens")
            return wrapped_tokens
        except Exception as e:
            self.logger.error(f"❌ Error detecting wrapped tokens: {str(e)}")
            return {}
    
    async def unwrap_value(self, 
                          token_address: str,
                          amount: float,
                          network: str) -> Optional[Dict[str, float]]:
        """
        Calculate unwrapped token value
        
        Args:
            token_address: Wrapped token address
            amount: Amount of wrapped token
            network: Network name
        
        Returns:
            Unwrapped value dict or None
        """
        try:
            wrapped = await self.detect_wrapped_token(token_address, network)
            
            if wrapped:
                unwrapped_amount = amount * wrapped.wrap_ratio
                
                return {
                    "wrapped_token": wrapped.wrapper_symbol,
                    "wrapped_amount": amount,
                    "underlying_token": wrapped.underlying_symbol,
                    "underlying_amount": unwrapped_amount,
                    "ratio": wrapped.wrap_ratio
                }
            
            return None
        except Exception as e:
            self.logger.error(f"❌ Error unwrapping value: {str(e)}")
            return None
    
    async def get_wrapper_contract(self, 
                                  underlying_token: str,
                                  network: str) -> Optional[str]:
        """Get wrapper contract address for underlying token"""
        try:
            if network in self.STANDARD_WRAPPED_TOKENS:
                tokens = self.STANDARD_WRAPPED_TOKENS[network]
                
                for wrapper_addr, data in tokens.items():
                    if data["underlying"].lower() == underlying_token.lower():
                        return wrapper_addr
            
            return None
        except Exception as e:
            self.logger.error(f"❌ Error getting wrapper contract: {str(e)}")
            return None
    
    async def get_all_wrappers_for_network(self, network: str) -> List[WrappedTokenInfo]:
        """Get all wrapper tokens available on network"""
        try:
            wrappers = []
            
            if network in self.STANDARD_WRAPPED_TOKENS:
                tokens = self.STANDARD_WRAPPED_TOKENS[network]
                
                for wrapper_addr, data in tokens.items():
                    wrappers.append(WrappedTokenInfo(
                        wrapper_address=wrapper_addr,
                        wrapper_symbol=data["symbol"],
                        underlying_token=data["underlying"],
                        underlying_symbol=data["underlying"],
                        chain=network
                    ))
            
            return wrappers
        except Exception as e:
            self.logger.error(f"❌ Error getting wrappers: {str(e)}")
            return []
