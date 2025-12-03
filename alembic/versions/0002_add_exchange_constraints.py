"""add exchange unique constraints and indexes

Revision ID: 0002_add_exchange_constraints
Revises: 
Create Date: 2025-12-03 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0002_add_exchange_constraints'
down_revision = '0001_baseline'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    dialect = conn.dialect.name

    # Indexes
    try:
        op.create_index('idx_exchange_balance_account_asset', 'exchange_balances', ['exchange_account_id', 'asset'])
    except Exception:
        pass

    try:
        op.create_index('idx_exchange_trade_account_symbol', 'exchange_trades', ['exchange_account_id', 'symbol'])
    except Exception:
        pass

    try:
        op.create_index('idx_exchange_deposit_account_asset', 'exchange_deposits', ['exchange_account_id', 'asset'])
    except Exception:
        pass

    try:
        op.create_index('idx_exchange_withdrawal_account_asset', 'exchange_withdrawals', ['exchange_account_id', 'asset'])
    except Exception:
        pass

    # Unique constraints (skip for sqlite since altering tables is complex)
    if dialect != 'sqlite':
        try:
            op.create_unique_constraint('uq_exchange_trade_account_tradeid', 'exchange_trades', ['exchange_account_id', 'trade_id'])
        except Exception:
            pass

        try:
            op.create_unique_constraint('uq_exchange_deposit_account_depositid', 'exchange_deposits', ['exchange_account_id', 'deposit_id'])
        except Exception:
            pass

        try:
            op.create_unique_constraint('uq_exchange_withdrawal_account_withdrawalid', 'exchange_withdrawals', ['exchange_account_id', 'withdrawal_id'])
        except Exception:
            pass
    else:
        # On SQLite, adding a UNIQUE constraint requires table rebuild; skip and rely on application dedupe.
        pass


def downgrade():
    conn = op.get_bind()
    dialect = conn.dialect.name

    # Drop indexes
    try:
        op.drop_index('idx_exchange_balance_account_asset', table_name='exchange_balances')
    except Exception:
        pass

    try:
        op.drop_index('idx_exchange_trade_account_symbol', table_name='exchange_trades')
    except Exception:
        pass

    try:
        op.drop_index('idx_exchange_deposit_account_asset', table_name='exchange_deposits')
    except Exception:
        pass

    try:
        op.drop_index('idx_exchange_withdrawal_account_asset', table_name='exchange_withdrawals')
    except Exception:
        pass

    if dialect != 'sqlite':
        try:
            op.drop_constraint('uq_exchange_trade_account_tradeid', 'exchange_trades', type_='unique')
        except Exception:
            pass

        try:
            op.drop_constraint('uq_exchange_deposit_account_depositid', 'exchange_deposits', type_='unique')
        except Exception:
            pass

        try:
            op.drop_constraint('uq_exchange_withdrawal_account_withdrawalid', 'exchange_withdrawals', type_='unique')
        except Exception:
            pass
    else:
        pass
