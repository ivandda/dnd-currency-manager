"""add spend and self_add transaction types

Revision ID: a1b2c3d4e5f6
Revises: 69db3ef09e66
Create Date: 2026-03-05 02:20:00.000000

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '69db3ef09e66'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add new enum values to transactiontype (SQLAlchemy uses enum .name = uppercase)
    op.execute("ALTER TYPE transactiontype ADD VALUE IF NOT EXISTS 'SPEND'")
    op.execute("ALTER TYPE transactiontype ADD VALUE IF NOT EXISTS 'SELF_ADD'")


def downgrade() -> None:
    # PostgreSQL does not support removing enum values directly.
    # A full enum recreation would be needed, which is complex.
    pass
