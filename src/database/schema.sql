-- Schema SQL completo - Crypto Portfolio Tracker v3
-- ===========================================================================
-- Definición SQL de todas las tablas, índices y vistas
-- Ejecutar en SQLite para crear esquema completo
-- ===========================================================================

-- PRAGMA configuration
PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;

-- ============================================================================
-- TABLAS BASE (9 tablas)
-- ============================================================================

-- Tabla: wallets
-- Almacena todas las wallets monitoreadas del usuario
CREATE TABLE IF NOT EXISTS wallets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    wallet_type TEXT NOT NULL,          -- metamask, phantom, ledger, etc
    network TEXT NOT NULL,              -- ethereum, arbitrum, base, etc
    address TEXT NOT NULL UNIQUE,       -- 0x... address
    label TEXT,                         -- Nombre amigable
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_wallets_address ON wallets(address);
CREATE INDEX idx_wallets_network ON wallets(network);


-- Tabla: tokens
-- Definición de tokens
CREATE TABLE IF NOT EXISTS tokens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL UNIQUE,        -- USDC, ETH, AAVE, etc
    name TEXT NOT NULL,                 -- USD Coin, Ethereum, etc
    decimals INTEGER DEFAULT 18,        -- Decimales del token
    token_type TEXT,                    -- native, erc20, bridged, lp, atoken
    coingecko_id TEXT,                  -- ID en CoinGecko
    logo_url TEXT,                      -- URL del logo
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_tokens_symbol ON tokens(symbol);


-- Tabla: token_networks
-- Mapa de tokens por red blockchain
CREATE TABLE IF NOT EXISTS token_networks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    token_id INTEGER NOT NULL,
    network TEXT NOT NULL,              -- ethereum, arbitrum, base, etc
    contract_address TEXT UNIQUE,       -- Dirección en esa red
    decimals INTEGER DEFAULT 18,
    is_wrapped BOOLEAN DEFAULT 0,       -- ¿Es un token wrapped?
    wrapped_of TEXT,                    -- Símbolo del token original
    FOREIGN KEY(token_id) REFERENCES tokens(id),
    UNIQUE(token_id, network)
);


-- Tabla: token_aliases
-- Aliases para tokens (ej: WETH es alias de ETH)
CREATE TABLE IF NOT EXISTS token_aliases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    token_id INTEGER NOT NULL,
    alias TEXT UNIQUE,                  -- WETH, USDC.e, etc
    network TEXT,
    FOREIGN KEY(token_id) REFERENCES tokens(id)
);


-- Tabla: transactions
-- Histórico completo de transacciones
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    wallet_id INTEGER NOT NULL,
    tx_hash TEXT UNIQUE,                -- Hash de la transacción
    tx_type TEXT,                       -- swap, transfer, deposit, etc
    token_in_symbol TEXT,               -- Token enviado
    token_out_symbol TEXT,              -- Token recibido
    amount_in TEXT,                     -- Cantidad enviada
    amount_out TEXT,                    -- Cantidad recibida
    fee_paid TEXT,                      -- Fee pagada
    fee_token TEXT,                     -- Token de fee
    price_per_unit TEXT,                -- Precio al momento
    value_usd TEXT,                     -- Valor en USD
    network TEXT,                       -- Red donde ocurrió
    block_number INTEGER,               -- Bloque
    timestamp TIMESTAMP,                -- Cuando ocurrió
    status TEXT DEFAULT 'confirmed',    -- confirmed, pending, failed
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(wallet_id) REFERENCES wallets(id)
);

CREATE INDEX idx_transactions_wallet ON transactions(wallet_id);
CREATE INDEX idx_transactions_timestamp ON transactions(timestamp);


-- Tabla: balances
-- Saldos actuales por wallet y token
CREATE TABLE IF NOT EXISTS balances (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    wallet_id INTEGER NOT NULL,
    token_symbol TEXT NOT NULL,
    network TEXT NOT NULL,
    balance TEXT DEFAULT '0',           -- Cantidad en Decimal
    balance_usd TEXT DEFAULT '0',       -- Valor en USD
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(wallet_id) REFERENCES wallets(id),
    UNIQUE(wallet_id, token_symbol, network)
);

CREATE INDEX idx_balances_wallet ON balances(wallet_id);


-- Tabla: price_history
-- Histórico de precios de tokens
CREATE TABLE IF NOT EXISTS price_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    token_symbol TEXT NOT NULL,
    price_usd TEXT DEFAULT '0',
    market_cap_usd TEXT,
    volume_24h_usd TEXT,
    change_24h_percent TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_price_history_symbol ON price_history(token_symbol);
CREATE INDEX idx_price_history_timestamp ON price_history(timestamp);


-- Tabla: portfolio_snapshots
-- Snapshots periódicos del portfolio completo
CREATE TABLE IF NOT EXISTS portfolio_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    wallet_id INTEGER NOT NULL,
    total_value_usd TEXT DEFAULT '0',
    total_tokens INTEGER DEFAULT 0,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data TEXT,                          -- JSON con detalles
    FOREIGN KEY(wallet_id) REFERENCES wallets(id)
);


-- Tabla: raw_api_responses
-- Cache de respuestas de API (para auditoría y debugging)
CREATE TABLE IF NOT EXISTS raw_api_responses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    api_source TEXT NOT NULL,           -- binance, coinbase, kraken, etc
    endpoint TEXT,
    response_data TEXT,                 -- JSON crudo
    status_code INTEGER,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ttl INTEGER DEFAULT 3600            -- Time to live en segundos
);


-- ============================================================================
-- TABLAS DEFI (4 tablas nuevas en v3)
-- ============================================================================

-- Tabla: defi_pools
-- Información de pools DeFi (Uniswap, Aave, etc)
CREATE TABLE IF NOT EXISTS defi_pools (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    protocol TEXT NOT NULL,             -- uniswap_v2, uniswap_v3, aave_v3
    pool_address TEXT NOT NULL,         -- Dirección del pool/market
    network TEXT NOT NULL,              -- ethereum, arbitrum, base, etc
    token0_symbol TEXT,                 -- Token 0 (ej: USDC)
    token1_symbol TEXT,                 -- Token 1 (ej: ETH)
    token0_address TEXT,
    token1_address TEXT,
    fee_tier INTEGER,                   -- Fee en bps (Uniswap V3)
    lp_token_symbol TEXT,               -- LP token (Uniswap V2)
    tvl_usd TEXT DEFAULT '0',           -- Total Value Locked
    volume_24h_usd TEXT DEFAULT '0',    -- Volumen 24h
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(protocol, pool_address, network)
);

CREATE INDEX idx_defi_pools_protocol ON defi_pools(protocol);
CREATE INDEX idx_defi_pools_network ON defi_pools(network);


-- Tabla: uniswap_v3_positions
-- Posiciones NFT en Uniswap V3
CREATE TABLE IF NOT EXISTS uniswap_v3_positions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    token_id INTEGER NOT NULL UNIQUE,   -- NFT token ID
    pool_id INTEGER NOT NULL,
    wallet_id INTEGER NOT NULL,
    lower_tick INTEGER,                 -- Tick inferior
    upper_tick INTEGER,                 -- Tick superior
    liquidity TEXT DEFAULT '0',         -- Liquidez depositada
    token0_balance TEXT DEFAULT '0',
    token1_balance TEXT DEFAULT '0',
    uncollected_fees_token0 TEXT DEFAULT '0',
    uncollected_fees_token1 TEXT DEFAULT '0',
    in_range BOOLEAN DEFAULT 1,         -- ¿Está en rango?
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(pool_id) REFERENCES defi_pools(id),
    FOREIGN KEY(wallet_id) REFERENCES wallets(id)
);

CREATE INDEX idx_uniswap_v3_wallet ON uniswap_v3_positions(wallet_id);
CREATE INDEX idx_uniswap_v3_pool ON uniswap_v3_positions(pool_id);
CREATE INDEX idx_uniswap_v3_in_range ON uniswap_v3_positions(in_range);


-- Tabla: aave_markets
-- Markets de Aave (configuración de cada asset)
CREATE TABLE IF NOT EXISTS aave_markets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    protocol TEXT NOT NULL,             -- aave_v2, aave_v3
    market_address TEXT NOT NULL,       -- Dirección del asset
    network TEXT NOT NULL,
    asset_symbol TEXT,                  -- USDC, DAI, etc
    atoken_symbol TEXT,                 -- aUSDC, aDAI, etc
    atoken_address TEXT,
    debt_token_variable_symbol TEXT,    -- variableDebtUSDC
    debt_token_variable_address TEXT,
    debt_token_stable_symbol TEXT,      -- stableDebtUSDC (Aave V3)
    debt_token_stable_address TEXT,
    ltv TEXT DEFAULT '0.75',            -- Loan-to-Value
    liquidation_threshold TEXT DEFAULT '0.80',
    liquidation_bonus TEXT DEFAULT '0.05',
    borrow_apy TEXT DEFAULT '0',
    deposit_apy TEXT DEFAULT '0',
    total_supplied TEXT DEFAULT '0',
    total_borrowed TEXT DEFAULT '0',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(protocol, market_address, network)
);

CREATE INDEX idx_aave_markets_protocol ON aave_markets(protocol);


-- Tabla: aave_user_positions
-- Posiciones de usuarios en Aave
CREATE TABLE IF NOT EXISTS aave_user_positions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    wallet_id INTEGER NOT NULL,
    market_id INTEGER NOT NULL,
    asset_symbol TEXT,
    supplied_amount TEXT DEFAULT '0',           -- Monto suministrado
    supplied_as_collateral BOOLEAN DEFAULT 0,   -- ¿Usado como colateral?
    borrowed_variable_amount TEXT DEFAULT '0',  -- Deuda variable
    borrowed_stable_amount TEXT DEFAULT '0',    -- Deuda estable
    unclaimed_rewards TEXT DEFAULT '0',         -- Rewards no cobrados
    health_factor TEXT DEFAULT '0',             -- Health factor actual
    snapshot_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(wallet_id) REFERENCES wallets(id),
    FOREIGN KEY(market_id) REFERENCES aave_markets(id),
    UNIQUE(wallet_id, market_id, snapshot_date)
);

CREATE INDEX idx_aave_positions_wallet ON aave_user_positions(wallet_id);
CREATE INDEX idx_aave_positions_market ON aave_user_positions(market_id);


-- ============================================================================
-- VISTAS ÚTILES
-- ============================================================================

-- Vista: Portfolio resumen
CREATE VIEW IF NOT EXISTS v_portfolio_summary AS
SELECT
    w.id,
    w.address,
    w.wallet_type,
    w.network,
    SUM(CAST(b.balance_usd AS REAL)) as total_usd,
    COUNT(DISTINCT b.token_symbol) as total_tokens,
    MAX(b.last_updated) as last_updated
FROM wallets w
LEFT JOIN balances b ON w.id = b.wallet_id
GROUP BY w.id, w.address, w.wallet_type, w.network;


-- Vista: Transacciones recientes
CREATE VIEW IF NOT EXISTS v_recent_transactions AS
SELECT
    t.id,
    w.address,
    t.tx_type,
    t.token_in_symbol,
    t.token_out_symbol,
    t.value_usd,
    t.timestamp,
    t.status
FROM transactions t
JOIN wallets w ON t.wallet_id = w.id
ORDER BY t.timestamp DESC
LIMIT 100;


-- Vista: Posiciones Aave del usuario
CREATE VIEW IF NOT EXISTS v_aave_positions_detail AS
SELECT
    aut.id,
    w.address,
    am.asset_symbol,
    am.protocol,
    am.network,
    aut.supplied_amount,
    aut.supplied_as_collateral,
    aut.borrowed_variable_amount,
    aut.borrowed_stable_amount,
    aut.health_factor,
    am.ltv,
    am.liquidation_threshold,
    aut.snapshot_date
FROM aave_user_positions aut
JOIN wallets w ON aut.wallet_id = w.id
JOIN aave_markets am ON aut.market_id = am.id
ORDER BY aut.snapshot_date DESC;

-- ============================================================================
-- FIN SCHEMA
-- ============================================================================
