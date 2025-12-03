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
- **13 tablas SQL** (9 base + 4 DeFi)
- **10+ índices** optimizados
- SQLite con soporte para PRAGMA foreign_keys
- Migraciones automáticas

### Estructura de Código
```
src/
├── database/      (modelos, gestión BD, schema)
├── api/           (conectores: exchanges, blockchain, DeFi)
├── utils/         (configuración, validación, logging)
└── services/      (portfolio, impuestos, reportes)
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
python scripts/init_database.py
```

### 5. Verificar Instalación
```bash
python -c "from src.database.db_manager import DatabaseManager; print('✅ OK')"
```

## 📚 Documentación

- **PROYECTO_COMPLETO_v3.md** - Guía exhaustiva del proyecto
- **ACTUALIZACION_3_DEFI.md** - Cambios y características DeFi
- **ARQUITECTURA_BD.md** - Diseño detallado de la base de datos
- **API_REFERENCE.md** - Referencia completa de API

## 💻 Uso Básico

### Inicializar Database Manager
```python
from src.database.db_manager import DatabaseManager

# Crear instancia
db = DatabaseManager(db_path="./data/crypto_portfolio.db")

# Conectar
db.connect()

# Inicializar (si es primera vez)
db.initialize_database()
```

### Usar Conectores DeFi
```python
from src.api.defi_connectors import DeFiConnectorFactory

# Obtener conector Uniswap V3
uv3 = DeFiConnectorFactory.get_connector("uniswap_v3", network="ethereum")

# Obtener posiciones del usuario
positions = uv3.fetch_user_positions("0xYourWalletAddress")

# Obtener conector Aave V3
aave = DeFiConnectorFactory.get_connector("aave_v3", network="ethereum")

# Obtener cuenta del usuario
account = aave.fetch_user_account("0xYourWalletAddress")
```

### Gestionar Portfolio
```python
from src.services.portfolio_service import PortfolioService

# Crear servicio
portfolio = PortfolioService(db)

# Agregar wallet
portfolio.add_wallet(wallet_type="metamask", network="ethereum", address="0x...")

# Sincronizar datos
portfolio.sync_all_wallets()

# Obtener resumen
summary = portfolio.get_portfolio_summary()
```

## 🔧 Configuración

### config.yaml
```yaml
database:
  path: ./data/crypto_portfolio.db
  timeout: 30

logging:
  level: INFO
  file: ./logs/crypto_tracker.log

networks:
  ethereum:
    chain_id: 1
    name: "Ethereum Mainnet"
    rpc_url: "https://eth-mainnet.alchemyapi.io/v2/YOUR_KEY"
```

### .env.example
Contiene placeholders para:
- Direcciones de wallets
- Credenciales de exchanges (Binance, Coinbase, Kraken)
- URLs de RPC
- Claves de APIs

## 📊 Scripts de Utilidad

- **init_database.py** - Inicializar/resetear BD
- **sync_wallets.py** - Sincronizar todas las wallets
- **fetch_prices.py** - Obtener precios actualizados
- **generate_report.py** - Generar reportes

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

## ✅ Checklist de Instalación

- [ ] Python 3.9+ instalado
- [ ] Entorno virtual creado y activado
- [ ] Dependencias instaladas: `pip install -r requirements.txt`
- [ ] .env configurado con credenciales
- [ ] BD inicializada: `python scripts/init_database.py`
- [ ] 13 tablas creadas correctamente
- [ ] Imports funcionan sin errores

## 📞 Soporte & Troubleshooting

### Error: "No module named 'src'"
```bash
# Asegúrate que estás en el directorio correcto
cd crypto_tracker_v3

# Verifica que PYTHONPATH es correcto
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Error: "Table 'defi_pools' doesn't exist"
```bash
# Reinicializar la BD
python scripts/init_database.py --reset --verbose
```

### Error: "ImportError: cannot import name 'DefiProtocol'"
- Verifica que `src/database/models.py` está actualizado
- Ejecuta `pip install -r requirements.txt` nuevamente

## 🚀 Próximos Pasos

### Fase Actual (v3.0)
- ✅ Estructura completa del proyecto
- ✅ Modelos de datos y enums DeFi
- ✅ Manager de BD con 13 tablas
- ✅ Conectores base (stubs)
- ✅ Configuración YAML

### Próximas Fases
- [ ] Implementar métodos concretos en conectores (APIs/Web3)
- [ ] Agregar más protocolos DeFi (Curve, Balancer, SushiSwap)
- [ ] Dashboard web (Streamlit/Dash)
- [ ] Automatización con scheduler
- [ ] Exportar reportes PDF
- [ ] Alertas y notificaciones

## 📈 Estadísticas del Proyecto

| Métrica | Valor |
|---------|-------|
| Líneas de Código | 7,000+ |
| Archivos Python | 24 |
| Tablas BD | 13 |
| Conectores API | 8+ |
| Blockchains | 8+ |
| Tokens | 27+ |
| Tipos de Transacción | 24+ |
| Enums | 10+ |
| Dataclasses | 20+ |

## 📄 Licencia

MIT License - Ver LICENSE para detalles

## 👨‍💻 Autor

Crypto Portfolio Tracker v3 - 2025

---

**¿Necesitas ayuda?** Consulta la documentación en `docs/` o revisa los comentarios en el código.

**¿Quieres extender?** La arquitectura está diseñada para ser modular y escalable.

**¿Encontraste un bug?** Verifica los logs en `logs/crypto_tracker.log`
