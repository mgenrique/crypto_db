# src/api/connectors/wallets/metamask_connector.py

"""
Metamask Connector
==================

Integration with Metamask wallet (via WalletConnect or direct).
"""

import logging
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


class MetamaskConnector:
    """Metamask wallet connector"""
    
    def __init__(self, wallet_address: str):
        """
        Initialize Metamask connector
        
        Args:
            wallet_address: Metamask wallet address
        """
        self.wallet_address = wallet_address
        self.logger = logging.getLogger(f"connector.metamask.{wallet_address[:10]}")
    
    async def get_addresses(self) -> List[str]:
        """Get all managed addresses"""
        # For Metamask, typically just one address per instance
        return [self.wallet_address]
    
    async def get_supported_networks(self) -> List[str]:
        """Get supported networks"""
        return ["ethereum", "arbitrum", "base", "polygon", "optimism"]


# Similar implementations for:
# - src/api/connectors/wallets/phantom_connector.py (Solana)
# - src/api/connectors/wallets/ledger_connector.py (Ledger Hardware)
