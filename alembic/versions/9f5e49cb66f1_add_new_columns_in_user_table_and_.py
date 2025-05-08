"""add new columns in user table and create new subject table

Revision ID: 9f5e49cb66f1
Revises: 0fcd1dcec190
Create Date: 2025-05-06 17:58:04.343429

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9f5e49cb66f1'
down_revision = '0fcd1dcec190'
branch_labels = None
depends_on = None


def upgrade() -> None:

    # Add 'role' and 'about' columns to user table
    op.add_column('user', sa.Column('role', sa.String(), nullable=True))
    op.add_column('user', sa.Column('about', sa.Text(), nullable=True))


def downgrade() -> None:
    # Drop 'role' and 'about' columns from user table
    op.drop_column('user', 'role')
    op.drop_column('user', 'about')