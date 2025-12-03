"""
FastAPI Routes (v1)
===================

HTTP API endpoints for portfolio management, taxes, and reporting.
Fully integrated with services and database.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from decimal import Decimal
from datetime import datetime

from src.api.v1.schemas import (
    WalletSchema, TransactionSchema, BalanceSchema, 
    PortfolioSummarySchema, TaxReportSchema, ErrorSchema
)
from src.api.v1.dependencies import (
    get_db, get_portfolio_service, get_tax_calculator, 
    get_report_generator
)
from src.services import PortfolioService, TaxCalculator, ReportGenerator
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["v1"])


# ============================================================================
# WALLET ENDPOINTS
# ============================================================================

@router.post("/wallets", response_model=dict, status_code=201)
async def create_wallet(
    wallet: WalletSchema,
    portfolio_svc: PortfolioService = Depends(get_portfolio_service)
):
    """
    Create new wallet
    
    Example:
        POST /api/v1/wallets
        {
            "address": "0x742d35Cc6634C0532925a3b844Bc0e8e15b51d93",
            "wallet_type": "hot",
            "network": "ethereum",
            "label": "My Main Wallet"
        }
    """
    try:
        result = portfolio_svc.add_wallet(
            address=wallet.address,
            wallet_type=wallet.wallet_type,
            network=wallet.network,
            label=wallet.label
        )
        return result
    except Exception as e:
        logger.error(f"Error creating wallet: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/wallets", response_model=List[dict])
async def list_wallets(
    network: Optional[str] = Query(None, description="Filter by network"),
    portfolio_svc: PortfolioService = Depends(get_portfolio_service)
):
    """
    List all wallets or filter by network
    
    Example:
        GET /api/v1/wallets?network=ethereum
    """
    try:
        wallets = portfolio_svc.get_wallets(network=network)
        return wallets
    except Exception as e:
        logger.error(f"Error listing wallets: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/wallets/{wallet_id}", response_model=dict)
async def get_wallet(
    wallet_id: int,
    portfolio_svc: PortfolioService = Depends(get_portfolio_service)
):
    """
    Get wallet by ID
    
    Example:
        GET /api/v1/wallets/1
    """
    try:
        wallet = portfolio_svc.get_wallet(wallet_id)
        if not wallet:
            raise HTTPException(status_code=404, detail="Wallet not found")
        return wallet
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting wallet: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/wallets/{wallet_id}", status_code=204)
async def delete_wallet(
    wallet_id: int,
    portfolio_svc: PortfolioService = Depends(get_portfolio_service)
):
    """
    Delete wallet and all associated data
    
    Example:
        DELETE /api/v1/wallets/1
    """
    try:
        success = portfolio_svc.remove_wallet(wallet_id)
        if not success:
            raise HTTPException(status_code=404, detail="Wallet not found")
        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting wallet: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


# ============================================================================
# TRANSACTION ENDPOINTS
# ============================================================================

@router.post("/wallets/{wallet_id}/transactions", response_model=dict, status_code=201)
async def record_transaction(
    wallet_id: int,
    transaction: TransactionSchema,
    portfolio_svc: PortfolioService = Depends(get_portfolio_service)
):
    """
    Record transaction for wallet
    
    Example:
        POST /api/v1/wallets/1/transactions
        {
            "tx_hash": "0xabc123...",
            "tx_type": "buy",
            "token_in": "USD",
            "token_out": "ETH",
            "amount_in": "1000",
            "amount_out": "0.5",
            "fee": "10",
            "price_usd_in": "1.0",
            "price_usd_out": "2000.0"
        }
    """
    try:
        result = portfolio_svc.record_transaction(
            wallet_id=wallet_id,
            tx_hash=transaction.tx_hash,
            tx_type=transaction.tx_type,
            token_in=transaction.token_in,
            token_out=transaction.token_out,
            amount_in=Decimal(str(transaction.amount_in)),
            amount_out=Decimal(str(transaction.amount_out)),
            fee=Decimal(str(transaction.fee)) if transaction.fee else Decimal("0"),
            fee_token=transaction.fee_token,
            price_usd_in=Decimal(str(transaction.price_usd_in)) if transaction.price_usd_in else None,
            price_usd_out=Decimal(str(transaction.price_usd_out)) if transaction.price_usd_out else None,
            notes=transaction.notes
        )
        return result
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error recording transaction: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/wallets/{wallet_id}/transactions", response_model=List[dict])
async def list_transactions(
    wallet_id: int,
    limit: int = Query(100, ge=1, le=1000, description="Max transactions to return"),
    portfolio_svc: PortfolioService = Depends(get_portfolio_service)
):
    """
    List wallet transactions
    
    Example:
        GET /api/v1/wallets/1/transactions?limit=50
    """
    try:
        transactions = portfolio_svc.get_transactions(wallet_id, limit=limit)
        return transactions
    except Exception as e:
        logger.error(f"Error listing transactions: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


# ============================================================================
# BALANCE ENDPOINTS
# ============================================================================

@router.post("/wallets/{wallet_id}/balances", response_model=dict, status_code=201)
async def update_balance(
    wallet_id: int,
    balance: BalanceSchema,
    portfolio_svc: PortfolioService = Depends(get_portfolio_service)
):
    """
    Record balance snapshot for wallet
    
    Example:
        POST /api/v1/wallets/1/balances
        {
            "token_symbol": "ETH",
            "balance": "10.5",
            "balance_usd": "21000"
        }
    """
    try:
        result = portfolio_svc.update_balance(
            wallet_id=wallet_id,
            token_symbol=balance.token_symbol,
            balance=Decimal(str(balance.balance)),
            balance_usd=Decimal(str(balance.balance_usd)) if balance.balance_usd else None
        )
        return result
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating balance: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# PORTFOLIO ENDPOINTS
# ============================================================================

@router.get("/portfolio/summary", response_model=dict)
async def portfolio_summary(
    portfolio_svc: PortfolioService = Depends(get_portfolio_service)
):
    """
    Get portfolio summary across all wallets
    
    Example:
        GET /api/v1/portfolio/summary
    """
    try:
        summary = portfolio_svc.get_portfolio_value()
        return summary
    except Exception as e:
        logger.error(f"Error getting portfolio summary: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/reports/portfolio", response_model=dict)
async def portfolio_report(
    wallet_id: Optional[int] = Query(None, description="Optional wallet filter"),
    report_gen: ReportGenerator = Depends(get_report_generator)
):
    """
    Generate comprehensive portfolio report
    
    Example:
        GET /api/v1/reports/portfolio?wallet_id=1
    """
    try:
        report = report_gen.generate_portfolio_summary(wallet_id=wallet_id)
        return report
    except Exception as e:
        logger.error(f"Error generating portfolio report: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/reports/assets", response_model=dict)
async def asset_breakdown(
    wallet_id: Optional[int] = Query(None, description="Optional wallet filter"),
    report_gen: ReportGenerator = Depends(get_report_generator)
):
    """
    Generate asset allocation breakdown
    
    Example:
        GET /api/v1/reports/assets?wallet_id=1
    """
    try:
        report = report_gen.generate_asset_breakdown(wallet_id=wallet_id)
        return report
    except Exception as e:
        logger.error(f"Error generating asset breakdown: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/reports/transactions", response_model=dict)
async def transaction_report(
    wallet_id: Optional[int] = Query(None, description="Optional wallet filter"),
    start_date: Optional[datetime] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[datetime] = Query(None, description="End date (ISO format)"),
    limit: int = Query(1000, ge=1, le=10000, description="Max transactions"),
    report_gen: ReportGenerator = Depends(get_report_generator)
):
    """
    Generate transaction activity report
    
    Example:
        GET /api/v1/reports/transactions?wallet_id=1&limit=500
    """
    try:
        report = report_gen.generate_transaction_report(
            wallet_id=wallet_id,
            start_date=start_date,
            end_date=end_date,
            limit=limit
        )
        return report
    except Exception as e:
        logger.error(f"Error generating transaction report: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


# ============================================================================
# TAX ENDPOINTS
# ============================================================================

@router.post("/wallets/{wallet_id}/taxes/fifo", response_model=dict)
async def calculate_tax_fifo(
    wallet_id: int,
    year: int = Query(..., description="Tax year"),
    token: Optional[str] = Query(None, description="Optional token filter (e.g., ETH)"),
    tax_calc: TaxCalculator = Depends(get_tax_calculator)
):
    """
    Calculate taxes using FIFO method
    
    Example:
        POST /api/v1/wallets/1/taxes/fifo?year=2024&token=ETH
    """
    try:
        result = tax_calc.calculate_fifo(
            wallet_id=wallet_id,
            year=year,
            token=token
        )
        return result
    except Exception as e:
        logger.error(f"Error calculating FIFO tax: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/wallets/{wallet_id}/taxes/lifo", response_model=dict)
async def calculate_tax_lifo(
    wallet_id: int,
    year: int = Query(..., description="Tax year"),
    token: Optional[str] = Query(None, description="Optional token filter"),
    tax_calc: TaxCalculator = Depends(get_tax_calculator)
):
    """
    Calculate taxes using LIFO method
    
    Example:
        POST /api/v1/wallets/1/taxes/lifo?year=2024
    """
    try:
        result = tax_calc.calculate_lifo(
            wallet_id=wallet_id,
            year=year,
            token=token
        )
        return result
    except Exception as e:
        logger.error(f"Error calculating LIFO tax: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/wallets/{wallet_id}/taxes/average-cost", response_model=dict)
async def calculate_tax_average_cost(
    wallet_id: int,
    year: int = Query(..., description="Tax year"),
    token: Optional[str] = Query(None, description="Optional token filter"),
    tax_calc: TaxCalculator = Depends(get_tax_calculator)
):
    """
    Calculate taxes using Average Cost method
    
    Example:
        POST /api/v1/wallets/1/taxes/average-cost?year=2024
    """
    try:
        result = tax_calc.calculate_average_cost(
            wallet_id=wallet_id,
            year=year,
            token=token
        )
        return result
    except Exception as e:
        logger.error(f"Error calculating average cost tax: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/wallets/{wallet_id}/taxes/summary", response_model=dict)
async def tax_annual_summary(
    wallet_id: int,
    year: int = Query(..., description="Tax year"),
    tax_calc: TaxCalculator = Depends(get_tax_calculator)
):
    """
    Get annual tax summary for wallet
    
    Example:
        GET /api/v1/wallets/1/taxes/summary?year=2024
    """
    try:
        summary = tax_calc.get_annual_summary(wallet_id=wallet_id, year=year)
        return summary
    except Exception as e:
        logger.error(f"Error getting tax summary: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/reports/taxes", response_model=dict)
async def tax_report(
    wallet_id: int = Query(..., description="Wallet ID"),
    year: int = Query(..., description="Tax year"),
    method: Optional[str] = Query(None, description="Tax method filter (FIFO/LIFO/AVERAGE_COST)"),
    report_gen: ReportGenerator = Depends(get_report_generator)
):
    """
    Generate detailed tax report
    
    Example:
        GET /api/v1/reports/taxes?wallet_id=1&year=2024&method=FIFO
    """
    try:
        report = report_gen.generate_tax_report(
            wallet_id=wallet_id,
            year=year,
            tax_method=method
        )
        return report
    except Exception as e:
        logger.error(f"Error generating tax report: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# COMPREHENSIVE REPORT
# ============================================================================

@router.get("/reports/comprehensive", response_model=dict)
async def comprehensive_report(
    wallet_id: Optional[int] = Query(None, description="Optional wallet filter"),
    report_gen: ReportGenerator = Depends(get_report_generator)
):
    """
    Generate comprehensive report with all data sections
    
    Example:
        GET /api/v1/reports/comprehensive?wallet_id=1
    """
    try:
        report = report_gen.generate_comprehensive_report(wallet_id=wallet_id)
        return report
    except Exception as e:
        logger.error(f"Error generating comprehensive report: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


# ============================================================================
# HEALTH & STATUS
# ============================================================================

@router.get("/health", response_model=dict)
async def health_check():
    """Health check endpoint"""
    return {
        "status": "ok",
        "service": "Crypto Portfolio Tracker",
        "version": "3.0.0"
    }
