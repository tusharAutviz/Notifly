"""add sid column in message_log table

Revision ID: 0fcd1dcec190
Revises: 8f09efe7eda8
Create Date: 2025-05-05 18:39:58.458042

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0fcd1dcec190'
down_revision = '8f09efe7eda8'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ... existing drop statements
    op.add_column('message_logs', sa.Column('sid', sa.VARCHAR(), nullable=True))

def downgrade() -> None:
    # ... existing create table statements
    op.drop_column('message_logs', 'sid')