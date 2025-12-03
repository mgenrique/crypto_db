"""
Helpers - Crypto Portfolio Tracker v3
===========================================================================

Funciones auxiliares y utilidades generales.

Incluye:
- Conversiones de unidades
- Formateo de números
- Conversión de fechas
- Cálculos comunes
- String utilities

Author: Crypto Portfolio Tracker Team
Version: 3.0.0
License: MIT
"""

import logging
from typing import Optional, List, Dict, Any
from decimal import Decimal
from datetime import datetime, timedelta
import time


logger = logging.getLogger(__name__)


class Converters:
    """Conversiones y utilidades de formato."""
    
    @staticmethod
    def wei_to_eth(wei: int) -> Decimal:
        """
        Convierte Wei a ETH.
        
        Args:
            wei: Cantidad en Wei
            
        Returns:
            Cantidad en ETH
        """
        return Decimal(wei) / Decimal(10 ** 18)
    
    @staticmethod
    def eth_to_wei(eth: Decimal) -> int:
        """
        Convierte ETH a Wei.
        
        Args:
            eth: Cantidad en ETH
            
        Returns:
            Cantidad en Wei
        """
        return int(eth * Decimal(10 ** 18))
    
    @staticmethod
    def token_to_decimal(amount: int, decimals: int) -> Decimal:
        """
        Convierte cantidad raw a decimal.
        
        Args:
            amount: Cantidad en unidades mínimas
            decimals: Número de decimales
            
        Returns:
            Cantidad en decimal
        """
        return Decimal(amount) / Decimal(10 ** decimals)
    
    @staticmethod
    def decimal_to_token(amount: Decimal, decimals: int) -> int:
        """
        Convierte decimal a cantidad raw.
        
        Args:
            amount: Cantidad en decimal
            decimals: Número de decimales
            
        Returns:
            Cantidad en unidades mínimas
        """
        return int(amount * Decimal(10 ** decimals))
    
    @staticmethod
    def format_usd(amount: Decimal, decimals: int = 2) -> str:
        """
        Formatea cantidad a USD.
        
        Args:
            amount: Cantidad
            decimals: Decimales
            
        Returns:
            String formateado (ej: $1,234.56)
        """
        try:
            formatted = f"${amount:,.{decimals}f}"
            return formatted
        except Exception as e:
            logger.error(f"Error formatting USD: {e}")
            return "$0.00"
    
    @staticmethod
    def format_percentage(value: Decimal, decimals: int = 2) -> str:
        """
        Formatea como porcentaje.
        
        Args:
            value: Valor (ej: 0.05 para 5%)
            decimals: Decimales
            
        Returns:
            String formateado (ej: 5.00%)
        """
        percentage = value * Decimal(100)
        return f"{percentage:.{decimals}f}%"
    
    @staticmethod
    def format_number(number: Decimal, decimals: int = 2) -> str:
        """
        Formatea número con separadores.
        
        Args:
            number: Número
            decimals: Decimales
            
        Returns:
            String formateado
        """
        return f"{number:,.{decimals}f}"
    
    @staticmethod
    def parse_timestamp(timestamp: int, unit: str = "seconds") -> datetime:
        """
        Convierte timestamp a datetime.
        
        Args:
            timestamp: Valor del timestamp
            unit: Unidad (seconds, milliseconds)
            
        Returns:
            Datetime object
        """
        if unit == "milliseconds":
            timestamp = timestamp / 1000
        
        return datetime.fromtimestamp(timestamp)
    
    @staticmethod
    def get_timestamp(dt: Optional[datetime] = None, unit: str = "seconds") -> int:
        """
        Obtiene timestamp de datetime.
        
        Args:
            dt: Datetime (default: ahora)
            unit: Unidad (seconds, milliseconds)
            
        Returns:
            Timestamp
        """
        if dt is None:
            dt = datetime.now()
        
        timestamp = int(dt.timestamp())
        if unit == "milliseconds":
            timestamp *= 1000
        
        return timestamp


class Calculator:
    """Cálculos comunes para crypto."""
    
    @staticmethod
    def calculate_impermanent_loss(entry_price_a: Decimal, entry_price_b: Decimal,
                                   current_price_a: Decimal, current_price_b: Decimal) -> Decimal:
        """
        Calcula pérdida impermanente (Uniswap V2).
        
        Fórmula: IL = 2 * sqrt(PriceRatio) / (1 + PriceRatio) - 1
        
        Args:
            entry_price_a: Precio inicial token A
            entry_price_b: Precio inicial token B
            current_price_a: Precio actual token A
            current_price_b: Precio actual token B
            
        Returns:
            Pérdida impermanente (ej: -0.05 para 5%)
        """
        try:
            entry_ratio = entry_price_a / entry_price_b
            current_ratio = current_price_a / current_price_b
            price_ratio = current_ratio / entry_ratio
            
            sqrt_ratio = price_ratio.sqrt()
            il = (2 * sqrt_ratio / (1 + price_ratio)) - 1
            
            return il
        except Exception as e:
            logger.error(f"Error calculating IL: {e}")
            return Decimal(0)
    
    @staticmethod
    def calculate_apy(daily_reward: Decimal, total_staked: Decimal) -> Decimal:
        """
        Calcula APY desde rewards diarios.
        
        Fórmula: APY = (1 + daily_reward/total_staked)^365 - 1
        
        Args:
            daily_reward: Reward diario
            total_staked: Total apostado
            
        Returns:
            APY (ej: 0.15 para 15%)
        """
        try:
            if total_staked <= 0:
                return Decimal(0)
            
            daily_rate = daily_reward / total_staked
            apy = (1 + daily_rate) ** 365 - 1
            
            return apy
        except Exception as e:
            logger.error(f"Error calculating APY: {e}")
            return Decimal(0)
    
    @staticmethod
    def calculate_compound_interest(principal: Decimal, rate: Decimal, 
                                    periods: int, compound_frequency: int = 365) -> Decimal:
        """
        Calcula interés compuesto.
        
        Args:
            principal: Monto inicial
            rate: Tasa de interés anual
            periods: Número de períodos (en años)
            compound_frequency: Frecuencia de compounding (default: diario)
            
        Returns:
            Monto final
        """
        try:
            rate_per_period = rate / Decimal(compound_frequency)
            final_amount = principal * (1 + rate_per_period) ** (compound_frequency * periods)
            return final_amount
        except Exception as e:
            logger.error(f"Error calculating compound interest: {e}")
            return principal


class StringUtils:
    """Utilidades para strings."""
    
    @staticmethod
    def truncate_address(address: str, prefix_chars: int = 6, suffix_chars: int = 4) -> str:
        """
        Trunca dirección Ethereum para display.
        
        Args:
            address: Dirección completa
            prefix_chars: Caracteres del inicio
            suffix_chars: Caracteres del final
            
        Returns:
            Dirección truncada (ej: 0x1234...5678)
        """
        if len(address) <= prefix_chars + suffix_chars + 3:
            return address
        
        prefix = address[:prefix_chars]
        suffix = address[-suffix_chars:]
        return f"{prefix}...{suffix}"
    
    @staticmethod
    def humanize_size(size_bytes: int) -> str:
        """
        Convierte tamaño en bytes a formato legible.
        
        Args:
            size_bytes: Tamaño en bytes
            
        Returns:
            String formateado (ej: 1.5 MB)
        """
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        
        return f"{size_bytes:.2f} TB"
    
    @staticmethod
    def pluralize(count: int, singular: str, plural: Optional[str] = None) -> str:
        """
        Pluraliza palabra según count.
        
        Args:
            count: Número
            singular: Forma singular
            plural: Forma plural (default: singular + 's')
            
        Returns:
            Palabra correcta
        """
        if plural is None:
            plural = singular + 's'
        
        return singular if count == 1 else plural


class DateUtils:
    """Utilidades para fechas."""
    
    @staticmethod
    def get_date_range(days: int) -> tuple:
        """
        Obtiene rango de fechas.
        
        Args:
            days: Número de días hacia atrás
            
        Returns:
            Tupla (start_date, end_date)
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        return (start_date, end_date)
    
    @staticmethod
    def format_relative_time(dt: datetime) -> str:
        """
        Formatea fecha relativamente.
        
        Args:
            dt: Datetime
            
        Returns:
            String (ej: "hace 2 horas")
        """
        now = datetime.now()
        diff = now - dt
        
        if diff.days > 0:
            return f"hace {diff.days} día{'s' if diff.days > 1 else ''}"
        
        hours = diff.seconds // 3600
        if hours > 0:
            return f"hace {hours} hora{'s' if hours > 1 else ''}"
        
        minutes = diff.seconds // 60
        if minutes > 0:
            return f"hace {minutes} minuto{'s' if minutes > 1 else ''}"
        
        return "ahora mismo"


__all__ = [
    "Converters",
    "Calculator",
    "StringUtils",
    "DateUtils",
]
