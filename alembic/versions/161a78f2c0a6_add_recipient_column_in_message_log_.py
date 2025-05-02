"""add recipient_column in message_log table.

Revision ID: 161a78f2c0a6
Revises: a345791ff8ee
Create Date: 2025-05-01 11:37:13.468842

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '161a78f2c0a6'
down_revision = 'a345791ff8ee'
branch_labels = None
depends_on = None


def upgrade():
    # Add a new column `recipient_name` to `message_logs` table
    op.add_column('message_logs', sa.Column('recipient_name', sa.String(), nullable=False, server_default=''))


def downgrade():
    # Remove the `recipient_name` column if downgrading
    op.drop_column('message_logs', 'recipient_name')