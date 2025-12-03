"""
Logger - Crypto Portfolio Tracker v3
===========================================================================

Configuración centralizada de logging.

Características:
- Logging a archivo y consola
- Múltiples niveles (DEBUG, INFO, WARNING, ERROR)
- Rotación de logs
- Formatting personalizado
- Contexto de usuario

Author: Crypto Portfolio Tracker Team
Version: 3.0.0
License: MIT
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional


class LoggerSetup:
    """Configuración centralizada de logging."""
    
    LEVELS = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL,
    }
    
    @staticmethod
    def setup(
        name: str = "crypto_tracker",
        level: str = "INFO",
        log_file: Optional[str] = None,
        max_bytes: int = 10485760,  # 10MB
        backup_count: int = 5,
    ) -> logging.Logger:
        """
        Configura logger centralizado.
        
        Args:
            name: Nombre del logger
            level: Nivel de logging
            log_file: Ruta del archivo de log
            max_bytes: Tamaño máximo antes de rotación
            backup_count: Número de backups
            
        Returns:
            Logger configurado
        """
        logger = logging.getLogger(name)
        logger.setLevel(LoggerSetup.LEVELS.get(level, logging.INFO))
        
        # Limpiar handlers existentes
        logger.handlers.clear()
        
        # Formato
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Handler console (stderr)
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setLevel(LoggerSetup.LEVELS.get(level, logging.INFO))
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # Handler archivo (si especificado)
        if log_file:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            file_handler = logging.handlers.RotatingFileHandler(
                log_path,
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding='utf-8'
            )
            file_handler.setLevel(LoggerSetup.LEVELS.get(level, logging.INFO))
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        
        return logger
    
    @staticmethod
    def get_logger(name: str) -> logging.Logger:
        """
        Obtiene logger existente.
        
        Args:
            name: Nombre del logger
            
        Returns:
            Logger
        """
        return logging.getLogger(name)


def setup_root_logger(
    level: str = "INFO",
    log_file: Optional[str] = None,
    max_bytes: int = 10485760,
    backup_count: int = 5,
) -> None:
    """
    Configura el logger raíz.
    
    Args:
        level: Nivel de logging
        log_file: Ruta del archivo de log
        max_bytes: Tamaño máximo antes de rotación
        backup_count: Número de backups
    """
    LoggerSetup.setup(
        name="crypto_tracker",
        level=level,
        log_file=log_file,
        max_bytes=max_bytes,
        backup_count=backup_count,
    )


__all__ = ["LoggerSetup", "setup_root_logger"]
