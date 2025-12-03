"""
Pydantic Schemas for API
========================

Data validation and serialization schemas.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal


# ============================================================================
# REQUEST SCHEMAS
# ============================================================================

class WalletSchema(BaseModel):
    """Wallet creation schema"""
    address: str = Field(..., min_length=1, max_length=255, description="Wallet address")
    wallet_type: str = Field(..., description="hot, cold, hardware, exchange, defi")
    network: str = Field(..., description="ethereum, arbitrum, base, polygon, etc")
    label: Optional[str] = Field(None, max_length=255, description="User-friendly label")

    class Config:
        json_schema_extra = {
            "example": {
                "address": "0x742d35Cc6634C0532925a3b844Bc0e8e15b51d93",
                "wallet_type": "hot",
                "network": "ethereum",
                "label": "My Ethereum Wallet"
            }
        }


class TransactionSchema(BaseModel):
    """Transaction recording schema"""
    tx_hash: str = Field(..., min_length=1, description="Transaction hash")
    tx_type: str = Field(..., description="buy, sell, swap, transfer_in, transfer_out")
    token_in: str = Field(..., max_length=20, description="Input token symbol")
    token_out: str = Field(..., max_length=20, description="Output token symbol")
    amount_in: Decimal = Field(..., gt=0, description="Input amount")
    amount_out: Decimal = Field(..., gt=0, description="Output amount")
    fee: Optional[Decimal] = Field(None, ge=0, description="Transaction fee")
    fee_token: Optional[str] = Field(None, max_length=20, description="Fee token symbol")
    price_usd_in: Optional[Decimal] = Field(None, description="Historical price of input token in USD")
    price_usd_out: Optional[Decimal] = Field(None, description="Historical price of output token in USD")
    notes: Optional[str] = Field(None, description="Additional notes")

    class Config:
        json_schema_extra = {
            "example": {
                "tx_hash": "0xabc123...",
                "tx_type": "buy",
                "token_in": "USDC",
                "token_out": "ETH",
                "amount_in": "1000",
                "amount_out": "0.5",
                "fee": "10",
                "price_usd_in": "1.0",
                "price_usd_out": "2000.0"
            }
        }


class BalanceSchema(BaseModel):
    """Balance snapshot schema"""
    token_symbol: str = Field(..., max_length=20, description="Token symbol")
    balance: Decimal = Field(..., ge=0, description="Token balance")
    balance_usd: Optional[Decimal] = Field(None, ge=0, description="USD equivalent")

    class Config:
        json_schema_extra = {
            "example": {
                "token_symbol": "ETH",
                "balance": "10.5",
                "balance_usd": "21000"
            }
        }


# ============================================================================
# RESPONSE SCHEMAS
# ============================================================================

class PortfolioSummarySchema(BaseModel):
    """Portfolio summary response"""
    total_value_usd: str = Field(..., description="Total portfolio value in USD")
    wallet_count: int = Field(..., description="Number of wallets")
    transaction_count: int = Field(..., description="Number of transactions")
    assets: Dict[str, Any] = Field(..., description="Asset breakdown")
    last_updated: str = Field(..., description="Last update timestamp")


class TaxRecordResponseSchema(BaseModel):
    """Tax record response"""
    method: str = Field(..., description="Tax calculation method")
    year: int = Field(..., description="Tax year")
    total_gain_loss: str = Field(..., description="Total gain or loss")
    total_cost_basis: str = Field(..., description="Total cost basis")
    total_proceeds: str = Field(..., description="Total proceeds")
    estimated_tax_usd: str = Field(..., description="Estimated tax in USD")


class TaxReportSchema(BaseModel):
    """Tax report response"""
    report_type: str = Field(..., description="Report type identifier")
    generated_at: str = Field(..., description="Generation timestamp")
    wallet_id: int = Field(..., description="Wallet ID")
    year: int = Field(..., description="Tax year")
    summary: Dict[str, Any] = Field(..., description="Tax summary")
    by_method: Optional[Dict[str, Any]] = Field(None, description="Breakdown by method")


class ErrorSchema(BaseModel):
    """Error response"""
    detail: str = Field(..., description="Error message")
    status_code: int = Field(..., description="HTTP status code")

    class Config:
        json_schema_extra = {
            "example": {
                "detail": "Wallet not found",
                "status_code": 404
            }
        }
