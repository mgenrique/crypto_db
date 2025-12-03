"""
Utils Module - Crypto Portfolio Tracker v3
===========================================================================

Módulo de utilidades que incluye:
- ConfigLoader (configuración YAML + .env)
- Validators (validadores de blockchain)
- Logger (logging centralizado)
- Helpers (conversiones, cálculos, formateo)

Uso:
    from src.utils import ConfigLoader, Validators, Converters
    
    # Cargar configuración
    config = ConfigLoader()
    db_config = config.get_database_config()
    
    # Validar dirección
    if Validators.is_ethereum_address("0x..."):
        print("Valid address")
    
    # Convertir Wei a ETH
    eth = Converters.wei_to_eth(1000000000000000000)
"""

from .config_loader import ConfigLoader
from .validators import Validators
from .logger import LoggerSetup, setup_root_logger
from .helpers import (
    Converters,
    Calculator,
    StringUtils,
    DateUtils,
)

__all__ = [
    # Config
    "ConfigLoader",
    # Validators
    "Validators",
    # Logger
    "LoggerSetup",
    "setup_root_logger",
    # Helpers
    "Converters",
    "Calculator",
    "StringUtils",
    "DateUtils",
]
