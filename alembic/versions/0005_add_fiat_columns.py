"""add fiat valuation columns to movement tables

Revision ID: 0005_add_fiat_columns
Revises: 0004_wallet_balance_usd_numeric
Create Date: 2025-12-03 00:40:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0005_add_fiat_columns'
down_revision = '0004_wallet_balance_usd_numeric'
branch_labels = None
depends_on = None


def upgrade():
    try:
        op.add_column('transactions', sa.Column('price_fiat_in', sa.Numeric(30,8), nullable=True))
        op.add_column('transactions', sa.Column('price_fiat_out', sa.Numeric(30,8), nullable=True))
    except Exception:
        pass

    try:
        op.add_column('tax_records', sa.Column('gain_loss_fiat', sa.Numeric(30,8), nullable=True))
        op.add_column('tax_records', sa.Column('cost_basis_fiat', sa.Numeric(30,8), nullable=True))
        op.add_column('tax_records', sa.Column('proceeds_fiat', sa.Numeric(30,8), nullable=True))
    except Exception:
        pass

    try:
        op.add_column('exchange_balances', sa.Column('total_fiat', sa.Numeric(30,8), nullable=True))
    except Exception:
        pass

    try:
        op.add_column('exchange_trades', sa.Column('price_fiat', sa.Numeric(30,8), nullable=True))
        op.add_column('exchange_trades', sa.Column('commission_fiat', sa.Numeric(30,8), nullable=True))
    except Exception:
        pass

    try:
        op.add_column('exchange_deposits', sa.Column('amount_fiat', sa.Numeric(30,8), nullable=True))
    except Exception:
        pass

    try:
        op.add_column('exchange_withdrawals', sa.Column('amount_fiat', sa.Numeric(30,8), nullable=True))
    except Exception:
        pass

    try:
        op.add_column('wallet_balances', sa.Column('balance_fiat', sa.Numeric(30,8), nullable=True))
    except Exception:
        pass


def downgrade():
    try:
        op.drop_column('transactions', 'price_fiat_in')
        op.drop_column('transactions', 'price_fiat_out')
    except Exception:
        pass

    try:
        op.drop_column('tax_records', 'gain_loss_fiat')
        op.drop_column('tax_records', 'cost_basis_fiat')
        op.drop_column('tax_records', 'proceeds_fiat')
    except Exception:
        pass

    try:
        op.drop_column('exchange_balances', 'total_fiat')
    except Exception:
        pass

    try:
        op.drop_column('exchange_trades', 'price_fiat')
        op.drop_column('exchange_trades', 'commission_fiat')
    except Exception:
        pass

    try:
        op.drop_column('exchange_deposits', 'amount_fiat')
    except Exception:
        pass

    try:
        op.drop_column('exchange_withdrawals', 'amount_fiat')
    except Exception:
        pass

    try:
        op.drop_column('wallet_balances', 'balance_fiat')
    except Exception:
        pass
