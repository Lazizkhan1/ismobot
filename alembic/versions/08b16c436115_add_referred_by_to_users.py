"""add referred_by to users

Revision ID: 08b16c436115
Revises: 5dd8085b0a39
Create Date: 2026-11-01 03:11:18.159610
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = '08b16c436115'
down_revision: str | None = '5dd8085b0a39'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        'users',
        sa.Column('referred_by', sa.BigInteger(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    )


def downgrade() -> None:
    op.drop_column('users', 'referred_by')
