"""
Database Manager - Crypto Portfolio Tracker v3
===========================================================================

Gestor centralizado de base de datos SQLite con:
- Gestión de conexiones
- CRUD operations
- Migraciones automáticas
- Índices optimizados
- 13 tablas (9 base + 4 DeFi)

Author: Crypto Portfolio Tracker Team
Version: 3.0.0
License: MIT
"""

import sqlite3
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from contextlib import contextmanager
from datetime import datetime
from decimal import Decimal


logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Gestor centralizado de base de datos SQLite.
    
    Responsabilidades:
        - Conexión y desconexión
        - Inicialización de tablas
        - Operaciones CRUD
        - Índices y optimizaciones
        - Transacciones
    """
    
    def __init__(self, db_path: str = "./data/crypto_portfolio.db", timeout: int = 30):
        """
        Inicializa el DatabaseManager.
        
        Args:
            db_path: Ruta a la BD SQLite
            timeout: Timeout para operaciones (segundos)
        """
        self.db_path = Path(db_path)
        self.timeout = timeout
        self.connection: Optional[sqlite3.Connection] = None
        logger.info(f"DatabaseManager initialized: {self.db_path}")
    
    def connect(self) -> sqlite3.Connection:
        """
        Establece conexión con la BD.
        
        Returns:
            Conexión SQLite
        """
        if self.connection is None:
            # Crear directorio si no existe
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Conectar
            self.connection = sqlite3.connect(
                str(self.db_path),
                timeout=self.timeout,
                check_same_thread=False
            )
            
            # Configurar pragmas
            self.connection.execute("PRAGMA foreign_keys = ON")
            self.connection.execute("PRAGMA journal_mode = WAL")
            self.connection.execute("PRAGMA synchronous = NORMAL")
            
            logger.debug(f"Connected to database: {self.db_path}")
        
        return self.connection
    
    def disconnect(self) -> None:
        """Cierra la conexión con la BD."""
        if self.connection:
            self.connection.close()
            self.connection = None
            logger.debug("Disconnected from database")
    
    @contextmanager
    def get_connection(self):
        """Context manager para conexión segura."""
        conn = self.connect()
        try:
            yield conn
        finally:
            pass  # No cerrar en context manager
    
    @contextmanager
    def transaction(self):
        """Context manager para transacciones."""
        conn = self.connect()
        try:
            yield conn
            conn.commit()
            logger.debug("Transaction committed")
        except Exception as e:
            conn.rollback()
            logger.error(f"Transaction rolled back: {e}")
            raise
    
    def initialize_database(self) -> None:
        """
        Crea todas las tablas de la BD.
        
        Tablas creadas:
            - wallets (usuarios)
            - tokens (definiciones)
            - token_networks (tokens por red)
            - token_aliases (aliases de tokens)
            - transactions (histórico)
            - balances (saldos actuales)
            - price_history (precios)
            - portfolio_snapshots (snapshots)
            - raw_api_responses (cache de APIs)
            - defi_pools (pools DeFi)
            - uniswap_v3_positions (posiciones V3)
            - aave_markets (markets Aave)
            - aave_user_positions (posiciones usuario)
        """
        conn = self.connect()
        cursor = conn.cursor()
        
        try:
            # ===== TABLAS BASE =====
            
            # Tabla: wallets
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS wallets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    wallet_type TEXT NOT NULL,
                    network TEXT NOT NULL,
                    address TEXT NOT NULL UNIQUE,
                    label TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Tabla: tokens
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tokens (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL UNIQUE,
                    name TEXT NOT NULL,
                    decimals INTEGER DEFAULT 18,
                    token_type TEXT,
                    coingecko_id TEXT,
                    logo_url TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Tabla: token_networks
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS token_networks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    token_id INTEGER NOT NULL,
                    network TEXT NOT NULL,
                    contract_address TEXT UNIQUE,
                    decimals INTEGER DEFAULT 18,
                    is_wrapped BOOLEAN DEFAULT 0,
                    wrapped_of TEXT,
                    FOREIGN KEY(token_id) REFERENCES tokens(id),
                    UNIQUE(token_id, network)
                )
            """)
            
            # Tabla: token_aliases
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS token_aliases (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    token_id INTEGER NOT NULL,
                    alias TEXT UNIQUE,
                    network TEXT,
                    FOREIGN KEY(token_id) REFERENCES tokens(id)
                )
            """)
            
            # Tabla: transactions
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    wallet_id INTEGER NOT NULL,
                    tx_hash TEXT UNIQUE,
                    tx_type TEXT,
                    token_in_symbol TEXT,
                    token_out_symbol TEXT,
                    amount_in TEXT,
                    amount_out TEXT,
                    fee_paid TEXT,
                    fee_token TEXT,
                    price_per_unit TEXT,
                    value_usd TEXT,
                    network TEXT,
                    block_number INTEGER,
                    timestamp TIMESTAMP,
                    status TEXT DEFAULT 'confirmed',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(wallet_id) REFERENCES wallets(id)
                )
            """)
            
            # Tabla: balances
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS balances (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    wallet_id INTEGER NOT NULL,
                    token_symbol TEXT NOT NULL,
                    network TEXT NOT NULL,
                    balance TEXT DEFAULT '0',
                    balance_usd TEXT DEFAULT '0',
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(wallet_id) REFERENCES wallets(id),
                    UNIQUE(wallet_id, token_symbol, network)
                )
            """)
            
            # Tabla: price_history
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS price_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    token_symbol TEXT NOT NULL,
                    price_usd TEXT DEFAULT '0',
                    market_cap_usd TEXT,
                    volume_24h_usd TEXT,
                    change_24h_percent TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Tabla: portfolio_snapshots
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS portfolio_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    wallet_id INTEGER NOT NULL,
                    total_value_usd TEXT DEFAULT '0',
                    total_tokens INTEGER DEFAULT 0,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    data TEXT,
                    FOREIGN KEY(wallet_id) REFERENCES wallets(id)
                )
            """)
            
            # Tabla: raw_api_responses
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS raw_api_responses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    api_source TEXT NOT NULL,
                    endpoint TEXT,
                    response_data TEXT,
                    status_code INTEGER,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    ttl INTEGER DEFAULT 3600
                )
            """)
            
            # ===== TABLAS DEFI =====
            
            # Tabla: defi_pools
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS defi_pools (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    protocol TEXT NOT NULL,
                    pool_address TEXT NOT NULL,
                    network TEXT NOT NULL,
                    token0_symbol TEXT,
                    token1_symbol TEXT,
                    token0_address TEXT,
                    token1_address TEXT,
                    fee_tier INTEGER,
                    lp_token_symbol TEXT,
                    tvl_usd TEXT DEFAULT '0',
                    volume_24h_usd TEXT DEFAULT '0',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(protocol, pool_address, network)
                )
            """)
            
            # Tabla: uniswap_v3_positions
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS uniswap_v3_positions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    token_id INTEGER NOT NULL UNIQUE,
                    pool_id INTEGER NOT NULL,
                    wallet_id INTEGER NOT NULL,
                    lower_tick INTEGER,
                    upper_tick INTEGER,
                    liquidity TEXT DEFAULT '0',
                    token0_balance TEXT DEFAULT '0',
                    token1_balance TEXT DEFAULT '0',
                    uncollected_fees_token0 TEXT DEFAULT '0',
                    uncollected_fees_token1 TEXT DEFAULT '0',
                    in_range BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(pool_id) REFERENCES defi_pools(id),
                    FOREIGN KEY(wallet_id) REFERENCES wallets(id)
                )
            """)
            
            # Tabla: aave_markets
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS aave_markets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    protocol TEXT NOT NULL,
                    market_address TEXT NOT NULL,
                    network TEXT NOT NULL,
                    asset_symbol TEXT,
                    atoken_symbol TEXT,
                    atoken_address TEXT,
                    debt_token_variable_symbol TEXT,
                    debt_token_variable_address TEXT,
                    debt_token_stable_symbol TEXT,
                    debt_token_stable_address TEXT,
                    ltv TEXT DEFAULT '0.75',
                    liquidation_threshold TEXT DEFAULT '0.80',
                    liquidation_bonus TEXT DEFAULT '0.05',
                    borrow_apy TEXT DEFAULT '0',
                    deposit_apy TEXT DEFAULT '0',
                    total_supplied TEXT DEFAULT '0',
                    total_borrowed TEXT DEFAULT '0',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(protocol, market_address, network)
                )
            """)
            
            # Tabla: aave_user_positions
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS aave_user_positions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    wallet_id INTEGER NOT NULL,
                    market_id INTEGER NOT NULL,
                    asset_symbol TEXT,
                    supplied_amount TEXT DEFAULT '0',
                    supplied_as_collateral BOOLEAN DEFAULT 0,
                    borrowed_variable_amount TEXT DEFAULT '0',
                    borrowed_stable_amount TEXT DEFAULT '0',
                    unclaimed_rewards TEXT DEFAULT '0',
                    health_factor TEXT DEFAULT '0',
                    snapshot_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(wallet_id) REFERENCES wallets(id),
                    FOREIGN KEY(market_id) REFERENCES aave_markets(id),
                    UNIQUE(wallet_id, market_id, snapshot_date)
                )
            """)
            
            # ===== ÍNDICES OPTIMIZADOS =====
            
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_wallets_address ON wallets(address)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_wallets_network ON wallets(network)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_tokens_symbol ON tokens(symbol)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_transactions_wallet ON transactions(wallet_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_transactions_timestamp ON transactions(timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_balances_wallet ON balances(wallet_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_price_history_symbol ON price_history(token_symbol)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_price_history_timestamp ON price_history(timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_defi_pools_protocol ON defi_pools(protocol)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_defi_pools_network ON defi_pools(network)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_uniswap_v3_wallet ON uniswap_v3_positions(wallet_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_uniswap_v3_pool ON uniswap_v3_positions(pool_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_uniswap_v3_in_range ON uniswap_v3_positions(in_range)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_aave_markets_protocol ON aave_markets(protocol)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_aave_positions_wallet ON aave_user_positions(wallet_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_aave_positions_market ON aave_user_positions(market_id)")
            
            conn.commit()
            logger.info("Database initialized successfully with 13 tables and 15 indices")
            
        except sqlite3.Error as e:
            logger.error(f"Error initializing database: {e}")
            conn.rollback()
            raise
    
    def reset_database(self) -> None:
        """Borra todas las tablas y reinicializa."""
        conn = self.connect()
        cursor = conn.cursor()
        
        try:
            # Desactivar foreign keys temporalmente
            cursor.execute("PRAGMA foreign_keys = OFF")
            
            # Obtener lista de tablas
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
            """)
            tables = cursor.fetchall()
            
            # Borrar cada tabla
            for table in tables:
                cursor.execute(f"DROP TABLE IF EXISTS {table[0]}")
                logger.debug(f"Dropped table: {table[0]}")
            
            conn.commit()
            
            # Reactivar foreign keys
            cursor.execute("PRAGMA foreign_keys = ON")
            
            # Reinitialize
            self.initialize_database()
            logger.info("Database reset completed")
            
        except sqlite3.Error as e:
            logger.error(f"Error resetting database: {e}")
            conn.rollback()
            raise
    
    def execute_query(self, query: str, params: tuple = ()) -> List[Tuple]:
        """
        Ejecuta una query SELECT.
        
        Args:
            query: Query SQL
            params: Parámetros
            
        Returns:
            Lista de tuplas con resultados
        """
        conn = self.connect()
        cursor = conn.cursor()
        
        try:
            cursor.execute(query, params)
            return cursor.fetchall()
        except sqlite3.Error as e:
            logger.error(f"Error executing query: {e}")
            raise
    
    def execute_insert(self, query: str, params: tuple = ()) -> int:
        """
        Ejecuta un INSERT.
        
        Args:
            query: Query SQL
            params: Parámetros
            
        Returns:
            ID del registro insertado
        """
        conn = self.connect()
        cursor = conn.cursor()
        
        try:
            cursor.execute(query, params)
            conn.commit()
            return cursor.lastrowid
        except sqlite3.Error as e:
            logger.error(f"Error inserting data: {e}")
            conn.rollback()
            raise
    
    def execute_update(self, query: str, params: tuple = ()) -> int:
        """
        Ejecuta un UPDATE.
        
        Args:
            query: Query SQL
            params: Parámetros
            
        Returns:
            Número de filas afectadas
        """
        conn = self.connect()
        cursor = conn.cursor()
        
        try:
            cursor.execute(query, params)
            conn.commit()
            return cursor.rowcount
        except sqlite3.Error as e:
            logger.error(f"Error updating data: {e}")
            conn.rollback()
            raise
    
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()


__all__ = ["DatabaseManager"]
