# Crypto Portfolio Tracker v3

Un sistema completo de monitoreo de portfolio cryptocurrency multi-wallet, multi-blockchain con soporte avanzado para DeFi (Uniswap V2/V3, Aave V2/V3).

## 🎯 Características Principales

### ✅ Multi-Wallet & Multi-Blockchain
- **Tipos de Wallet**: MetaMask, Phantom, Ledger, Hardware wallets, Exchange
- **Blockchains**: Ethereum, Arbitrum, Base, Polygon, Optimism, Avalanche, Solana, Bitcoin
- **Conectores**: Binance, Coinbase, Kraken

### ✅ DeFi Protocols
- **Uniswap V2**: Liquidez uniforme, LP tokens
- **Uniswap V3**: Liquidez concentrada, NFT positions, fee tracking
- **Aave V2**: Préstamos básicos
- **Aave V3**: E-mode, isolation mode, optimizaciones

### ✅ Tokens Soportados
- Stablecoins (USDC, USDT, DAI)
- Tokens bridged (USDC.e, USDT.e)
- LP tokens (Uniswap V2/V3)
- aTokens y debtTokens (Aave)
- 27+ tokens base configurables

### ✅ Funcionalidades
- Monitoreo en tiempo real
- Health factor automático
- Tracking de fees no cobrados (V3)
- Portfolio consolidado multi-chain
- Histórico completo de transacciones
- Snapshots periódicos
- Logging y auditoría
- Cálculo de impuestos

## 📊 Arquitectura

### Base de Datos
- Uses SQLite by default for local development (engine configurable to PostgreSQL).
- On each SQLite connection the app enables `PRAGMA foreign_keys=ON` for referential integrity.
- Alembic is included for migrations; a lightweight baseline is stamped when starting locally.

### Estructura de Código (resumen)
```text
cli.py                # CLI entrypoints and utilities
main.py               # FastAPI app, startup/shutdown wiring
src/                  # Application package
	api/                 # Routers and connector implementations
	auth/                # Authentication and models
	database/            # SQLAlchemy models, manager, migrations
	services/            # Business logic (ExchangeService, portfolio, tax)
	utils/               # Config loader, crypto helpers, logger
tests/                 # Unit and integration tests
``` 

### Conectores Disponibles
- **Exchanges**: Binance, Coinbase, Kraken
- **Blockchain**: Web3 connector genérico
- **DeFi**: Uniswap V2/V3, Aave V2/V3
- **Precios**: CoinGecko

## 🚀 Instalación Rápida

### 1. Requisitos Previos
```bash
# Python 3.9+
python --version

# pip
pip --version
```

### 2. Clonar y Configurar
```bash
# Extraer proyecto
cd crypto_tracker_v3

# Crear entorno virtual
python -m venv venv

# Activar entorno
# En Linux/macOS:
source venv/bin/activate
# En Windows:
venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt
```

### 3. Configurar Variables de Entorno
```bash
# Copiar plantilla
cp .env.example .env

# Editar con tus credenciales
nano .env  # o usar tu editor favorito
```

### 4. Inicializar Base de Datos
```bash
# Create the DB and tables using the app utility
python -c "from src.database.manager import init_database; init_database()"

# Or run Alembic migrations (recommended for production)
alembic upgrade head
```

### 5. Verificar Instalación
```bash
# Quick import check
python -c "import src; print('IMPORT_OK')"

# Run tests
python -m pytest -q
```

## 📚 Documentación

See `config/config.yaml` for runtime configuration and `config/README_config.md` for examples.

## 💻 Uso Básico

### Inicializar Database Manager
```python
```python
from src.utils.config_loader import ConfigLoader
from src.database.manager import get_db_manager, init_database

cfg = ConfigLoader()
dbm = get_db_manager()
# Create tables (dev only)
init_database()
```

### Usar Conectores DeFi
```python
```python
# Example: instantiate a Binance connector and fetch balances
from src.api.connectors.exchanges.binance_connector import BinanceConnector

client = BinanceConnector(api_key='KEY', api_secret='SECRET')
balances = client.get_balance()
```

### Gestionar Portfolio
```python
```python
# Use services to query/persist portfolio state
from src.services.portfolio_service import PortfolioService
svc = PortfolioService()
svc.recalculate_for_user(user_id=1)
```

## 🔧 Configuración

### config.yaml
```yaml
```yaml
# See `config/config.yaml` for a full example. Relevant connector section:
connectors:
	background_sync:
		enabled: true
		interval_seconds: 300
```

### .env.example
Contiene placeholders para:
- Direcciones de wallets
- Credenciales de exchanges (Binance, Coinbase, Kraken)
- URLs de RPC
- Claves de APIs

## 📊 Scripts de Utilidad



## 🗄️ Base de Datos

### Tablas Principales
- **wallets** - Gestión de wallets
- **tokens** - Definición de tokens
- **transactions** - Histórico de transacciones
- **balances** - Saldos actuales
- **price_history** - Histórico de precios
- **defi_pools** - Pools DeFi
- **uniswap_v3_positions** - Posiciones NFT V3
- **aave_markets** - Markets de Aave
- **aave_user_positions** - Posiciones de usuarios en Aave







## 📄 Licencia

MIT License - Ver LICENSE para detalles

## 👨‍💻 Autor

Crypto Portfolio Tracker v3 - 2025

---


