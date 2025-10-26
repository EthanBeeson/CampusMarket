"""Add profile fields to users

Revision ID: 0002_add_profile_fields_to_users
Revises: 0001_add_condition_to_listings
Create Date: 2025-10-26
"""

# revision identifiers, used by Alembic.
revision = '0002_add_profile_fields_to_users'
down_revision = '0001_add_condition_to_listings'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('users', sa.Column('full_name', sa.String(length=100), nullable=True))
    op.add_column('users', sa.Column('display_name', sa.String(length=50), nullable=True))
    op.add_column('users', sa.Column('phone', sa.String(length=20), nullable=True))
    op.add_column('users', sa.Column('bio', sa.String(length=500), nullable=True))
    op.add_column('users', sa.Column('profile_picture', sa.String(length=255), nullable=True))


def downgrade():
    op.drop_column('users', 'profile_picture')
    op.drop_column('users', 'bio')
    op.drop_column('users', 'phone')
    op.drop_column('users', 'display_name')
    op.drop_column('users', 'full_name')
