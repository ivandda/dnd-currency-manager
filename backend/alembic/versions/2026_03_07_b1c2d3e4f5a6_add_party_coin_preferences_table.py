"""add party coin preferences table

Revision ID: b1c2d3e4f5a6
Revises: 6ad51bea90cb
Create Date: 2026-03-07 16:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b1c2d3e4f5a6"
down_revision: Union[str, None] = "6ad51bea90cb"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "partycoinpreference",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("party_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("use_gold", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("use_electrum", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("use_platinum", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["party_id"], ["party.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("party_id", "user_id", name="uq_party_coin_preference_party_user"),
    )
    op.create_index("ix_partycoinpreference_party_id", "partycoinpreference", ["party_id"])
    op.create_index("ix_partycoinpreference_user_id", "partycoinpreference", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_partycoinpreference_user_id", table_name="partycoinpreference")
    op.drop_index("ix_partycoinpreference_party_id", table_name="partycoinpreference")
    op.drop_table("partycoinpreference")
