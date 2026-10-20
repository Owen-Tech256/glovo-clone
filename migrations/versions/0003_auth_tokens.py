"""Hashed, single-use password reset and email verification tokens.

Revision ID: 0003
Revises: 0002
"""
from alembic import op
import sqlalchemy as sa

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "auth_tokens",
        sa.Column("id", sa.Integer(), sa.Identity(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("purpose", sa.String(length=32), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "purpose IN ('password_reset', 'email_verification')",
            name=op.f("ck_auth_tokens_purpose_allowed"),
        ),
        sa.CheckConstraint(
            "expires_at > created_at",
            name=op.f("ck_auth_tokens_expiry_after_creation"),
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"],
            name=op.f("fk_auth_tokens_user_id_users"), ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_auth_tokens")),
        sa.UniqueConstraint("token_hash", name=op.f("uq_auth_tokens_token_hash")),
    )
    # PostgreSQL cannot use now() in a partial-index predicate because it is not
    # immutable. Used/revoked tokens are excluded; expiration is checked in queries.
    op.create_index(
        "ix_auth_tokens_user_purpose_active",
        "auth_tokens",
        ["user_id", "purpose"],
        unique=False,
        postgresql_where=sa.text("used_at IS NULL AND revoked_at IS NULL"),
    )


def downgrade():
    op.drop_index("ix_auth_tokens_user_purpose_active", table_name="auth_tokens")
    op.drop_table("auth_tokens")
