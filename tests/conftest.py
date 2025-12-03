import pytest

from src.database.manager import get_db_manager
from src.database.models import Base


@pytest.fixture(autouse=False)
def fresh_db():
    """Fixture to reset DB schema when explicitly requested by a test.

    By default this fixture is NOT autouse; tests that need a clean DB can
    request it with a function argument `fresh_db`. To reset the DB from the
    command line or CI, run the helper script `scripts/reset_db.py`.
    """
    dbm = get_db_manager()

    # Drop and recreate all tables to ensure a clean state
    try:
        Base.metadata.drop_all(dbm.engine)
    except Exception:
        # ignore if drop fails (e.g., first-run)
        pass
    Base.metadata.create_all(dbm.engine)

    yield dbm

    # Optionally remove tables after test to avoid cross-test contamination
    try:
        Base.metadata.drop_all(dbm.engine)
    except Exception:
        pass
