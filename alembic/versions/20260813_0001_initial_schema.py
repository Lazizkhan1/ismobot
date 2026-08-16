"""initial schema

Revision ID: 20260813_0001
Revises:
Create Date: 2026-08-13
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260813_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    existing_tables = set(inspector.get_table_names())
    print(f"Existing tables: {existing_tables}")
    if "users" not in existing_tables:
        op.create_table(
            "users",
            sa.Column("id", sa.BigInteger(), primary_key=True),
            sa.Column("username", sa.String(length=255), nullable=True),
            sa.Column("lang", sa.String(length=3), nullable=True),
            sa.Column("user_type", sa.Integer(), nullable=True),
        )
        existing_tables.add("users")

    if "categories" not in existing_tables:
        op.create_table(
            "categories",
            sa.Column("id", sa.BigInteger(), primary_key=True),
            sa.Column("name", sa.String(length=255), nullable=True),
            sa.Column("deleted_at", sa.DateTime(), nullable=True),
        )
        existing_tables.add("categories")

    if "orders" not in existing_tables:
        op.create_table(
            "orders",
            sa.Column("id", sa.BigInteger(), primary_key=True),
            sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.id"), nullable=True),
            sa.Column("moderator_id", sa.BigInteger(), nullable=True),
            sa.Column("category_id", sa.Integer(), sa.ForeignKey("categories.id"), nullable=True),
            sa.Column("ceremony_date", sa.Date(), nullable=True),
            sa.Column("video_note_id", sa.String(length=255), nullable=True),
            sa.Column("cheque_id", sa.String(length=255), nullable=True),
            sa.Column("status", sa.Integer(), server_default=sa.text("0"), nullable=True),
            sa.Column("cancel_reason", sa.String(length=255), nullable=True),
            sa.Column("canceled_at", sa.DateTime(), nullable=True),
            sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_DATE"), nullable=True),
        )
        existing_tables.add("orders")

    if "order_photos" not in existing_tables:
        op.create_table(
            "order_photos",
            sa.Column("id", sa.BigInteger(), primary_key=True),
            sa.Column("order_id", sa.Integer(), sa.ForeignKey("orders.id"), nullable=True),
            sa.Column("photo_id", sa.String(), nullable=True),
        )

    if "categories" in existing_tables:
        op.execute(
            "INSERT INTO categories (name) SELECT 'SARBON' "
            "WHERE NOT EXISTS (SELECT 1 FROM categories WHERE name = 'SARBON')"
        )


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    existing_tables = set(inspector.get_table_names())

    if "order_photos" in existing_tables:
        op.drop_table("order_photos")
    if "orders" in existing_tables:
        op.drop_table("orders")
    if "categories" in existing_tables:
        op.drop_table("categories")
    if "users" in existing_tables:
        op.drop_table("users")
