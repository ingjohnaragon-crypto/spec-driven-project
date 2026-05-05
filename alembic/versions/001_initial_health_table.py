"""Initial health table

Revision ID: 001_initial_health_table
Revises: None
Create Date: 2026-05-05 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
import sqlalchemy.dialects.postgresql as pg

revision = "001_initial_health_table"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "health",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("service_name", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("version", sa.String(length=50), nullable=False),
        sa.Column("uptime_seconds", sa.Integer(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("health")
