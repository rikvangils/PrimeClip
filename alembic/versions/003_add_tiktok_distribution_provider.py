"""Add tiktok distribution provider enum value

Revision ID: 003_add_tiktok_distribution_provider
Revises: 002_add_fan_account_disclosed
Create Date: 2026-03-19 00:30:00
"""

from alembic import op


revision = "003_add_tiktok_distribution_provider"
down_revision = "002_add_fan_account_disclosed"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TYPE distribution_provider_enum ADD VALUE IF NOT EXISTS 'tiktok'")


def downgrade() -> None:
    # PostgreSQL does not support removing enum values in-place.
    # Keep downgrade as no-op to preserve existing data compatibility.
    pass
