"""Identity database models for migrations 0002 and 0003.

This module defines schema only. Authentication flows, token services, audit logs,
and role-assignment services are introduced in their approved later batches.
"""
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Index,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import INET, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from flask_login import UserMixin

from app.models.base import Base, PrimaryKeyMixin, PublicIdMixin, TimestampMixin


class User(UserMixin, PrimaryKeyMixin, PublicIdMixin, TimestampMixin, Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("email = lower(email)", name="email_lowercase"),
        CheckConstraint(
            "status IN ('active', 'suspended', 'disabled')",
            name="status_allowed",
        ),
        CheckConstraint("session_version >= 0", name="session_version_nonnegative"),
    )

    email: Mapped[str] = mapped_column(String(254), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, server_default=text("'active'")
    )
    status_changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    email_verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    session_version: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0")
    )

    @property
    def is_active(self) -> bool:
        return self.status == "active"

    @property
    def role_codes(self) -> set[str]:
        from sqlalchemy import select
        from app.extensions import db
        stmt = select(Role.code).join(UserRole, UserRole.role_id == Role.id).where(UserRole.user_id == self.id)
        return set(db.session.scalars(stmt).all())

    def has_role(self, *codes: str) -> bool:
        return bool(self.role_codes.intersection(codes))


class Role(PrimaryKeyMixin, Base):
    __tablename__ = "roles"
    __table_args__ = (
        CheckConstraint("code ~ '^[a-z_]+$'", name="code_format"),
    )

    code: Mapped[str] = mapped_column(String(40), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )


class Permission(PrimaryKeyMixin, Base):
    __tablename__ = "permissions"

    code: Mapped[str] = mapped_column(String(60), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )


class RolePermission(Base):
    __tablename__ = "role_permissions"

    role_id: Mapped[int] = mapped_column(
        ForeignKey("roles.id", ondelete="RESTRICT"), primary_key=True
    )
    permission_id: Mapped[int] = mapped_column(
        ForeignKey("permissions.id", ondelete="RESTRICT"), primary_key=True
    )


class UserRole(Base):
    __tablename__ = "user_roles"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), primary_key=True
    )
    role_id: Mapped[int] = mapped_column(
        ForeignKey("roles.id", ondelete="RESTRICT"), primary_key=True, index=True
    )
    granted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )

class AuthToken(PrimaryKeyMixin, Base):
    """Hashed, single-use tokens for password reset and email verification.

    Raw token values must never be persisted. Token issuance/consumption services
    are implemented in a later batch; this model only defines the approved schema.
    """

    __tablename__ = "auth_tokens"
    __table_args__ = (
        CheckConstraint(
            "purpose IN ('password_reset', 'email_verification')",
            name="purpose_allowed",
        ),
        CheckConstraint("expires_at > created_at", name="expiry_after_creation"),
        Index(
            "ix_auth_tokens_user_purpose_active",
            "user_id",
            "purpose",
            postgresql_where=text("used_at IS NULL AND revoked_at IS NULL"),
        ),
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    purpose: Mapped[str] = mapped_column(String(32), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class AuditRetentionPolicy(PrimaryKeyMixin, PublicIdMixin, Base):
    """Append-only, owner-approved audit retention policy."""

    __tablename__ = "audit_retention_policy"
    __table_args__ = (
        CheckConstraint("retention_days > 0", name="retention_days_positive"),
        CheckConstraint("length(trim(approver)) > 0", name="approver_nonempty"),
        CheckConstraint("length(trim(legal_basis)) > 0", name="legal_basis_nonempty"),
    )

    retention_days: Mapped[int] = mapped_column(Integer, nullable=False)
    approver: Mapped[str] = mapped_column(String(120), nullable=False)
    legal_basis: Mapped[str] = mapped_column(String(500), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )


class AuditLog(PrimaryKeyMixin, PublicIdMixin, Base):
    """Structured audit event schema; append-only enforcement is a later batch."""

    __tablename__ = "audit_logs"
    __table_args__ = (
        CheckConstraint(
            "actor_user_id IS NOT NULL OR actor_label IS NOT NULL",
            name="actor_present",
        ),
        Index("ix_audit_logs_entity_created", "entity_type", "entity_id", "created_at"),
        Index("ix_audit_logs_actor_created", "actor_user_id", "created_at"),
        Index("ix_audit_logs_action_created", "action", "created_at"),
    )

    actor_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=True
    )
    actor_label: Mapped[str | None] = mapped_column(String(80), nullable=True)
    action: Mapped[str] = mapped_column(String(80), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(40), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(64), nullable=False)
    before_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    after_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    event_metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(INET, nullable=True)
    request_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
