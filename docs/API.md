# API Documentation

## Database Models

### Platform

Represents a cryptocurrency exchange or trading platform.

**Fields:**
- `id`: Integer, primary key
- `name`: String(100), unique, platform name
- `description`: String(500), optional description
- `created_at`: DateTime, creation timestamp
- `updated_at`: DateTime, last update timestamp

### CryptoTransaction

Represents a cryptocurrency transaction.

**Fields:**
- `id`: Integer, primary key
- `platform_id`: Integer, foreign key to Platform
- `transaction_type`: Enum (TransactionType)
  - `BUY`: Purchase of cryptocurrency
  - `SELL`: Sale of cryptocurrency
  - `TRANSFER_IN`: Incoming transfer
  - `TRANSFER_OUT`: Outgoing transfer
  - `STAKE`: Staking operation
  - `UNSTAKE`: Unstaking operation
  - `REWARD`: Reward received
  - `FEE`: Fee paid
- `cryptocurrency`: String(20), crypto symbol (BTC, ETH, etc.)
- `amount`: Float, quantity of cryptocurrency
- `price_per_unit`: Float, price in FIAT currency
- `fiat_currency`: String(3), FIAT currency code (EUR, USD)
- `total_value`: Float, total transaction value
- `fee_amount`: Float, transaction fee
- `fee_currency`: String(20), fee currency
- `transaction_date`: DateTime, when transaction occurred
- `transaction_id`: String(200), platform's transaction ID
- `notes`: String(1000), optional notes
- `created_at`: DateTime, record creation
- `updated_at`: DateTime, record update

### FiatDeposit

Represents FIAT currency deposits and withdrawals.

**Fields:**
- `id`: Integer, primary key
- `platform_id`: Integer, foreign key to Platform
- `deposit_type`: Enum (DepositType)
  - `DEPOSIT`: Money deposited to platform
  - `WITHDRAWAL`: Money withdrawn from platform
- `amount`: Float, amount of FIAT
- `currency`: String(3), currency code (EUR, USD)
- `transaction_date`: DateTime, when transaction occurred
- `transaction_id`: String(200), transaction ID
- `notes`: String(1000), optional notes
- `created_at`: DateTime, record creation
- `updated_at`: DateTime, record update

### TaxReport

Stores generated tax reports.

**Fields:**
- `id`: Integer, primary key
- `tax_year`: Integer, year of the report
- `report_type`: String(50), type of report (annual, quarterly)
- `total_gains`: Float, total capital gains
- `total_losses`: Float, total capital losses
- `net_result`: Float, net gain/loss
- `generated_at`: DateTime, report generation time
- `report_data`: String, JSON serialized detailed data
- `notes`: String(1000), optional notes

## Service Layer

### PlatformService

Manages trading platforms.

**Methods:**

```python
create_platform(db, name, description=None) -> Platform
```
Create a new platform.

```python
get_platform(db, platform_id) -> Platform
```
Get platform by ID.

```python
get_platform_by_name(db, name) -> Platform
```
Get platform by name.

```python
get_all_platforms(db) -> List[Platform]
```
Get all platforms.

```python
update_platform(db, platform_id, name=None, description=None) -> Platform
```
Update platform details.

```python
delete_platform(db, platform_id) -> bool
```
Delete a platform (only if no transactions exist).

### CryptoTransactionService

Manages cryptocurrency transactions.

**Methods:**

```python
create_transaction(
    db,
    platform_id,
    transaction_type,
    cryptocurrency,
    amount,
    price_per_unit,
    fiat_currency="EUR",
    fee_amount=0.0,
    fee_currency="EUR",
    transaction_date=None,
    transaction_id=None,
    notes=None
) -> CryptoTransaction
```
Create a new cryptocurrency transaction.

```python
get_transactions(
    db,
    platform_id=None,
    cryptocurrency=None,
    transaction_type=None,
    start_date=None,
    end_date=None
) -> List[CryptoTransaction]
```
Get transactions with optional filtering.

```python
get_portfolio_balance(db, cryptocurrency=None) -> dict
```
Calculate current portfolio balance for each cryptocurrency.

```python
get_transaction_summary(db, start_date=None, end_date=None) -> dict
```
Get summary of transactions for a period.

### FiatDepositService

Manages FIAT deposits and withdrawals.

**Methods:**

```python
create_deposit(
    db,
    platform_id,
    deposit_type,
    amount,
    currency="EUR",
    transaction_date=None,
    transaction_id=None,
    notes=None
) -> FiatDeposit
```
Create a new FIAT deposit or withdrawal.

```python
get_deposits(
    db,
    platform_id=None,
    deposit_type=None,
    currency=None,
    start_date=None,
    end_date=None
) -> List[FiatDeposit]
```
Get FIAT deposits with optional filtering.

```python
get_balance(db, platform_id=None, currency="EUR") -> float
```
Calculate FIAT balance for a platform.

```python
get_deposit_summary(db, start_date=None, end_date=None, currency="EUR") -> dict
```
Get summary of FIAT deposits for a period.

### SpanishTaxService

Handles Spanish tax compliance.

**Methods:**

```python
calculate_capital_gains(db, tax_year) -> dict
```
Calculate capital gains for a tax year using FIFO method.

Returns:
```python
{
    'tax_year': int,
    'total_gains': float,
    'total_losses': float,
    'net_result': float,
    'transactions': List[dict],
    'remaining_holdings': dict
}
```

```python
calculate_tax_liability(net_gains) -> dict
```
Calculate tax liability based on Spanish tax brackets.

Returns:
```python
{
    'taxable_amount': float,
    'tax_owed': float,
    'effective_rate': float,
    'breakdown': List[dict]
}
```

```python
generate_tax_report(db, tax_year, report_type="annual") -> TaxReport
```
Generate comprehensive tax report for Spanish compliance.

```python
check_modelo_720_requirement(db) -> bool
```
Check if Modelo 720 reporting is required.

### PriceService

Fetches real-time cryptocurrency prices.

**Methods:**

```python
get_current_price(cryptocurrency, fiat_currency="EUR") -> float
```
Get current price of cryptocurrency in FIAT currency.

```python
get_multiple_prices(cryptocurrencies, fiat_currency="EUR") -> dict
```
Get current prices for multiple cryptocurrencies.

**Supported Cryptocurrencies:**
- BTC (Bitcoin)
- ETH (Ethereum)
- ADA (Cardano)
- SOL (Solana)
- DOT (Polkadot)
- MATIC (Polygon)
- LINK (Chainlink)
- XRP (Ripple)
- USDT (Tether)
- USDC (USD Coin)
- BNB (Binance Coin)
- AVAX (Avalanche)

## CLI Commands

See README.md for comprehensive CLI documentation.

## Usage Examples

### Python API Usage

```python
from crypto_db.database import SessionLocal, init_db
from crypto_db.platform_service import PlatformService
from crypto_db.crypto_service import CryptoTransactionService
from crypto_db.models import TransactionType

# Initialize database
init_db()

# Create session
db = SessionLocal()

try:
    # Create platform
    platform = PlatformService.create_platform(
        db, "Binance", "Binance Exchange"
    )
    
    # Create transaction
    transaction = CryptoTransactionService.create_transaction(
        db=db,
        platform_id=platform.id,
        transaction_type=TransactionType.BUY,
        cryptocurrency="BTC",
        amount=0.5,
        price_per_unit=45000.0,
        fiat_currency="EUR"
    )
    
    # Get balance
    balance = CryptoTransactionService.get_portfolio_balance(db)
    print(balance)  # {'BTC': 0.5}
    
finally:
    db.close()
```

### Real-time Prices

```python
from crypto_db.price_service import PriceService

# Get single price
btc_price = PriceService.get_current_price("BTC", "EUR")
print(f"BTC: {btc_price} EUR")

# Get multiple prices
prices = PriceService.get_multiple_prices(["BTC", "ETH", "ADA"], "EUR")
for crypto, price in prices.items():
    print(f"{crypto}: {price} EUR")
```

### Tax Calculations

```python
from crypto_db.tax_service import SpanishTaxService
from crypto_db.database import SessionLocal

db = SessionLocal()

try:
    # Calculate capital gains
    gains = SpanishTaxService.calculate_capital_gains(db, 2024)
    print(f"Net gains: {gains['net_result']} EUR")
    
    # Calculate tax liability
    tax = SpanishTaxService.calculate_tax_liability(gains['net_result'])
    print(f"Tax owed: {tax['tax_owed']} EUR")
    
    # Generate report
    report = SpanishTaxService.generate_tax_report(db, 2024)
    print(f"Report ID: {report.id}")
    
finally:
    db.close()
```
