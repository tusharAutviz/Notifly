"""remove unique constraint from template table

Revision ID: 86cc085e9b9c
Revises: 7a3d32a92909
Create Date: 2025-05-05 16:40:33.735394

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '86cc085e9b9c'
down_revision = '7a3d32a92909'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop the existing templates table
    op.drop_table('templates')

    # Recreate the templates table with the updated definition
    op.create_table(
        'templates',
        sa.Column('id', sa.INTEGER(), primary_key=True),
        sa.Column('user_id', sa.INTEGER(), nullable=False),
        sa.Column('name', sa.VARCHAR(), nullable=False),
        sa.Column('content', sa.TEXT(), nullable=False),
        sa.Column('type', sa.VARCHAR(), nullable=True),
        sa.Column('subject', sa.VARCHAR(), nullable=True),
        sa.Column('created_at', sa.DATETIME(), nullable=False),
        sa.Column('updated_at', sa.DATETIME(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('name')
    )
    op.create_index('ix_templates_id', 'templates', ['id'], unique=False)


def downgrade() -> None:
    # Drop the templates table in downgrade
    op.drop_index('ix_templates_id', table_name='templates')
    op.drop_table('templates')

    # ### end Alembic commands ###



