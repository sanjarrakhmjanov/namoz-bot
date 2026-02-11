"""initial

Revision ID: 001_initial
Revises: 
Create Date: 2026-02-11
"""
from alembic import op
import sqlalchemy as sa


revision = "001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("telegram_id", sa.BigInteger, nullable=False, unique=True),
        sa.Column("username", sa.String(length=64)),
        sa.Column("lang", sa.String(length=8), nullable=False, server_default="uz"),
        sa.Column("city", sa.String(length=64)),
        sa.Column("lat", sa.Float),
        sa.Column("lon", sa.Float),
        sa.Column("timezone", sa.String(length=64)),
        sa.Column("time_offset_min", sa.Integer, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_users_telegram_id", "users", ["telegram_id"], unique=True)

    op.create_table(
        "reminders",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id"), unique=True),
        sa.Column("fajr_on", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("dhuhr_on", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("asr_on", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("maghrib_on", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("isha_on", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("offset_min", sa.Integer, nullable=False, server_default="10"),
        sa.Column("enabled", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "tasbeh",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id"), unique=True),
        sa.Column("count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("goal", sa.Integer, nullable=False, server_default="33"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("tasbeh")
    op.drop_table("reminders")
    op.drop_index("ix_users_telegram_id", table_name="users")
    op.drop_table("users")
