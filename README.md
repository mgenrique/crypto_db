# Crypto DB - Sistema de Gestión de Criptomonedas

Sistema integral de gestión y seguimiento de transacciones de criptomonedas y depósitos FIAT en múltiples plataformas. Diseñado para mantener un registro unificado de operaciones, cálculos de valoración en tiempo real y conformidad fiscal española.

## Características

### Gestión de Transacciones
- ✅ Registro de transacciones de criptomonedas (compra, venta, transferencias, staking, rewards)
- ✅ Seguimiento de depósitos y retiros FIAT
- ✅ Soporte para múltiples plataformas (Binance, Coinbase, Kraken, etc.)
- ✅ Gestión de comisiones y costes de transacción

### Valoración en Tiempo Real
- ✅ Integración con CoinGecko API para precios en tiempo real
- ✅ Cálculo automático de balance de portfolio
- ✅ Soporte para múltiples monedas FIAT (EUR, USD, etc.)

### Conformidad Fiscal Española
- ✅ Cálculo de ganancias y pérdidas de capital usando método FIFO
- ✅ Aplicación de tramos impositivos españoles (19%, 21%, 23%, 26%)
- ✅ Generación de informes fiscales anuales
- ✅ Preparación para Modelo 100 (IRPF)
- ✅ Verificación de requisitos para Modelo 720

## Instalación

1. Clonar el repositorio:
```bash
git clone https://github.com/mgenrique/crypto_db.git
cd crypto_db
```

2. Crear entorno virtual:
```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

3. Instalar dependencias:
```bash
pip install -r requirements.txt
```

4. Configurar variables de entorno:
```bash
cp .env.example .env
# Editar .env con tu configuración
```

5. Inicializar base de datos:
```bash
python -m crypto_db.cli init
```

## Uso

### Gestión de Plataformas

Agregar una plataforma:
```bash
python -m crypto_db.cli platform add "Binance" --description "Binance Exchange"
python -m crypto_db.cli platform add "Coinbase" --description "Coinbase Exchange"
```

Listar plataformas:
```bash
python -m crypto_db.cli platform list
```

### Transacciones de Criptomonedas

Agregar una compra:
```bash
python -m crypto_db.cli crypto add \
  --platform-id 1 \
  --type buy \
  --crypto BTC \
  --amount 0.5 \
  --price 45000 \
  --currency EUR \
  --fee 50 \
  --date "2024-01-15 10:30:00" \
  --notes "Compra inicial de Bitcoin"
```

Agregar una venta:
```bash
python -m crypto_db.cli crypto add \
  --platform-id 1 \
  --type sell \
  --crypto BTC \
  --amount 0.2 \
  --price 50000 \
  --currency EUR \
  --fee 30
```

Listar transacciones:
```bash
python -m crypto_db.cli crypto list
python -m crypto_db.cli crypto list --crypto BTC
python -m crypto_db.cli crypto list --platform-id 1
```

Ver balance:
```bash
python -m crypto_db.cli crypto balance
python -m crypto_db.cli crypto balance --crypto BTC
```

Consultar precio actual:
```bash
python -m crypto_db.cli crypto price BTC
python -m crypto_db.cli crypto price ETH --currency USD
```

### Depósitos FIAT

Agregar depósito:
```bash
python -m crypto_db.cli fiat add \
  --platform-id 1 \
  --type deposit \
  --amount 10000 \
  --currency EUR \
  --date "2024-01-10 09:00:00" \
  --notes "Depósito inicial"
```

Agregar retiro:
```bash
python -m crypto_db.cli fiat add \
  --platform-id 1 \
  --type withdrawal \
  --amount 5000 \
  --currency EUR
```

Ver balance FIAT:
```bash
python -m crypto_db.cli fiat balance
python -m crypto_db.cli fiat balance --platform-id 1
```

### Informes Fiscales

Generar informe fiscal anual:
```bash
python -m crypto_db.cli tax report --year 2024
```

Calcular ganancias de capital:
```bash
python -m crypto_db.cli tax gains --year 2024
```

## Estructura de la Base de Datos

### Tablas Principales

- **platforms**: Plataformas de trading/exchange
- **crypto_transactions**: Transacciones de criptomonedas
- **fiat_deposits**: Depósitos y retiros FIAT
- **tax_reports**: Informes fiscales generados

### Tipos de Transacción

- `buy`: Compra de criptomoneda
- `sell`: Venta de criptomoneda
- `transfer_in`: Transferencia entrante
- `transfer_out`: Transferencia saliente
- `stake`: Staking de criptomoneda
- `unstake`: Unstaking de criptomoneda
- `reward`: Recompensas recibidas
- `fee`: Comisiones pagadas

## Conformidad Fiscal Española

El sistema implementa las siguientes características para cumplir con la normativa fiscal española:

### Cálculo de Ganancias de Capital
- Método FIFO (First In, First Out) para calcular base de coste
- Tracking automático de fechas de adquisición y venta
- Cálculo de plusvalías y minusvalías

### Tramos Impositivos
- 19% hasta 6.000€
- 21% de 6.000€ a 50.000€
- 23% de 50.000€ a 200.000€
- 26% más de 200.000€

### Informes Requeridos
- **Modelo 100 (IRPF)**: Declaración anual de la renta
- **Modelo 720**: Declaración de bienes en el extranjero (si >50.000€)

## API de Precios

El sistema utiliza la API de CoinGecko para obtener precios en tiempo real. Las criptomonedas soportadas incluyen:

- BTC (Bitcoin)
- ETH (Ethereum)
- ADA (Cardano)
- SOL (Solana)
- DOT (Polkadot)
- MATIC (Polygon)
- LINK (Chainlink)
- XRP (Ripple)
- Y más...

## Desarrollo

### Ejecutar Tests
```bash
pytest tests/
pytest tests/ --cov=crypto_db
```

### Formato de Código
```bash
black crypto_db/
flake8 crypto_db/
mypy crypto_db/
```

## Licencia

MIT License

## Contribuciones

Las contribuciones son bienvenidas. Por favor, abre un issue o pull request para sugerencias o mejoras.

## Soporte

Para preguntas o problemas, abre un issue en el repositorio de GitHub.