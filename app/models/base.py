"""Declarative base, naming convention and reusable column mixins.

The naming convention must exist before the first migration so Alembic can
create and drop constraints by predictable names. PostgreSQL truncates
identifiers at 63 characters, so keep table and column names short.
"""
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Identity, Integer, MetaData, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)


class PrimaryKeyMixin:
    """Internal integer identity key. Never expose it in URLs or responses."""

    id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True)


class PublicIdMixin:
    """Public UUID for records that need an external identifier.

    A UUID is an identifier, not an authorization check. Ownership and
    permission checks are still required on every request.
    """

    public_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        unique=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )


class TimestampMixin:
    """UTC timestamps (timestamptz). Display timezone is a separate, pending decision."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
