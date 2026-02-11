"""user silent hours and hijri reminder

Revision ID: 002_user_silent_hijri
Revises: 001_initial
Create Date: 2026-02-11
"""
from alembic import op
import sqlalchemy as sa


revision = "002_user_silent_hijri"
down_revision = "001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("silent_start", sa.String(length=5)))
    op.add_column("users", sa.Column("silent_end", sa.String(length=5)))
    op.add_column(
        "users",
        sa.Column("hijri_reminder_on", sa.Boolean, nullable=False, server_default=sa.text("false")),
    )
    op.add_column("users", sa.Column("last_hijri_month", sa.Integer))
    op.add_column("users", sa.Column("last_hijri_year", sa.Integer))


def downgrade() -> None:
    op.drop_column("users", "last_hijri_year")
    op.drop_column("users", "last_hijri_month")
    op.drop_column("users", "hijri_reminder_on")
    op.drop_column("users", "silent_end")
    op.drop_column("users", "silent_start")
