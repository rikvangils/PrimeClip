"""Add fan_account_disclosed to compliance_audit

Revision ID: 002_add_fan_account_disclosed
Revises: 001_initial_schema
Create Date: 2026-03-19 00:00:00
"""

from alembic import op
import sqlalchemy as sa


revision = "002_add_fan_account_disclosed"
down_revision = "001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "compliance_audit",
        sa.Column(
            "fan_account_disclosed",
            sa.Boolean(),
            nullable=False,
            server_default="false",
        ),
    )


def downgrade() -> None:
    op.drop_column("compliance_audit", "fan_account_disclosed")
