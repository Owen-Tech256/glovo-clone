import uuid
from datetime import datetime, timezone

import pytest
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from flask_migrate import downgrade, upgrade
from sqlalchemy import MetaData, create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

from app.extensions import db
from app.models import NAMING_CONVENTION, Base, PrimaryKeyMixin, PublicIdMixin, TimestampMixin


def version_rows(app):
    with app.app_context():
        rows = db.session.execute(text("SELECT version_num FROM alembic_version")).scalars().all()
        db.session.rollback()
        return rows


# F-20
def test_upgrade_head_on_empty_database(app, clean_db):
    with app.app_context():
        upgrade()
    assert version_rows(app) == ["0006"]


# F-21
def test_downgrade_then_upgrade_round_trips(app, clean_db):
    with app.app_context():
        upgrade()
        downgrade(revision="base")
    assert version_rows(app) == []
    with app.app_context():
        upgrade()
    assert version_rows(app) == ["0006"]


# F-22
def test_no_pending_model_changes(app, clean_db):
    with app.app_context():
        upgrade()
        with db.engine.connect() as conn:
            context = MigrationContext.configure(conn, opts={"compare_type": True})
            assert compare_metadata(context, db.metadata) == []


# F-23
def test_metadata_uses_the_approved_naming_convention(app):
    assert db.metadata.naming_convention == NAMING_CONVENTION
    assert Base.metadata is db.metadata
    assert NAMING_CONVENTION["pk"] == "pk_%(table_name)s"


# F-35: mixins work on real PostgreSQL. Uses a private base so app metadata is untouched.
class ProbeBase(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)


class ProbeWidget(PrimaryKeyMixin, PublicIdMixin, TimestampMixin, ProbeBase):
    __tablename__ = "probe_widgets"
    label: Mapped[str] = mapped_column(nullable=False)


def test_mixins_create_identity_key_public_uuid_and_utc_timestamps(clean_db):
    engine = create_engine(clean_db)
    try:
        ProbeBase.metadata.create_all(engine)
        inspector = inspect(engine)
        assert inspector.get_pk_constraint("probe_widgets")["name"] == "pk_probe_widgets"
        unique_names = {c["name"] for c in inspector.get_unique_constraints("probe_widgets")}
        assert "uq_probe_widgets_public_id" in unique_names

        with Session(engine) as session:
            via_orm = ProbeWidget(label="orm")
            session.add(via_orm)
            session.flush()
            session.execute(text("INSERT INTO probe_widgets (label) VALUES ('raw')"))
            session.commit()
            rows = session.query(ProbeWidget).order_by(ProbeWidget.id).all()
            assert [r.label for r in rows] == ["orm", "raw"]
            assert isinstance(rows[0].id, int) and rows[1].id > rows[0].id
            assert all(isinstance(r.public_id, uuid.UUID) for r in rows)
            assert rows[0].public_id != rows[1].public_id
            for row in rows:
                assert row.created_at.tzinfo is not None
                assert abs((datetime.now(timezone.utc) - row.created_at).total_seconds()) < 60
    finally:
        ProbeBase.metadata.drop_all(engine)
        engine.dispose()
