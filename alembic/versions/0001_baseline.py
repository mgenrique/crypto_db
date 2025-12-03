"""baseline

Revision ID: 0001_baseline
Revises: 
Create Date: 2025-12-03 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0001_baseline'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Baseline revision: database was created manually; no actions.
    pass


def downgrade():
    # No-op downgrade for baseline
    pass
