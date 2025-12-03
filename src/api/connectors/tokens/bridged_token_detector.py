# src/api/connectors/tokens/bridged_token_detector.py

"""
Bridged Token Detector
======================

Detects and tracks bridged tokens (USDC.e, USDT.e, etc.).
Maps bridge addresses and confirms authenticity.
"""

import logging
from typing import Dict, List, Optional, Any
from decimal import Decimal
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class BridgeMetadata:
    """Bridged token metadata"""
    original_token: str
    original_chain: str
    bridge_address: str
    bridge_protocol: str
    canonical_address: str
    wrapped_address: str
    fee_percentage: Decimal
    is_canonical: bool = True


class BridgedTokenDetector:
    """Detects and manages bridged tokens"""
    
    # Known bridge protocols
    BRIDGE_PROTOCOLS = {
        "circle": {
            "name": "Circle Bridge (CCTP)",
            "tokens": ["USDC"],
            "chains": ["ethereum", "arbitrum", "base", "polygon", "optimism", "avalanche"],
        },
        "stargate": {
            "name": "Stargate",
            "tokens": ["USDC", "USDT"],
            "chains": ["ethereum", "arbitrum", "base", "polygon", "optimism"],
        },
        "synapse": {
            "name": "Synapse Protocol",
            "tokens": ["USDC", "USDT", "DAI"],
            "chains": ["ethereum", "arbitrum", "base", "polygon", "optimism", "avalanche"],
        },
        "celer": {
            "name": "Celer Bridge",
            "tokens": ["USDC", "USDT", "USDE"],
            "chains": ["ethereum", "arbitrum", "base", "polygon", "optimism"],
        }
    }
    
    # Common bridged token suffixes
    BRIDGED_TOKEN_PATTERNS = {
        ".e": {  # Avalanche bridge convention
            "bridge": "avalanche-bridge",
            "example": "USDC.e"
        },
        ".m": {  # Mainnet wrapped
            "bridge": "wrapped",
            "example": "WETH.m"
        },
        "ax": {  # Arbitrum bridge suffix
            "bridge": "arbitrum-bridge",
            "example": "USDAx"
        },
    }
    
    # Known bridged token addresses (Ethereum mainnet)
    KNOWN_BRIDGED_TOKENS = {
        "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48": {  # USDC
            "name": "USDC",
            "symbol": "USDC",
            "bridges": {
                "arbitrum": "0xff970a61a04b1ca14834a43f5de4533ebddb5f86",
                "base": "0x833589fcd6edb6e08f4c7c32d4f71b1566469c18",
                "polygon": "0x2791bca1f2de4661ed88a30c99a7a9449aa84174",
                "optimism": "0x7f5c764cbc14f9669b88837ca1490cca17c31607",
                "avalanche": "0xa7d8d9ef8d91e8d7d491653a35eb667f6ea97d7f",
            }
        },
        "0xdac17f958d2ee523a2206206994597c13d831ec7": {  # USDT
            "name": "USDT",
            "symbol": "USDT",
            "bridges": {
                "arbitrum": "0xfd086bc7cd5c481dcc9c85ebe478a1c0b69fcbb9",
                "base": "0xfde4c96c8593536e31f543fcb815438f505be5b5",
                "polygon": "0xc2132d05d31c914a87c6611c10748aeb04b58e8f",
                "optimism": "0x94b008aa00579c1307b0ef2c499ad98a8ce58e58",
                "avalanche": "0x9702230a8ea53601f5eb13228f642e6ad7468247",
            }
        }
    }
    
    def __init__(self):
        """Initialize bridged token detector"""
        self.logger = logging.getLogger("detector.bridged_tokens")
    
    async def detect_bridged_token(self, 
                                   token_address: str,
                                   network: str) -> Optional[BridgeMetadata]:
        """
        Detect if token is bridged and get metadata
        
        Args:
            token_address: Token contract address
            network: Network name (ethereum, arbitrum, base, etc)
        
        Returns:
            BridgeMetadata or None
        """
        try:
            # Check if token matches known bridged patterns
            token_address = token_address.lower()
            
            # Look up in known bridged tokens
            for eth_token, data in self.KNOWN_BRIDGED_TOKENS.items():
                if data["bridges"].get(network) == token_address:
                    self.logger.info(f"✅ Detected bridged token: {data['name']} on {network}")
                    
                    return BridgeMetadata(
                        original_token=data["name"],
                        original_chain="ethereum",
                        bridge_address=eth_token,
                        bridge_protocol=self._detect_bridge_protocol(token_address, network),
                        canonical_address=token_address,
                        wrapped_address=token_address,
                        fee_percentage=Decimal("0.01"),
                        is_canonical=False
                    )
            
            return None
        except Exception as e:
            self.logger.error(f"❌ Error detecting bridged token: {str(e)}")
            return None
    
    async def detect_all_bridged_tokens(self, 
                                       balances: Dict[str, Any],
                                       network: str) -> Dict[str, BridgeMetadata]:
        """
        Detect all bridged tokens in balance dict
        
        Args:
            balances: Token balances dict
            network: Network name
        
        Returns:
            Dict of detected bridged tokens
        """
        try:
            bridged_tokens = {}
            
            for token_address, balance_info in balances.items():
                metadata = await self.detect_bridged_token(token_address, network)
                if metadata:
                    bridged_tokens[token_address] = metadata
            
            self.logger.info(f"✅ Detected {len(bridged_tokens)} bridged tokens")
            return bridged_tokens
        except Exception as e:
            self.logger.error(f"❌ Error detecting bridged tokens: {str(e)}")
            return {}
    
    async def get_canonical_token(self, 
                                 token_address: str,
                                 network: str) -> Optional[Dict[str, str]]:
        """
        Get canonical (original) token information
        
        Args:
            token_address: Bridged token address
            network: Network name
        
        Returns:
            Canonical token info or None
        """
        try:
            metadata = await self.detect_bridged_token(token_address, network)
            
            if metadata:
                return {
                    "name": metadata.original_token,
                    "chain": metadata.original_chain,
                    "address": metadata.bridge_address,
                    "is_canonical": metadata.is_canonical
                }
            
            return None
        except Exception as e:
            self.logger.error(f"❌ Error getting canonical token: {str(e)}")
            return None
    
    async def get_bridge_info(self, token_symbol: str) -> Optional[Dict[str, Any]]:
        """Get bridge information for token"""
        try:
            for protocol, data in self.BRIDGE_PROTOCOLS.items():
                if token_symbol in data["tokens"]:
                    return {
                        "protocol": protocol,
                        "name": data["name"],
                        "supported_chains": data["chains"],
                        "tokens": data["tokens"]
                    }
            
            return None
        except Exception as e:
            self.logger.error(f"❌ Error getting bridge info: {str(e)}")
            return None
    
    def _detect_bridge_protocol(self, token_address: str, network: str) -> str:
        """Infer bridge protocol from token characteristics"""
        # This would use more sophisticated detection
        # For now, return generic bridge
        return "cross-chain-bridge"
