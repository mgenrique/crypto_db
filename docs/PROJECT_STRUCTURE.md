# Crypto DB - Project Structure

```
crypto_db/
├── crypto_db/              # Main package
│   ├── __init__.py        # Package initialization
│   ├── cli.py             # Command-line interface
│   ├── database.py        # Database configuration
│   ├── models.py          # SQLAlchemy models
│   ├── platform_service.py    # Platform management
│   ├── crypto_service.py      # Crypto transaction service
│   ├── fiat_service.py        # FIAT deposit service
│   ├── tax_service.py         # Spanish tax compliance
│   └── price_service.py       # Real-time price fetching
├── tests/                 # Test suite
│   ├── __init__.py
│   ├── conftest.py        # Test fixtures
│   ├── test_platform_service.py
│   ├── test_crypto_service.py
│   ├── test_fiat_service.py
│   └── test_tax_service.py
├── docs/                  # Documentation
│   ├── API.md             # API documentation
│   └── SPANISH_TAX_GUIDE.md  # Tax compliance guide
├── .env.example           # Environment variables template
├── .gitignore            # Git ignore rules
├── requirements.txt      # Python dependencies
├── setup.py              # Package setup
├── example.py            # Example usage script
├── LICENSE               # MIT License
└── README.md             # Project documentation
```

## Key Components

### Database Models

1. **Platform**: Represents trading/exchange platforms
2. **CryptoTransaction**: Cryptocurrency transactions
3. **FiatDeposit**: FIAT currency deposits/withdrawals
4. **TaxReport**: Generated tax reports

### Services

1. **PlatformService**: CRUD operations for platforms
2. **CryptoTransactionService**: Transaction management and portfolio tracking
3. **FiatDepositService**: FIAT balance management
4. **SpanishTaxService**: Tax compliance and reporting
5. **PriceService**: Real-time price fetching from CoinGecko

### CLI Commands

- `init`: Initialize database
- `platform`: Manage platforms
- `crypto`: Manage cryptocurrency transactions
- `fiat`: Manage FIAT deposits
- `tax`: Tax reporting and compliance

## Design Decisions

### Database

- SQLAlchemy ORM for database abstraction
- SQLite for development, PostgreSQL-ready for production
- Alembic for migrations (optional)

### Transaction Types

Cryptocurrency:
- BUY/SELL: Standard purchases and sales
- TRANSFER_IN/TRANSFER_OUT: Inter-platform transfers
- STAKE/UNSTAKE: Staking operations
- REWARD: Staking rewards, airdrops
- FEE: Transaction fees

FIAT:
- DEPOSIT: Money added to platform
- WITHDRAWAL: Money removed from platform

### Tax Compliance

- **FIFO Method**: Required by Spanish law
- **Tax Brackets**: 19%, 21%, 23%, 26%
- **Cost Basis**: Tracked per cryptocurrency
- **Reporting**: Annual reports for Modelo 100

## Development Guidelines

### Adding New Features

1. Update models in `models.py` if database changes needed
2. Implement business logic in service layer
3. Add CLI commands in `cli.py` if user-facing
4. Write tests in `tests/` directory
5. Update documentation

### Testing

Run all tests:
```bash
pytest tests/
```

Run with coverage:
```bash
pytest tests/ --cov=crypto_db
```

### Code Quality

Format code:
```bash
black crypto_db/ tests/
```

Lint code:
```bash
flake8 crypto_db/
```

Type checking:
```bash
mypy crypto_db/
```

## Future Enhancements

Potential features for future versions:

1. **Web Interface**: Flask/FastAPI web application
2. **CSV Import**: Bulk transaction import from exchanges
3. **Multi-currency Support**: Non-EUR base currencies
4. **Advanced Reporting**: Graphical reports and charts
5. **API Integration**: Direct exchange API connections
6. **Mobile App**: React Native mobile application
7. **Backup/Export**: Data backup and export features
8. **Portfolio Analytics**: Advanced portfolio analysis
9. **Automated Tax Forms**: Direct Modelo 100 form generation
10. **Multi-user Support**: Support for multiple users/portfolios

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Run test suite
6. Submit a pull request

## Support

For issues or questions:
- Open an issue on GitHub
- Check the documentation in `docs/`
- Review the example script in `example.py`
