"""Add condition column to listings

Revision ID: 0001_add_condition_to_listings
Revises: None
Create Date: 2025-10-26
"""

# revision identifiers, used by Alembic.
revision = '0001_add_condition_to_listings'
down_revision = None
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    # Add 'condition' column with a server default of 'Good' so existing rows get a value.
    op.add_column('listings', sa.Column('condition', sa.String(length=20), nullable=False, server_default=sa.text("'Good'")))


def downgrade():
    # Remove the 'condition' column on downgrade
    op.drop_column('listings', 'condition')
