# Crypto Portfolio Tracker

## Descripción General

Sistema integral de gestión y seguimiento de transacciones de criptomonedas y depósitos FIAT en múltiples plataformas. Diseñado para mantener un registro unificado de operaciones, cálculos de valoración en tiempo real y conformidad fiscal española.

## Características Principales

- **Base de datos SQLite local** con estructura escalable
- **Integración con múltiples plataformas**:
  - Exchanges: Binance, Coinbase, Kraken
  - Wallets: MetaMask, Phantom, Ledger Live, Ledger Nano S Plus
  - Blockchains: Bitcoin, Ethereum, Solana, Base, Arbitrum
  - Monitoreo de precios: CoinGecko

- **Gestión unificada de tokens** con soporte para tokens en diferentes L2s
- **Cálculos de portfolio** valorados en EUR
- **Cálculo fiscal automatizado** para España (IRPF/Criptoactivos)
- **API para automatización** externa
- **Almacenamiento de datos brutos** en formato JSON
- **Gestión de configuración** mediante YAML
- **Gestión de secretos** mediante .env

## Requisitos Previos

- Python 3.12+
- Windows 10/11
- SQLite3 ODBC Driver (opcional, para acceso externo)
- pip (gestor de paquetes Python)

## Instalación

### 1. Clonar o descargar el proyecto

```bash
cd crypto_tracker
```

### 2. Crear entorno virtual

```bash
python -m venv venv
venv\Scripts\activate  # En Windows
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno

```bash
copy .env.example .env
# Editar .env con tus credenciales y API keys
```

### 5. Configurar parámetros de la aplicación

```bash
# Editar config.yaml según tus necesidades
# URLs de endpoints, ABIs, tokens soportados, etc.
```

### 6. Inicializar la base de datos

```bash
python -c "from src.database.db_manager import DatabaseManager; db = DatabaseManager(); db.initialize_database()"
```

## Estructura del Proyecto

```
crypto_tracker/
├── src/
│   ├── database/           # Gestión de base de datos
│   │   ├── db_manager.py   # Clase principal DatabaseManager
│   │   ├── models.py       # Definiciones de modelos de datos
│   │   └── migrations.py   # Migraciones de esquema
│   ├── api/                # Conectores con plataformas
│   │   ├── base_connector.py
│   │   ├── binance_connector.py
│   │   ├── coinbase_connector.py
│   │   ├── kraken_connector.py
│   │   ├── blockchain_connector.py
│   │   └── coingecko_connector.py
│   ├── utils/              # Utilidades y helpers
│   │   ├── config_loader.py
│   │   ├── logger.py
│   │   ├── decorators.py
│   │   └── validators.py
│   └── portfolio/          # Cálculos de portfolio
│       ├── portfolio_manager.py
│       └── tax_calculator.py
├── tests/                  # Suite de tests
├── scripts/                # Scripts de prueba y utilidad
├── config.yaml             # Configuración principal
├── .env.example            # Plantilla de variables de entorno
└── requirements.txt        # Dependencias Python
```

## Uso Básico

### Uso como Clase Externa

```python
from src.database.db_manager import DatabaseManager
from src.portfolio.portfolio_manager import PortfolioManager

# Inicializar gestor de base de datos
db_manager = DatabaseManager()

# Obtener balances del portfolio valorados en EUR
portfolio = PortfolioManager(db_manager)
balances = portfolio.get_portfolio_valuation_eur()

# Obtener información de transacciones
transactions = db_manager.get_transactions(
    platform='binance',
    start_date='2024-01-01',
    end_date='2024-12-31'
)
```

### Scripts de Sincronización

```bash
# Sincronizar datos desde Binance
python scripts/test_binance.py

# Sincronizar datos desde Coinbase
python scripts/test_coinbase.py

# Sincronizar datos desde Kraken
python scripts/test_kraken.py

# Sincronizar todas las plataformas
python scripts/sync_data.py

# Generar reporte fiscal anual
python scripts/report_generator.py --year 2024 --output report_2024.pdf
```

## Configuración

### Archivo config.yaml

Define:

- URLs de endpoints API
- Tokens soportados y sus símbolos alternativos
- ABIs de contratos inteligentes
- Configuración de redes blockchain
- Parámetros de sincronización
- Tipos de transacciones

### Archivo .env

Gestiona:

- API keys de Binance, Coinbase, Kraken
- URLs de RPC privadas
- Configuración de logging
- Parámetros de base de datos

## Base de Datos

### Tablas Principales

- **transactions**: Registro de todas las operaciones
- **balances**: Snapshot histórico de balances
- **tokens**: Catálogo de tokens/criptomonedas
- **token_networks**: Tokens en diferentes L2s
- **token_aliases**: Nombres alternativos de tokens
- **price_history**: Histórico de precios desde CoinGecko
- **raw_api_responses**: Respuestas JSON originales de APIs
- **portfolio_snapshots**: Snapshots de valoración del portfolio

### Características Especiales

- Almacenamiento de JSON bruto en `raw_api_data` para auditoría
- Campos UTC-aware para timestamp (independiente de configuración regional)
- Normalización de decimales con Decimal para precisión fiscal
- Soporte para tokens dinámicos sin precarga

## Funcionalidades por Implementar

- [ ] Conectores API para cada plataforma
- [ ] Parseo y normalización de datos heterogéneos
- [ ] Cálculos de impermanent loss (Uniswap)
- [ ] Algoritmos de cálculo fiscal (FIFO, LIFO, Media ponderada)
- [ ] Webhooks para actualizaciones en tiempo real
- [ ] Dashboard web (Flask/FastAPI)
- [ ] Exportación a formatos de impuestos españoles
- [ ] Alertas de precios
- [ ] Análisis de rendimiento

## Desarrollo

### Ejecutar Tests

```bash
# Tests unitarios
pytest tests/test_database.py -v

# Tests de integración
pytest tests/test_integration.py -v

# Cobertura de tests
pytest --cov=src tests/
```

### Generar Documentación

```bash
# Generar documentación con Sphinx
sphinx-build -b html docs/ docs/_build/
```

## Consideraciones de Seguridad

- **Nunca** hacer commit de .env con credenciales reales
- Usar API keys con permisos limitados (solo lectura cuando sea posible)
- Almacenar .env en ubicación segura
- Encriptar base de datos en producción
- Mantener copias de seguridad regulares

## Soporte y Contribuciones

Para issues o sugerencias, contactar al equipo de desarrollo.

## Licencia

Privado - Uso personal

## Changelog

### v0.1.0 (Inicial)

- Estructura base del proyecto
- Definición de modelos de datos
- Estructura de conectores
- Configuración básica

---

**Última actualización**: 2025-12-02
**Versión**: 0.1.0