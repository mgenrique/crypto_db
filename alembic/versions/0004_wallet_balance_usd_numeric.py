"""convert wallet_balances.balance_usd to numeric

Revision ID: 0004_wallet_balance_usd_numeric
Revises: 0003_add_total_usd
Create Date: 2025-12-03 00:20:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column
from sqlalchemy import String, Numeric

# revision identifiers, used by Alembic.
revision = '0004_wallet_balance_usd_numeric'
down_revision = '0003_add_total_usd'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    dialect = conn.dialect.name

    # Strategy: Add a new nullable numeric column, copy parsable values, then drop old and rename.
    try:
        op.add_column('wallet_balances', sa.Column('balance_usd_numeric', sa.Numeric(30, 8), nullable=True))
    except Exception:
        pass

    # copy values where possible
    try:
        wb = table('wallet_balances', column('id', sa.Integer), column('balance_usd', String), column('balance_usd_numeric', Numeric))
        # Use raw SQL for portability
        if dialect == 'sqlite':
            # SQLite: perform copy via SQL casting
            conn.execute(sa.text("UPDATE wallet_balances SET balance_usd_numeric = CAST(balance_usd AS NUMERIC) WHERE balance_usd IS NOT NULL"))
        else:
            conn.execute(sa.text("UPDATE wallet_balances SET balance_usd_numeric = CAST(balance_usd AS NUMERIC) WHERE balance_usd IS NOT NULL"))
    except Exception:
        pass

    # Drop old column and rename new to balance_usd
    try:
        # Some DBs support drop_column and alter_column rename
        op.drop_column('wallet_balances', 'balance_usd')
    except Exception:
        # If drop fails on SQLite, rely on app-level handling
        pass

    try:
        op.alter_column('wallet_balances', 'balance_usd_numeric', new_column_name='balance_usd')
    except Exception:
        pass


def downgrade():
    try:
        # Add back string column
        op.add_column('wallet_balances', sa.Column('balance_usd_str', sa.String(100), nullable=True))
    except Exception:
        pass
    try:
        conn = op.get_bind()
        conn.execute(sa.text("UPDATE wallet_balances SET balance_usd_str = CAST(balance_usd AS TEXT) WHERE balance_usd IS NOT NULL"))
    except Exception:
        pass
    try:
        op.drop_column('wallet_balances', 'balance_usd')
    except Exception:
        pass
    try:
        op.alter_column('wallet_balances', 'balance_usd_str', new_column_name='balance_usd')
    except Exception:
        pass
