"""add subject column in template table.

Revision ID: 4a0812ab8b1a
Revises: e5ca6b282b64
Create Date: 2025-04-29 12:42:28.263939

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4a0812ab8b1a'
down_revision = 'e5ca6b282b64'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ✅ Add only the new column
    op.add_column('templates', sa.Column('subject', sa.String(), nullable=True))

def downgrade() -> None:
    # ✅ Remove only the added column
    op.drop_column('templates', 'subject')