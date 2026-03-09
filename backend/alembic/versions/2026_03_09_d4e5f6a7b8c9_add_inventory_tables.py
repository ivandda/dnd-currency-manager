"""add inventory tables

Revision ID: d4e5f6a7b8c9
Revises: c2d3e4f5a6b7
Create Date: 2026-03-09 16:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "d4e5f6a7b8c9"
down_revision: Union[str, None] = "c2d3e4f5a6b7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "inventoryitem",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("party_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("description_md", sa.String(length=10000), nullable=False, server_default=""),
        sa.Column("amount", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("owner_character_id", sa.Integer(), nullable=True),
        sa.Column("is_public", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_by_user_id", sa.Integer(), nullable=False),
        sa.Column("updated_by_user_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["party_id"], ["party.id"]),
        sa.ForeignKeyConstraint(["owner_character_id"], ["character.id"]),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["user.id"]),
        sa.ForeignKeyConstraint(["updated_by_user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_inventoryitem_party_id", "inventoryitem", ["party_id"])
    op.create_index("ix_inventoryitem_owner_character_id", "inventoryitem", ["owner_character_id"])
    op.create_index("ix_inventoryitem_updated_at", "inventoryitem", ["updated_at"])

    op.create_table(
        "inventoryevent",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("party_id", sa.Integer(), nullable=False),
        sa.Column("item_id", sa.Integer(), nullable=False),
        sa.Column(
            "event_type",
            sa.Enum(
                "ITEM_CREATED",
                "ITEM_UPDATED",
                "ITEM_AMOUNT_CHANGED",
                "ITEM_VISIBILITY_CHANGED",
                "ITEM_TRANSFERRED",
                "ITEM_DELETED",
                "ITEM_RESTORED",
                name="inventoryeventtype",
            ),
            nullable=False,
        ),
        sa.Column("actor_user_id", sa.Integer(), nullable=False),
        sa.Column("item_name_snapshot", sa.String(length=120), nullable=True),
        sa.Column("owner_character_id", sa.Integer(), nullable=True),
        sa.Column("old_owner_character_id", sa.Integer(), nullable=True),
        sa.Column("new_owner_character_id", sa.Integer(), nullable=True),
        sa.Column("old_amount", sa.Integer(), nullable=True),
        sa.Column("new_amount", sa.Integer(), nullable=True),
        sa.Column("old_is_public", sa.Boolean(), nullable=True),
        sa.Column("new_is_public", sa.Boolean(), nullable=True),
        sa.Column("is_public_snapshot", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("note", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["party_id"], ["party.id"]),
        sa.ForeignKeyConstraint(["item_id"], ["inventoryitem.id"]),
        sa.ForeignKeyConstraint(["actor_user_id"], ["user.id"]),
        sa.ForeignKeyConstraint(["owner_character_id"], ["character.id"]),
        sa.ForeignKeyConstraint(["old_owner_character_id"], ["character.id"]),
        sa.ForeignKeyConstraint(["new_owner_character_id"], ["character.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_inventoryevent_party_id", "inventoryevent", ["party_id"])
    op.create_index("ix_inventoryevent_item_id", "inventoryevent", ["item_id"])
    op.create_index("ix_inventoryevent_created_at", "inventoryevent", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_inventoryevent_created_at", table_name="inventoryevent")
    op.drop_index("ix_inventoryevent_item_id", table_name="inventoryevent")
    op.drop_index("ix_inventoryevent_party_id", table_name="inventoryevent")
    op.drop_table("inventoryevent")

    op.drop_index("ix_inventoryitem_updated_at", table_name="inventoryitem")
    op.drop_index("ix_inventoryitem_owner_character_id", table_name="inventoryitem")
    op.drop_index("ix_inventoryitem_party_id", table_name="inventoryitem")
    op.drop_table("inventoryitem")

    op.execute("DROP TYPE IF EXISTS inventoryeventtype")
