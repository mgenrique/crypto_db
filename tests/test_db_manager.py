import os
from src.database.manager import DatabaseManager


def test_sqlite_pragma_and_masking():
    """Verify PRAGMA foreign_keys=ON is set for SQLite and URL masking masks passwords."""
    # Use an in-memory SQLite DB for testing
    dm = DatabaseManager("sqlite:///:memory:")

    # Check PRAGMA foreign_keys is enabled on a new connection
    with dm.engine.connect() as conn:
        # Use exec_driver_sql for raw PRAGMA statements under SQLAlchemy 1.4/2.x
        result = conn.exec_driver_sql("PRAGMA foreign_keys").scalar_one()
        assert int(result) == 1, "SQLite foreign_keys PRAGMA should be ON"

    # Test URL masking for a typical URL with credentials
    test_url = "postgresql://alice:secretpass@db.example.com/mydb"
    masked = dm._mask_url(test_url)
    assert ":***@" in masked, f"Masked URL should hide password, got: {masked}"
