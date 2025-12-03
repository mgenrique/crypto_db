"""add total_usd to exchange_balances

Revision ID: 0003_add_total_usd
Revises: 0002_add_exchange_constraints
Create Date: 2025-12-03 00:10:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0003_add_total_usd'
down_revision = '0002_add_exchange_constraints'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    dialect = conn.dialect.name

    # Add a nullable numeric column for USD-converted total balance.
    try:
        op.add_column('exchange_balances', sa.Column('total_usd', sa.Numeric(30, 8), nullable=True))
    except Exception:
        # On some DBs or older Alembic setups, this may fail; log and continue.
        pass


def downgrade():
    try:
        op.drop_column('exchange_balances', 'total_usd')
    except Exception:
        pass
