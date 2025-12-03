"""
Config Loader - Crypto Portfolio Tracker v3
===========================================================================

Cargador centralizado de configuración.

Responsabilidades:
- Cargar variables de entorno (.env)
- Cargar archivos YAML (config.yaml, networks.yaml)
- Interpolar variables de entorno en YAML
- Validar configuración
- Proporcionar accessors tipados

Uso:
    from src.utils import ConfigLoader
    
    config = ConfigLoader()
    db_config = config.get_database_config()
    network = config.get_network("ethereum")
    exchange = config.get_exchange_config("binance")

Author: Crypto Portfolio Tracker Team
Version: 3.0.0
License: MIT
"""

import os
import logging
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv

logger = logging.getLogger(__name__)


class ConfigLoader:
    """
    Cargador de configuración desde .env y archivos YAML.
    
    Estructura:
        NIVEL 1: .env (secretos)
        NIVEL 2: config.yaml + networks.yaml (parámetros)
        NIVEL 3: ConfigLoader (valida e interpola)
    """
    
    def __init__(self):
        """Inicializa y carga la configuración."""
        self.env_path = Path(".env")
        self.config_dir = Path("./config")
        
        # Cargar en orden
        self._load_env()
        self._load_yaml()
        self._validate()
        
        logger.info("✅ Configuration loaded successfully")
    
    # ========================================================================
    # Private Methods - Carga y validación
    # ========================================================================
    
    def _load_env(self) -> None:
        """
        Carga variables de entorno desde .env.
        
        Raises:
            FileNotFoundError: Si .env no existe
        """
        if not self.env_path.exists():
            raise FileNotFoundError(
                f"❌ .env file not found at {self.env_path}\n"
                f"Copy .env.example to .env and fill with your values"
            )
        
        load_dotenv(self.env_path)
        logger.debug(f"📄 Loaded environment variables from {self.env_path}")
    
    def _load_yaml(self) -> None:
        """
        Carga archivos YAML de configuración.
        
        Raises:
            FileNotFoundError: Si archivos YAML no existen
        """
        self.config = self._load_yaml_file("config/config.yaml")
        self.networks = self._load_yaml_file("config/networks.yaml")
        
        logger.debug("📋 Loaded YAML configuration files")
    
    def _load_yaml_file(self, path: str) -> Dict[str, Any]:
        """
        Carga y procesa un archivo YAML.
        
        Características:
        - Interpola variables de entorno ${VAR}
        - Maneja errores de parseo
        
        Args:
            path: Ruta al archivo YAML
            
        Returns:
            Diccionario con contenido del YAML
            
        Raises:
            FileNotFoundError: Si archivo no existe
            yaml.YAMLError: Si YAML es inválido
        """
        file_path = Path(path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"❌ Config file not found: {file_path}")
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                
                # Interpolar variables de entorno ${VAR}
                for key, value in os.environ.items():
                    placeholder = f"${{{key}}}"
                    if placeholder in content:
                        content = content.replace(placeholder, str(value))
                        logger.debug(f"  Interpolated ${{{key}}} in {file_path}")
                
                # Parsear YAML
                data = yaml.safe_load(content)
                
                if data is None:
                    logger.warning(f"⚠️  {file_path} is empty")
                    data = {}
            
            return data
        
        except yaml.YAMLError as e:
            raise yaml.YAMLError(f"❌ Error parsing {file_path}: {e}")
    
    def _validate(self) -> None:
        """
        Valida que la configuración tenga keys requeridas.
        
        Raises:
            ValueError: Si faltan keys obligatorias
        """
        required_keys = ["database", "logging", "api", "exchanges"]
        
        for key in required_keys:
            if key not in self.config:
                raise ValueError(
                    f"❌ Missing required config key: {key} in config.yaml"
                )
        
        logger.debug("✅ Configuration validation passed")
    
    # ========================================================================
    # Public Accessors - Métodos para acceder a configuración
    # ========================================================================
    
    def get_database_config(self) -> Dict[str, Any]:
        """
        Obtiene configuración de base de datos.
        
        Returns:
            Diccionario con config BD
            
        Example:
            config = ConfigLoader()
            db_config = config.get_database_config()
            # {'type': 'sqlite', 'path': './portfolio.db', 'timeout': 5, ...}
        """
        return self.config.get("database", {})
    
    def get_logging_config(self) -> Dict[str, Any]:
        """
        Obtiene configuración de logging.
        
        Returns:
            Diccionario con config logging
        """
        return self.config.get("logging", {})
    
    def get_api_config(self) -> Dict[str, Any]:
        """
        Obtiene configuración de API.
        
        Returns:
            Diccionario con config API
        """
        return self.config.get("api", {})
    
    def get_exchanges_config(self) -> Dict[str, Any]:
        """
        Obtiene configuración de todos los exchanges.
        
        Returns:
            Diccionario con config de exchanges
        """
        return self.config.get("exchanges", {})
    
    def get_exchange_config(self, exchange_name: str) -> Dict[str, Any]:
        """
        Obtiene configuración de un exchange específico.
        
        Args:
            exchange_name: Nombre del exchange (binance, coinbase, etc)
            
        Returns:
            Diccionario con config del exchange
            
        Raises:
            ValueError: Si exchange no existe
            
        Example:
            config = ConfigLoader()
            binance = config.get_exchange_config("binance")
            # {'enabled': True, 'base_url': 'https://api.binance.com', ...}
        """
        exchanges = self.get_exchanges_config()
        
        if exchange_name not in exchanges:
            available = list(exchanges.keys())
            raise ValueError(
                f"❌ Unknown exchange: {exchange_name}\n"
                f"Available: {available}"
            )
        
        return exchanges[exchange_name]
    
    def get_tax_config(self) -> Dict[str, Any]:
        """
        Obtiene configuración de impuestos.
        
        Returns:
            Diccionario con config de tax
        """
        return self.config.get("tax", {})
    
    def get_price_fetcher_config(self) -> Dict[str, Any]:
        """
        Obtiene configuración de price fetcher.
        
        Returns:
            Diccionario con config de price fetcher
        """
        return self.config.get("price_fetcher", {})
    
    def get_portfolio_config(self) -> Dict[str, Any]:
        """
        Obtiene configuración de portfolio.
        
        Returns:
            Diccionario con config de portfolio
        """
        return self.config.get("portfolio", {})
    
    def get_features_config(self) -> Dict[str, Any]:
        """
        Obtiene configuración de features.
        
        Returns:
            Diccionario con flags de features
        """
        return self.config.get("features", {})
    
    # ========================================================================
    # Network Accessors
    # ========================================================================
    
    def get_networks(self) -> Dict[str, Any]:
        """
        Obtiene todas las redes disponibles.
        
        Returns:
            Diccionario con todas las redes
            
        Example:
            config = ConfigLoader()
            networks = config.get_networks()
            # {'networks': {'ethereum': {...}, 'arbitrum': {...}}, ...}
        """
        return self.networks
    
    def get_available_networks(self) -> List[str]:
        """
        Obtiene lista de nombres de redes disponibles.
        
        Returns:
            Lista con nombres de redes
            
        Example:
            config = ConfigLoader()
            nets = config.get_available_networks()
            # ['ethereum', 'arbitrum', 'base']
        """
        networks_dict = self.networks.get("networks", {})
        return list(networks_dict.keys())
    
    def get_network(self, network_name: str) -> Dict[str, Any]:
        """
        Obtiene configuración de una red específica.
        
        Args:
            network_name: Nombre de la red (ethereum, arbitrum, base)
            
        Returns:
            Diccionario con config de la red
            
        Raises:
            ValueError: Si red no existe
            
        Example:
            config = ConfigLoader()
            ethereum = config.get_network("ethereum")
            # {'id': 1, 'name': 'Ethereum Mainnet', 'rpc_url': '...', ...}
        """
        networks_dict = self.networks.get("networks", {})
        
        if network_name not in networks_dict:
            available = list(networks_dict.keys())
            raise ValueError(
                f"❌ Unknown network: {network_name}\n"
                f"Available: {available}"
            )
        
        return networks_dict[network_name]
    
    def get_network_rpc(self, network_name: str) -> str:
        """
        Obtiene RPC URL de una red.
        
        Args:
            network_name: Nombre de la red
            
        Returns:
            RPC URL
            
        Raises:
            ValueError: Si red no existe o no tiene RPC
        """
        network = self.get_network(network_name)
        
        rpc_url = network.get("rpc_url")
        if not rpc_url:
            raise ValueError(f"❌ No RPC URL configured for {network_name}")
        
        return rpc_url
    
    def get_network_explorer(self, network_name: str) -> str:
        """
        Obtiene explorer URL de una red.
        
        Args:
            network_name: Nombre de la red
            
        Returns:
            Explorer URL
        """
        network = self.get_network(network_name)
        return network.get("explorer", "")
    
    # ========================================================================
    # DeFi Protocol Accessors
    # ========================================================================
    
    def get_defi_protocols(self) -> Dict[str, Any]:
        """
        Obtiene configuración de todos los protocolos DeFi.
        
        Returns:
            Diccionario con protocolos DeFi
        """
        return self.networks.get("defi_protocols", {})
    
    def get_defi_protocol(self, protocol_name: str) -> Dict[str, Any]:
        """
        Obtiene configuración de un protocolo DeFi específico.
        
        Args:
            protocol_name: Nombre del protocolo (uniswap_v2, aave, etc)
            
        Returns:
            Diccionario con config del protocolo
            
        Raises:
            ValueError: Si protocolo no existe
        """
        protocols = self.get_defi_protocols()
        
        if protocol_name not in protocols:
            available = list(protocols.keys())
            raise ValueError(
                f"❌ Unknown protocol: {protocol_name}\n"
                f"Available: {available}"
            )
        
        return protocols[protocol_name]
    
    # ========================================================================
    # Token Accessors
    # ========================================================================
    
    def get_tokens(self) -> Dict[str, Any]:
        """
        Obtiene información de todos los tokens conocidos.
        
        Returns:
            Diccionario con tokens
        """
        return self.networks.get("tokens", {})
    
    def get_token(self, token_symbol: str) -> Dict[str, Any]:
        """
        Obtiene información de un token específico.
        
        Args:
            token_symbol: Símbolo del token (ETH, USDC, etc)
            
        Returns:
            Diccionario con info del token
            
        Raises:
            ValueError: Si token no existe
        """
        tokens = self.get_tokens()
        token_symbol = token_symbol.upper()
        
        if token_symbol not in tokens:
            available = list(tokens.keys())
            raise ValueError(
                f"❌ Unknown token: {token_symbol}\n"
                f"Available: {available}"
            )
        
        return tokens[token_symbol]
    
    def get_token_address(
        self,
        token_symbol: str,
        network_name: str
    ) -> Optional[str]:
        """
        Obtiene dirección de contrato de un token en una red.
        
        Args:
            token_symbol: Símbolo del token
            network_name: Nombre de la red
            
        Returns:
            Dirección del contrato o None si no existe
        """
        try:
            token = self.get_token(token_symbol)
            networks = token.get("networks", {})
            return networks.get(network_name)
        except ValueError:
            return None
    
    # ========================================================================
    # Utility Methods
    # ========================================================================
    
    def is_feature_enabled(self, feature_name: str) -> bool:
        """
        Verifica si un feature está habilitado.
        
        Args:
            feature_name: Nombre del feature
            
        Returns:
            True si está habilitado, False en otro caso
        """
        features = self.get_features_config()
        return features.get(feature_name, False)
    
    def get_env(self, key: str, default: str = "") -> str:
        """
        Obtiene variable de entorno.
        
        Args:
            key: Nombre de la variable
            default: Valor por defecto
            
        Returns:
            Valor de la variable
        """
        return os.getenv(key, default)
    
    def __repr__(self) -> str:
        """Representación en string."""
        return (
            f"<ConfigLoader "
            f"networks={len(self.get_available_networks())} "
            f"exchanges={len(self.get_exchanges_config())} "
            f"tokens={len(self.get_tokens())}>"
        )


__all__ = ["ConfigLoader"]
