"""add club status sheet

Revision ID: c4e88cbf5828
Revises: 4f6668e59f9f
Create Date: 2026-11-07 01:16:24.025005
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c4e88cbf5828"
down_revision: str | Sequence[str] | None = "4f6668e59f9f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("clubs", sa.Column("status_sheet_name", sa.String(length=100), nullable=True))


def downgrade() -> None:
    op.drop_column("clubs", "status_sheet_name")
