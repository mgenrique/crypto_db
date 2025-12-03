"""Reset the application's database schema.

Usage:
    python scripts/reset_db.py

This script drops all tables and recreates them using the SQLAlchemy
`Base` declarative metadata. Use it when you want a fresh DB to run tests
or to inspect a clean database state.
"""
import logging
import sys
import os

# Ensure project root is on sys.path so `from src...` imports work when the
# script is executed from the `scripts/` directory (or any other CWD).
root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if root not in sys.path:
    sys.path.insert(0, root)

from src.database import init_database, get_db_manager
from src.database.models import Base

logger = logging.getLogger(__name__)


def reset_db():
    dbm = get_db_manager()
    try:
        logger.info("Dropping all tables...")
        Base.metadata.drop_all(dbm.engine)
    except Exception as e:
        logger.warning(f"Drop tables failed (ignored): {e}")

    try:
        logger.info("Creating all tables and seeding config...")
        # Use init_database so table creation and post-create seeding happen
        init_database()
        logger.info("✅ Database schema recreated and seeded from config")
    except Exception as e:
        logger.error(f"Failed to create tables and seed: {e}")
        raise


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    reset_db()
    sys.exit(0)
