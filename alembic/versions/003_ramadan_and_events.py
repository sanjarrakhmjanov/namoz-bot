"""ramadan fields and reminder events

Revision ID: 003_ramadan_and_events
Revises: 002_user_silent_hijri
Create Date: 2026-02-11
"""
from alembic import op
import sqlalchemy as sa


revision = "003_ramadan_and_events"
down_revision = "002_user_silent_hijri"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("ramadan_on", sa.Boolean, nullable=False, server_default=sa.text("false")),
    )
    op.add_column(
        "users",
        sa.Column("suhoor_offset_min", sa.Integer, nullable=False, server_default="-30"),
    )
    op.add_column(
        "users",
        sa.Column("iftar_offset_min", sa.Integer, nullable=False, server_default="0"),
    )
    op.create_table(
        "reminder_events",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id"), index=True),
        sa.Column("event_type", sa.String(length=24), nullable=False),
        sa.Column("prayer_key", sa.String(length=16)),
        sa.Column("sent_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("reminder_events")
    op.drop_column("users", "iftar_offset_min")
    op.drop_column("users", "suhoor_offset_min")
    op.drop_column("users", "ramadan_on")
