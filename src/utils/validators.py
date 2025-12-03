"""
Validators - Crypto Portfolio Tracker v3
===========================================================================

Validadores personalizados para datos de criptomonedas.

Valida:
- Direcciones blockchain (0x...)
- Símbolos de tokens
- Montos y cantidades
- URLs
- Configuración

Author: Crypto Portfolio Tracker Team
Version: 3.0.0
License: MIT
"""

import logging
import re
from typing import Optional, List
from decimal import Decimal


logger = logging.getLogger(__name__)


class Validators:
    """Colección de validadores."""
    
    # Patrones regex
    ETH_ADDRESS_PATTERN = re.compile(r'^0x[a-fA-F0-9]{40}$')
    BTC_ADDRESS_PATTERN = re.compile(r'^[13][a-km-zA-HJ-NP-Z1-9]{25,34}$')  # P2PKH/P2SH
    SYMBOL_PATTERN = re.compile(r'^[A-Z0-9\.]{1,20}$')
    URL_PATTERN = re.compile(
        r'^https?://'
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'
        r'localhost|'
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
        r'(?::\d+)?'
        r'(?:/?|[/?]\S+)$',
        re.IGNORECASE
    )
    
    @staticmethod
    def is_ethereum_address(address: str) -> bool:
        """
        Valida dirección Ethereum.
        
        Args:
            address: Dirección a validar
            
        Returns:
            True si válida
        """
        if not address:
            return False
        
        if not Validators.ETH_ADDRESS_PATTERN.match(address):
            logger.warning(f"Invalid Ethereum address: {address}")
            return False
        
        return True
    
    @staticmethod
    def is_bitcoin_address(address: str) -> bool:
        """
        Valida dirección Bitcoin.
        
        Args:
            address: Dirección a validar
            
        Returns:
            True si válida
        """
        if not address:
            return False
        
        if not Validators.BTC_ADDRESS_PATTERN.match(address):
            logger.warning(f"Invalid Bitcoin address: {address}")
            return False
        
        return True
    
    @staticmethod
    def is_blockchain_address(address: str, blockchain: str = "ethereum") -> bool:
        """
        Valida dirección según blockchain.
        
        Args:
            address: Dirección a validar
            blockchain: Tipo de blockchain
            
        Returns:
            True si válida
        """
        if blockchain.lower() in ("ethereum", "arbitrum", "base", "polygon", "optimism", "avalanche"):
            return Validators.is_ethereum_address(address)
        elif blockchain.lower() == "bitcoin":
            return Validators.is_bitcoin_address(address)
        else:
            logger.warning(f"Unknown blockchain: {blockchain}")
            return False
    
    @staticmethod
    def is_token_symbol(symbol: str) -> bool:
        """
        Valida símbolo de token.
        
        Args:
            symbol: Símbolo a validar
            
        Returns:
            True si válido
        """
        if not symbol:
            return False
        
        if not Validators.SYMBOL_PATTERN.match(symbol):
            logger.warning(f"Invalid token symbol: {symbol}")
            return False
        
        return True
    
    @staticmethod
    def is_valid_amount(amount: any, min_value: Decimal = Decimal("0"), 
                       max_value: Optional[Decimal] = None) -> bool:
        """
        Valida monto/cantidad.
        
        Args:
            amount: Monto a validar
            min_value: Valor mínimo
            max_value: Valor máximo (opcional)
            
        Returns:
            True si válido
        """
        try:
            if isinstance(amount, str):
                amount = Decimal(amount)
            elif not isinstance(amount, Decimal):
                amount = Decimal(amount)
            
            if amount < min_value:
                logger.warning(f"Amount {amount} below minimum {min_value}")
                return False
            
            if max_value and amount > max_value:
                logger.warning(f"Amount {amount} exceeds maximum {max_value}")
                return False
            
            return True
        
        except Exception as e:
            logger.warning(f"Invalid amount: {e}")
            return False
    
    @staticmethod
    def is_valid_url(url: str) -> bool:
        """
        Valida URL.
        
        Args:
            url: URL a validar
            
        Returns:
            True si válida
        """
        if not url:
            return False
        
        if not Validators.URL_PATTERN.match(url):
            logger.warning(f"Invalid URL: {url}")
            return False
        
        return True
    
    @staticmethod
    def is_valid_email(email: str) -> bool:
        """
        Valida email.
        
        Args:
            email: Email a validar
            
        Returns:
            True si válido
        """
        if not email:
            return False
        
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, email):
            logger.warning(f"Invalid email: {email}")
            return False
        
        return True
    
    @staticmethod
    def validate_transaction_hash(tx_hash: str, blockchain: str = "ethereum") -> bool:
        """
        Valida hash de transacción.
        
        Args:
            tx_hash: Hash a validar
            blockchain: Blockchain
            
        Returns:
            True si válido
        """
        if not tx_hash:
            return False
        
        if blockchain.lower() in ("ethereum", "arbitrum", "base", "polygon", "optimism", "avalanche"):
            # EVM: 66 caracteres hex (0x + 64 hex)
            return bool(re.match(r'^0x[a-fA-F0-9]{64}$', tx_hash))
        elif blockchain.lower() == "bitcoin":
            # Bitcoin: 64 caracteres hex
            return bool(re.match(r'^[a-fA-F0-9]{64}$', tx_hash))
        
        return False
    
    @staticmethod
    def validate_wallet_label(label: str, min_length: int = 1, max_length: int = 50) -> bool:
        """
        Valida etiqueta de wallet.
        
        Args:
            label: Etiqueta
            min_length: Longitud mínima
            max_length: Longitud máxima
            
        Returns:
            True si válida
        """
        if not label:
            return False
        
        if len(label) < min_length or len(label) > max_length:
            logger.warning(f"Label length {len(label)} out of range [{min_length}, {max_length}]")
            return False
        
        # Solo alfanuméricos, espacios, guiones
        if not re.match(r'^[a-zA-Z0-9\s\-_]{' + str(min_length) + ',' + str(max_length) + '}$', label):
            logger.warning(f"Invalid label characters: {label}")
            return False
        
        return True
    
    @staticmethod
    def validate_api_key(api_key: str) -> bool:
        """
        Valida API key.
        
        Args:
            api_key: API key a validar
            
        Returns:
            True si válida (solo longitud)
        """
        if not api_key:
            return False
        
        if len(api_key) < 20:
            logger.warning("API key too short")
            return False
        
        return True


__all__ = ["Validators"]
