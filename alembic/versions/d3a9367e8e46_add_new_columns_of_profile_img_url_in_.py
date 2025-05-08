"""add new columns of profile_img_url in user table

Revision ID: d3a9367e8e46
Revises: 9f5e49cb66f1
Create Date: 2025-05-06 19:25:51.398519

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd3a9367e8e46'
down_revision = '9f5e49cb66f1'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('user', sa.Column('profile_img_url', sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column('user', 'profile_img_url')