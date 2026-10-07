"""add roles and admin sessions

Revision ID: d67170e06673
Revises: 03e97a1dbdb9
Create Date: 2026-10-07 18:19:56.065052
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "d67170e06673"
down_revision: str | Sequence[str] | None = "03e97a1dbdb9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "roles",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("title", sa.String(length=64), nullable=False),
        sa.Column("permissions", postgresql.ARRAY(sa.String(length=64)), server_default="{}", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_roles")),
        sa.UniqueConstraint("title", name=op.f("uq_roles_title")),
    )
    op.create_table(
        "admin_sessions",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("admin_user_id", sa.BigInteger(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["admin_user_id"],
            ["admin_users.id"],
            name=op.f("fk_admin_sessions_admin_user_id_admin_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_admin_sessions")),
        sa.UniqueConstraint("token_hash", name=op.f("uq_admin_sessions_token_hash")),
    )
    op.create_index(op.f("ix_admin_sessions_admin_user_id"), "admin_sessions", ["admin_user_id"], unique=False)
    op.create_table(
        "login_codes",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("code_hash", sa.String(length=64), nullable=False),
        sa.Column("admin_user_id", sa.BigInteger(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["admin_user_id"],
            ["admin_users.id"],
            name=op.f("fk_login_codes_admin_user_id_admin_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_login_codes")),
    )
    op.create_index(op.f("ix_login_codes_admin_user_id"), "login_codes", ["admin_user_id"], unique=False)
    op.create_index(op.f("ix_login_codes_code_hash"), "login_codes", ["code_hash"], unique=False)
    op.add_column("admin_users", sa.Column("role_id", sa.BigInteger(), nullable=True))
    op.alter_column(
        "admin_users",
        "name",
        existing_type=sa.VARCHAR(length=100),
        type_=sa.String(length=129),
        existing_nullable=False,
    )
    op.create_index(op.f("ix_admin_users_role_id"), "admin_users", ["role_id"], unique=False)
    op.create_foreign_key(
        op.f("fk_admin_users_role_id_roles"), "admin_users", "roles", ["role_id"], ["id"], ondelete="RESTRICT"
    )
    op.drop_column("admin_users", "role")


def downgrade() -> None:
    # Former admins had full access, so "admin" is the closest restore for the dropped enum column.
    op.add_column("admin_users", sa.Column("role", sa.VARCHAR(length=32), server_default="admin", nullable=False))
    op.drop_constraint(op.f("fk_admin_users_role_id_roles"), "admin_users", type_="foreignkey")
    op.drop_index(op.f("ix_admin_users_role_id"), table_name="admin_users")
    op.alter_column(
        "admin_users",
        "name",
        existing_type=sa.String(length=129),
        type_=sa.VARCHAR(length=100),
        existing_nullable=False,
    )
    op.drop_column("admin_users", "role_id")
    op.drop_index(op.f("ix_login_codes_code_hash"), table_name="login_codes")
    op.drop_index(op.f("ix_login_codes_admin_user_id"), table_name="login_codes")
    op.drop_table("login_codes")
    op.drop_index(op.f("ix_admin_sessions_admin_user_id"), table_name="admin_sessions")
    op.drop_table("admin_sessions")
    op.drop_table("roles")
