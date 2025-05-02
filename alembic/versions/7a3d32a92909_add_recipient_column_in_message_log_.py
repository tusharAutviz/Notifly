"""add recipient_column in message_log table.

Revision ID: 7a3d32a92909
Revises: 161a78f2c0a6
Create Date: 2025-05-01 11:43:11.607401

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7a3d32a92909'
down_revision = '161a78f2c0a6'
branch_labels = None
depends_on = None


def upgrade():
    # Drop the existing table
    op.drop_table('message_logs')

    # Recreate the updated table
    op.create_table(
        'message_logs',
        sa.Column('id', sa.Integer, primary_key=True, nullable=False),
        sa.Column('user_id', sa.Integer, sa.ForeignKey('user.id', ondelete='CASCADE'), nullable=False),
        sa.Column('message_type', sa.String, nullable=False),
        sa.Column('recipient', sa.String, nullable=False),
        sa.Column('recipient_name', sa.String, nullable=False),
        sa.Column('subject', sa.String, nullable=True),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('status', sa.Boolean, default=False),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime, nullable=False),
    )

    # Create indexes
    op.create_index('ix_message_logs_id', 'message_logs', ['id'], unique=False)
    op.create_index('ix_message_logs_recipient', 'message_logs', ['recipient'], unique=False)
    op.create_index('ix_message_logs_recipient_name', 'message_logs', ['recipient_name'], unique=False)
    op.create_index('ix_message_logs_status', 'message_logs', ['status'], unique=False)


def downgrade():
    op.drop_index('ix_message_logs_status', table_name='message_logs')
    op.drop_index('ix_message_logs_recipient_name', table_name='message_logs')
    op.drop_index('ix_message_logs_recipient', table_name='message_logs')
    op.drop_index('ix_message_logs_id', table_name='message_logs')
    op.drop_table('message_logs')
    # ### end Alembic commands ###
