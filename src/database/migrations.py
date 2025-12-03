"""
Database Migrations
===================

Alembic configuration for database versioning.
"""

import os
import logging
from alembic import command
from alembic.config import Config as AlembicConfig

logger = logging.getLogger(__name__)


class MigrationManager:
    """Manage database migrations"""

    def __init__(self, database_url: str):
        self.database_url = database_url
        self.alembic_cfg = self._get_alembic_config()

    def _get_alembic_config(self) -> AlembicConfig:
        """Get Alembic configuration"""
        # Assume alembic.ini exists in project root
        alembic_cfg = AlembicConfig("alembic.ini")
        alembic_cfg.set_main_option("sqlalchemy.url", self.database_url)
        return alembic_cfg

    def upgrade_head(self):
        """Upgrade to latest migration"""
        logger.info("Running migrations...")
        command.upgrade(self.alembic_cfg, "head")
        logger.info("✅ Migrations completed")

    def downgrade(self, revision: str = "-1"):
        """Downgrade to specific revision"""
        logger.warning(f"Downgrading to {revision}...")
        command.downgrade(self.alembic_cfg, revision)

    def current_revision(self) -> str:
        """Get current database revision"""
        command.current(self.alembic_cfg)

    def history(self):
        """Show migration history"""
        command.history(self.alembic_cfg)


def run_migrations():
    """Run all pending migrations on startup"""
    from src.utils.config_loader import ConfigLoader
    config = ConfigLoader()
    database_url = config.get("DATABASE_URL", "sqlite:///./portfolio.db")
    
    # Only run migrations for PostgreSQL (SQLite doesn't need them)
    if "postgresql" in database_url:
        try:
            manager = MigrationManager(database_url)
            manager.upgrade_head()
        except Exception as e:
            logger.error(f"Migration error: {str(e)}")
            # Don't fail startup if migrations fail
