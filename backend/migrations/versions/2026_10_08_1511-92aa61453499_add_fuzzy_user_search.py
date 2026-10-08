"""add fuzzy user search

Revision ID: 92aa61453499
Revises: d67170e06673
Create Date: 2026-10-08 15:11:34.665258
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "92aa61453499"
down_revision: str | Sequence[str] | None = "d67170e06673"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # pg_trgm is a trusted extension (PG 13+), so the database owner can create it without superuser rights.
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    op.add_column(
        "users",
        sa.Column(
            "search_text",
            sa.Text(),
            sa.Computed("lower(translate(full_name || ' ' || coalesce(tg_username, ''), 'Ёё', 'Ее'))", persisted=True),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_users_search_text",
        "users",
        ["search_text"],
        unique=False,
        postgresql_using="gin",
        postgresql_ops={"search_text": "gin_trgm_ops"},
    )


def downgrade() -> None:
    op.drop_index(
        "ix_users_search_text",
        table_name="users",
        postgresql_using="gin",
        postgresql_ops={"search_text": "gin_trgm_ops"},
    )
    op.drop_column("users", "search_text")
    op.execute("DROP EXTENSION IF EXISTS pg_trgm")
