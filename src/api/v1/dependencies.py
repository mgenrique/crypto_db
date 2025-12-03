"""
FastAPI Dependencies
====================

Dependency injection for FastAPI routes.
"""

from functools import lru_cache
from typing import Generator
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)


def get_db() -> Generator[Session, None, None]:
    """
    Get database session for dependency injection
    
    Usage:
        @app.get("/items")
        async def list_items(db: Session = Depends(get_db)):
            items = db.query(ItemModel).all()
    """
    from src.database.manager import get_db_manager
    
    db_manager = get_db_manager()
    session = db_manager.get_session()
    try:
        yield session
    finally:
        session.close()


@lru_cache()
def get_portfolio_service():
    """Get portfolio service singleton"""
    from src.services.portfolio_service import PortfolioService
    from src.database.manager import get_db_manager
    
    db_manager = get_db_manager()
    return PortfolioService(db_manager)


@lru_cache()
def get_tax_calculator():
    """Get tax calculator singleton"""
    from src.services.tax_calculator import TaxCalculator
    from src.database.manager import get_db_manager
    
    db_manager = get_db_manager()
    return TaxCalculator(db_manager)


@lru_cache()
def get_report_generator():
    """Get report generator singleton"""
    from src.services.report_generator import ReportGenerator
    from src.database.manager import get_db_manager
    
    db_manager = get_db_manager()
    return ReportGenerator(db_manager)
