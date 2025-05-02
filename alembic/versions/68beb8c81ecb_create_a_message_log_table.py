"""create a message_log table.

Revision ID: 68beb8c81ecb
Revises: f86994803362
Create Date: 2025-04-29 12:08:16.504594

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '68beb8c81ecb'
down_revision = 'f86994803362'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ✅ Create only the message_logs table
    op.create_table(
        'message_logs',
        sa.Column('id', sa.INTEGER(), nullable=False),
        sa.Column('user_id', sa.INTEGER(), nullable=False),
        sa.Column('message_type', sa.VARCHAR(), nullable=False),
        sa.Column('recipient', sa.VARCHAR(), nullable=False),
        sa.Column('subject', sa.VARCHAR(), nullable=True),
        sa.Column('content', sa.TEXT(), nullable=False),
        sa.Column('status', sa.BOOLEAN(), nullable=True),
        sa.Column('created_at', sa.DATETIME(), nullable=False),
        sa.Column('updated_at', sa.DATETIME(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_message_logs_id', 'message_logs', ['id'], unique=False)


def downgrade() -> None:
    # ❌ Only remove the message_logs table (the one we added in upgrade)
    op.drop_index('ix_message_logs_id', table_name='message_logs')
    op.drop_table('message_logs')