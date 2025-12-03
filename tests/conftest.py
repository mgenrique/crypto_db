"""
Test configuration
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from crypto_db.database import Base


@pytest.fixture
def db_session():
    """Create a test database session"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    yield session
    
    session.close()
