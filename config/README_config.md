# Config - Configuración de Crypto Portfolio Tracker v3

## 📋 Archivos en esta carpeta

### 1. `.env.example` (Versionar ✅)
Plantilla de variables de entorno.

**Uso:**
```bash
cp .env.example .env
vim .env  # Rellenar con tus valores
```

### 2. `config.yaml` (Versionar ✅)
Configuración principal de la aplicación.

**Secciones:**
- `database:` - Configuración de base de datos
- `logging:` - Configuración de logs
- `api:` - Configuración de FastAPI
- `exchanges:` - Configuración de exchanges
- `tax:` - Configuración de impuestos
- `price_fetcher:` - Configuración de obtención de precios
- `portfolio:` - Configuración de portfolio
- `features:` - Flags de features

### 3. `networks.yaml` (Versionar ✅)
Configuración de redes blockchain.

**Secciones:**
- `networks:` - Redes blockchain (Ethereum, Arbitrum, Base)
- `defi_protocols:` - Protocolos DeFi (Uniswap, Aave)
- `tokens:` - Tokens conocidos (ETH, USDC, DAI, etc)

### 4. `src/utils/config_loader.py` (Versionar ✅)
Clase Python que carga y valida la configuración.

**Responsabilidades:**
- Lee variables de entorno (.env)
- Lee archivos YAML
- Interpola variables (${VAR})
- Valida configuración
- Proporciona accessors seguros

---

## 🚀 Setup Rápido

### Paso 1: Copiar .env.example

```bash
cp config/.env.example .env
```

### Paso 2: Configurar variables

```bash
vim .env
```

Rellena como mínimo:
```ini
DATABASE_URL=sqlite:///./portfolio.db
ETHEREUM_RPC_URL=https://eth-mainnet.g.alchemy.com/v2/YOUR_KEY
ARBITRUM_RPC_URL=https://arb-mainnet.g.alchemy.com/v2/YOUR_KEY
BASE_RPC_URL=https://base-mainnet.g.alchemy.com/v2/YOUR_KEY
BINANCE_API_KEY=your_key
LOG_LEVEL=INFO
```

### Paso 3: Verificar instalación

```bash
python -c "from src.utils import ConfigLoader; c = ConfigLoader(); print('✅ Config loaded')"
```

---

## 📖 Uso en código

### En dependencies.py

```python
from src.utils import ConfigLoader

@lru_cache()
def get_config() -> ConfigLoader:
    return ConfigLoader()

def get_database(config = Depends(get_config)):
    db_config = config.get_database_config()
    return DatabaseManager(db_path=db_config['path'])
```

### En services

```python
from src.utils import ConfigLoader

class PortfolioService:
    def __init__(self, db):
        self.db = db
        self.config = ConfigLoader()
        
        # Acceder a redes
        ethereum = self.config.get_network("ethereum")
        rpc_url = self.config.get_network_rpc("ethereum")
        
        # Acceder a tokens
        usdc = self.config.get_token("USDC")
        usdc_addr = self.config.get_token_address("USDC", "ethereum")
        
        # Acceder a exchanges
        binance = self.config.get_exchange_config("binance")
```

---

## 🔐 Seguridad

### .gitignore

Asegúrate de que `.env` esté en `.gitignore`:

```
# Environment
.env
.env.local
.env.*.local
```

**NUNCA** commits `.env` - contiene secretos.

Sí versionar:
- `.env.example` (plantilla)
- `config.yaml`
- `networks.yaml`
- `src/utils/config_loader.py`

---

## 📊 Estructura de datos

### config.yaml Structure

```yaml
database:
  type: sqlite|postgresql
  path: ./portfolio.db
  timeout: 5

logging:
  level: INFO|DEBUG|WARNING|ERROR
  file: ./logs/app.log

api:
  version: 3.0.0
  cors:
    allow_origins: [...]
    allow_credentials: true

exchanges:
  binance:
    enabled: true
    base_url: https://api.binance.com

tax:
  default_method: FIFO|LIFO|AVERAGE_COST
  jurisdictions:
    ES: {name: España, tax_rate: 0.27}

price_fetcher:
  primary: coingecko
  fallback: [coinmarketcap, binance]

features:
  portfolio_management: true
  tax_calculation: true
```

### networks.yaml Structure

```yaml
networks:
  ethereum:
    id: 1
    name: Ethereum Mainnet
    rpc_url: ${ETHEREUM_RPC_URL}  # Interpola desde .env
    explorer: https://etherscan.io
    contracts:
      usdc: 0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48

defi_protocols:
  uniswap_v2:
    name: Uniswap V2
    factory: 0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f

tokens:
  USDC:
    symbol: USDC
    decimals: 6
    networks:
      ethereum: 0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48
```

---

## 🔍 API de ConfigLoader

```python
# Database
config.get_database_config() -> Dict

# Logging
config.get_logging_config() -> Dict

# API
config.get_api_config() -> Dict

# Exchanges
config.get_exchange_config("binance") -> Dict
config.get_exchanges_config() -> Dict

# Tax
config.get_tax_config() -> Dict

# Networks
config.get_network("ethereum") -> Dict
config.get_available_networks() -> List[str]
config.get_network_rpc("ethereum") -> str
config.get_network_explorer("ethereum") -> str

# DeFi Protocols
config.get_defi_protocol("uniswap_v2") -> Dict

# Tokens
config.get_token("USDC") -> Dict
config.get_token_address("USDC", "ethereum") -> str

# Features
config.is_feature_enabled("tax_calculation") -> bool

# Environment
config.get_env("MY_VAR", "default") -> str
```

---

## 🎯 Ejemplos prácticos

### Obtener RPC para transacciones

```python
from src.utils import ConfigLoader

config = ConfigLoader()
rpc_url = config.get_network_rpc("ethereum")

from web3 import Web3
w3 = Web3(Web3.HTTPProvider(rpc_url))
```

### Obtener dirección de contrato

```python
config = ConfigLoader()
usdc_ethereum = config.get_token_address("USDC", "ethereum")
usdc_arbitrum = config.get_token_address("USDC", "arbitrum")
```

### Verificar configuración de tax

```python
config = ConfigLoader()
tax_config = config.get_tax_config()
default_method = tax_config["default_method"]  # "FIFO"
```

### Iterar sobre redes disponibles

```python
config = ConfigLoader()
for network_name in config.get_available_networks():
    network = config.get_network(network_name)
    print(f"{network_name}: {network['explorer']}")
```

---

## ⚠️ Errores comunes

### Error: ".env file not found"

```
❌ .env file not found at .env
Copy .env.example to .env and fill with your values
```

**Solución:**
```bash
cp config/.env.example .env
vim .env
```

### Error: "Unknown network: polygon"

```
❌ Unknown network: polygon
Available: ['ethereum', 'arbitrum', 'base']
```

**Solución:**
- Usar nombre correcto: `ethereum`, `arbitrum`, `base`
- O añadir la red en `config/networks.yaml`

### Error: "No RPC URL configured for ethereum"

**Solución:**
- Verificar que `ETHEREUM_RPC_URL` está en `.env`
- Y que está interpolada en `config/networks.yaml`

---

## 🔄 Interpolación de variables

En `networks.yaml`:

```yaml
ethereum:
  rpc_url: ${ETHEREUM_RPC_URL}  # Se reemplaza con valor de .env
  name: Ethereum Mainnet
```

El `ConfigLoader` automáticamente:
1. Lee `ETHEREUM_RPC_URL` de `.env`
2. Reemplaza `${ETHEREUM_RPC_URL}` en el YAML
3. Retorna el valor interpolado

---

## 📝 Extensión: Agregar nueva red

### 1. Añadir en `config/networks.yaml`

```yaml
networks:
  polygon:
    id: 137
    name: "Polygon"
    rpc_url: ${POLYGON_RPC_URL}
    explorer: "https://polygonscan.com"
```

### 2. Añadir en `.env`

```
POLYGON_RPC_URL=https://polygon-mainnet.g.alchemy.com/v2/YOUR_KEY
```

### 3. Usar en código

```python
config = ConfigLoader()
polygon = config.get_network("polygon")
```

---

## 📚 Referencias

- YAML syntax: https://en.wikipedia.org/wiki/YAML
- Python-dotenv: https://github.com/theskumar/python-dotenv
- PyYAML: https://pyyaml.org/
