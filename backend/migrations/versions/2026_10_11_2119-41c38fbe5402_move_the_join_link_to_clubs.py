"""move the join link to clubs

Revision ID: 41c38fbe5402
Revises: f14f895a928a
Create Date: 2026-10-11 21:19:52.041961
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "41c38fbe5402"
down_revision: str | Sequence[str] | None = "f14f895a928a"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_constraint(op.f("uq_chat_accesses_invite_link"), "chat_accesses", type_="unique")
    op.drop_column("chat_accesses", "invite_link")
    op.add_column("clubs", sa.Column("chat_invite_link", sa.String(length=255), nullable=True))


def downgrade() -> None:
    op.drop_column("clubs", "chat_invite_link")
    # Personal links cannot be restored: without accesses the previous version invites everyone again.
    op.execute("DELETE FROM chat_accesses")
    op.add_column(
        "chat_accesses", sa.Column("invite_link", sa.VARCHAR(length=255), autoincrement=False, nullable=False)
    )
    op.create_unique_constraint(
        op.f("uq_chat_accesses_invite_link"), "chat_accesses", ["invite_link"], postgresql_nulls_not_distinct=False
    )
