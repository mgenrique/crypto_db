"""add price mapping and cache tables

Revision ID: 0006_price_mapping_and_cache
Revises: 0005_add_fiat_columns
Create Date: 2025-12-03 01:05:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0006_price_mapping_and_cache'
down_revision = '0005_add_fiat_columns'
branch_labels = None
depends_on = None


def upgrade():
    try:
        op.create_table(
            'price_mappings',
            sa.Column('id', sa.Integer, primary_key=True),
            sa.Column('symbol', sa.String(50), nullable=True),
            sa.Column('network', sa.String(50), nullable=True),
            sa.Column('contract_address', sa.String(255), nullable=True),
            sa.Column('coingecko_id', sa.String(255), nullable=False),
            sa.Column('source', sa.String(50), nullable=True),
            sa.Column('created_at', sa.DateTime, nullable=True),
        )
        op.create_index('idx_price_mapping_symbol', 'price_mappings', ['symbol'])
        op.create_index('idx_price_mapping_contract', 'price_mappings', ['contract_address'])
    except Exception:
        pass

    try:
        op.create_table(
            'price_cache',
            sa.Column('id', sa.Integer, primary_key=True),
            sa.Column('coingecko_id', sa.String(255), nullable=False),
            sa.Column('vs_currency', sa.String(10), nullable=False),
            sa.Column('ts_minute', sa.Integer, nullable=False),
            sa.Column('price', sa.Numeric(40, 18), nullable=True),
            sa.Column('fetched_at', sa.DateTime, nullable=True),
        )
        op.create_index('idx_pricecache_cg_vs', 'price_cache', ['coingecko_id', 'vs_currency'])
        op.create_index('idx_pricecache_ts', 'price_cache', ['ts_minute'])
    except Exception:
        pass


def downgrade():
    try:
        op.drop_index('idx_price_mapping_symbol', table_name='price_mappings')
    except Exception:
        pass
    try:
        op.drop_index('idx_price_mapping_contract', table_name='price_mappings')
    except Exception:
        pass
    try:
        op.drop_table('price_mappings')
    except Exception:
        pass

    try:
        op.drop_index('idx_pricecache_cg_vs', table_name='price_cache')
    except Exception:
        pass
    try:
        op.drop_index('idx_pricecache_ts', table_name='price_cache')
    except Exception:
        pass
    try:
        op.drop_table('price_cache')
    except Exception:
        pass
