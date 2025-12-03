"""remove users and api_keys tables

Revision ID: 0007_remove_user_tables
Revises: 0006_price_mapping_and_cache
Create Date: 2025-12-03 01:30:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0007_remove_user_tables'
down_revision = '0006_price_mapping_and_cache'
branch_labels = None
depends_on = None


def upgrade():
    # Drop API key and user tables if present. Safe to run on empty DB.
    try:
        op.drop_table('api_keys')
    except Exception:
        pass

    try:
        op.drop_table('users')
    except Exception:
        pass


def downgrade():
    # Re-create minimal user and api_keys tables in downgrade to restore previous schema
    try:
        op.create_table(
            'users',
            sa.Column('id', sa.Integer, primary_key=True),
            sa.Column('email', sa.String(255), nullable=False),
            sa.Column('username', sa.String(100), nullable=False),
            sa.Column('hashed_password', sa.String(255), nullable=False),
            sa.Column('is_active', sa.Boolean, default=True),
            sa.Column('is_admin', sa.Boolean, default=False),
            sa.Column('created_at', sa.DateTime, nullable=True),
        )
    except Exception:
        pass

    try:
        op.create_table(
            'api_keys',
            sa.Column('id', sa.Integer, primary_key=True),
            sa.Column('user_id', sa.Integer, nullable=False),
            sa.Column('key', sa.String(255), nullable=False),
            sa.Column('secret', sa.String(255), nullable=False),
            sa.Column('name', sa.String(100), nullable=False),
            sa.Column('is_active', sa.Boolean, default=True),
            sa.Column('created_at', sa.DateTime, nullable=True),
        )
    except Exception:
        pass
