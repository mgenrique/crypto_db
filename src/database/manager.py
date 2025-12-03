"""
Database Manager
================

SQLAlchemy database management with connection pooling.
"""

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool, QueuePool
from contextlib import contextmanager
import logging
import os

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Database connection manager with pooling and lifecycle management"""

    def __init__(self, database_url: str, echo: bool = False, pool_size: int = 20):
        """
        Initialize database manager
        
        Args:
            database_url: Connection string (sqlite, postgresql, etc)
            echo: Log SQL statements
            pool_size: Connection pool size (only for PostgreSQL)
        """
        self.database_url = database_url
        self.echo = echo
        
        # Configure pool based on database type
        if "sqlite" in database_url:
            # SQLite doesn't support connection pooling well
            self.engine = create_engine(
                database_url,
                echo=echo,
                connect_args={"check_same_thread": False},
                poolclass=NullPool,
            )
        else:
            # PostgreSQL with connection pooling
            self.engine = create_engine(
                database_url,
                echo=echo,
                poolclass=QueuePool,
                pool_size=pool_size,
                max_overflow=10,
                pool_pre_ping=True,  # Verify connection before reusing
            )
        
        self.SessionLocal = sessionmaker(bind=self.engine, expire_on_commit=False)
        self._init_event_listeners()
        logger.info(f"✅ Database initialized: {self._mask_url(database_url)}")

    def _init_event_listeners(self):
        """Initialize SQLAlchemy event listeners"""
        @event.listens_for(self.engine, "connect")
        def set_sqlite_pragma(dbapi_conn, connection_record):
            """Enable foreign keys for SQLite"""
            if "sqlite" in self.database_url:
                cursor = dbapi_conn.cursor()
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.close()

    @staticmethod
    def _mask_url(url: str) -> str:
        """Mask sensitive info in connection string"""
        if "@" in url:
            parts = url.split("@")
            return f"{parts.split(':')}:***@{parts}"
        return url

    def create_tables(self, base):
        """
        Create all tables from ORM models
        
        Args:
            base: SQLAlchemy declarative base
        """
        try:
            logger.info("Creating database tables...")
            base.metadata.create_all(self.engine)
            logger.info("✅ Database tables created successfully")
        except Exception as e:
            logger.error(f"❌ Error creating tables: {str(e)}")
            raise

    def drop_tables(self, base):
        """Drop all tables (USE WITH CAUTION)"""
        logger.warning("⚠️  Dropping all database tables...")
        base.metadata.drop_all(self.engine)
        logger.info("✅ All tables dropped")

    def get_session(self) -> Session:
        """Get a new database session"""
        return self.SessionLocal()

    @contextmanager
    def session_context(self):
        """Context manager for database sessions"""
        session = self.get_session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Session error: {str(e)}")
            raise
        finally:
            session.close()

    def health_check(self) -> bool:
        """Check database connectivity"""
        try:
            with self.session_context() as session:
                session.execute("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"❌ Database health check failed: {str(e)}")
            return False

    def close(self):
        """Close all connections"""
        self.engine.dispose()
        logger.info("Database connections closed")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# Global database manager instance
_db_manager = None


def get_db_manager() -> DatabaseManager:
    """Get or create global database manager"""
    global _db_manager
    if _db_manager is None:
        from src.utils.config_loader import ConfigLoader
        config = ConfigLoader()
        database_url = config.get("DATABASE_URL", "sqlite:///./portfolio.db")
        echo = config.get("DATABASE_ECHO", False)
        _db_manager = DatabaseManager(database_url, echo=echo)
    return _db_manager


def init_database():
    """Initialize database (call on app startup)"""
    from src.database.models import Base
    db = get_db_manager()
    db.create_tables(Base)
