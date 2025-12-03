"""
API v1 Module - Crypto Portfolio Tracker v3
===========================================================================

Módulo de API FastAPI v1 que incluye:
- Schemas (validación Pydantic)
- Dependencies (inyección de dependencias)
- Routes (endpoints HTTP)

NOTA: Este módulo va en src/api/v1/ y NO toca los conectores de src/api/

Estructura:
    src/api/
    ├── __init__.py (conectores)
    ├── base_connector.py
    ├── binance_connector.py
    └── v1/
        ├── __init__.py (ESTE ARCHIVO)
        ├── schemas.py
        ├── dependencies.py
        └── routes.py

Uso en main.py:
    from fastapi import FastAPI
    from src.api.v1 import router
    
    app = FastAPI(
        title="Crypto Portfolio Tracker",
        version="3.0.0",
        description="Advanced crypto portfolio management and tax tracking",
    )
    
    app.include_router(router)

Endpoints disponibles:
    - GET /health (health check)
    - POST /api/v1/wallets (crear wallet)
    - GET /api/v1/wallets (listar wallets)
    - DELETE /api/v1/wallets/{wallet_id} (eliminar wallet)
    - PUT /api/v1/wallets/{wallet_id}/balances/{token_symbol} (actualizar balance)
    - GET /api/v1/portfolio/summary (resumen portfolio)
    - GET /api/v1/portfolio/assets (desglose de activos)
    - POST /api/v1/wallets/{wallet_id}/transactions (registrar transacción)
    - GET /api/v1/wallets/{wallet_id}/transactions (listar transacciones)
    - GET /api/v1/wallets/{wallet_id}/taxes (reporte de impuestos)
"""

from .schemas import (
    WalletSchema,
    TransactionSchema,
    BalanceSchema,
    PortfolioSummarySchema,
    TaxReportSchema,
    ErrorSchema,
)

from .dependencies import (
    get_db,
    get_portfolio_service,
    get_tax_calculator,
    get_report_generator,
)

from .routes import router
from .exchanges_routes import router as exchanges_router
from .auth_routes import router as auth_router
from .price_mappings_routes import router as price_mappings_router

__all__ = [
    # Schemas
    "WalletSchema",
    "TransactionSchema",
    "BalanceSchema",
    "PortfolioSummarySchema",
    "TaxReportSchema",
    "ErrorSchema",
    # Dependencies
    "get_db",
    "get_portfolio_service",
    "get_tax_calculator",
    "get_report_generator",
    # Routes
    "router",
    "exchanges_router",
    "auth_router",
    "price_mappings_router",
]
