"""user activity fields

Revision ID: 004_user_activity
Revises: 003_ramadan_and_events
Create Date: 2026-02-12
"""
from alembic import op
import sqlalchemy as sa


revision = "004_user_activity"
down_revision = "003_ramadan_and_events"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("full_name", sa.String(length=128)))
    op.add_column("users", sa.Column("last_active_at", sa.DateTime(timezone=True)))


def downgrade() -> None:
    op.drop_column("users", "last_active_at")
    op.drop_column("users", "full_name")
