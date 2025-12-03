# src/api/connectors/manager.py

"""
Connector Manager
=================

Orchestrates all connector instances.
"""

import logging
from typing import Dict, List, Optional, Any
from enum import Enum
from src.api.connectors.tokens.bridged_token_detector import BridgedTokenDetector
from src.api.connectors.tokens.wrapped_token_detector import WrappedTokenDetector

logger = logging.getLogger(__name__)


class ConnectorType(str, Enum):
    """Connector types"""
    EXCHANGE = "exchange"
    BLOCKCHAIN = "blockchain"
    WALLET = "wallet"
    DEFI = "defi"
    ORACLE = "oracle"


class ConnectorManager:
    """Manages all connectors"""
    
    def __init__(self):
        """Initialize connector manager"""
        self.connectors = {}
        self.bridged_detector = BridgedTokenDetector()
        self.wrapped_detector = WrappedTokenDetector()
        self.logger = logging.getLogger("connector.manager")
    
    def register_exchange(self, name: str, connector):
        """Register exchange connector"""
        self.connectors[f"exchange:{name}"] = connector
        self.logger.info(f"✅ Registered exchange: {name}")
    
    def register_blockchain(self, name: str, connector):
        """Register blockchain connector"""
        self.connectors[f"blockchain:{name}"] = connector
        self.logger.info(f"✅ Registered blockchain: {name}")
    
    def register_wallet(self, name: str, connector):
        """Register wallet connector"""
        self.connectors[f"wallet:{name}"] = connector
        self.logger.info(f"✅ Registered wallet: {name}")
    
    def register_defi(self, name: str, connector):
        """Register DeFi connector"""
        self.connectors[f"defi:{name}"] = connector
        self.logger.info(f"✅ Registered DeFi: {name}")
    
    def get_connector(self, connector_type: str, name: str):
        """Get connector by type and name"""
        key = f"{connector_type}:{name}"
        return self.connectors.get(key)
    
    async def get_all_balances(self) -> Dict[str, Dict[str, Any]]:
        """Get all balances from all connectors"""
        all_balances = {}
        
        for key, connector in self.connectors.items():
            try:
                balances = await connector.get_balance()
                all_balances[key] = balances
            except Exception as e:
                self.logger.error(f"Error getting balance from {key}: {str(e)}")
        
        return all_balances
    
    async def analyze_tokens(self, balances: Dict[str, Any], network: str) -> Dict[str, Any]:
        """
        Analyze balances for bridged and wrapped tokens
        
        Args:
            balances: Token balances
            network: Network name
        
        Returns:
            Analysis with categorized tokens
        """
        try:
            analysis = {
                "canonical": {},
                "bridged": {},
                "wrapped": {},
                "other": balances
            }
            
            # Detect bridged tokens
            bridged = await self.bridged_detector.detect_all_bridged_tokens(balances, network)
            analysis["bridged"] = bridged
            
            # Detect wrapped tokens
            wrapped = await self.wrapped_detector.detect_all_wrapped_tokens(balances, network)
            analysis["wrapped"] = wrapped
            
            # Remove detected tokens from "other"
            for addr in list(bridged.keys()) + list(wrapped.keys()):
                analysis["other"].pop(addr, None)
            
            self.logger.info(f"✅ Token analysis complete")
            return analysis
        except Exception as e:
            self.logger.error(f"❌ Error analyzing tokens: {str(e)}")
            return {"error": str(e)}        
