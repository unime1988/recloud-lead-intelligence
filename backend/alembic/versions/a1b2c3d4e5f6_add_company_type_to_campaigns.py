"""add company_type to campaigns

Revision ID: a1b2c3d4e5f6
Revises: 305114eba5df
Create Date: 2026-06-09 14:30:00.000000
"""

from alembic import op
import sqlalchemy as sa

revision = "a1b2c3d4e5f6"
down_revision = "305114eba5df"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "campaigns",
        sa.Column("company_type", sa.String(64), nullable=False, server_default="all"),
    )


def downgrade() -> None:
    op.drop_column("campaigns", "company_type")
