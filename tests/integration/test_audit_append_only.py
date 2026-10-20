"""PostgreSQL integration tests for Revision 6 audit protections."""
import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from app.extensions import db
from flask_migrate import upgrade


def _upgrade(app):
    with app.app_context():
        upgrade()


def _insert_audit_row(connection, action="identity.test", created_at="now()"):
    return connection.execute(text(f"""
        INSERT INTO audit_logs (actor_label, action, entity_type, entity_id, created_at)
        VALUES ('test-suite', :action, 'test', 'entity-1', {created_at})
        RETURNING id
    """), {"action": action}).scalar_one()


def test_audit_rows_reject_update_delete_and_truncate_without_policy(app, clean_db):
    _upgrade(app)
    with app.app_context(), db.engine.connect() as connection:
        _insert_audit_row(connection)
        connection.commit()

        for statement in (
            "UPDATE audit_logs SET action = 'changed'",
            "DELETE FROM audit_logs",
            "TRUNCATE audit_logs",
        ):
            transaction = connection.begin()
            with pytest.raises(DBAPIError):
                connection.execute(text(statement))
            transaction.rollback()

        # No policy exists and the current database role is not an authorized
        # maintenance operator, so deletion must be refused.
        transaction = connection.begin()
        with pytest.raises(DBAPIError):
            connection.execute(text("DELETE FROM audit_logs"))
        transaction.rollback()


def test_recorder_only_actions_cannot_be_forged_by_direct_insert(app, clean_db):
    _upgrade(app)
    with app.app_context(), db.engine.connect() as connection:
        for action in ("audit.maintenance_run", "audit.retention_policy_approved"):
            transaction = connection.begin()
            with pytest.raises(DBAPIError):
                connection.execute(text("""
                    INSERT INTO audit_logs (actor_label, action, entity_type, entity_id)
                    VALUES ('forger', :action, 'test', 'entity-1')
                """), {"action": action})
            transaction.rollback()

        # Ordinary audit events remain insertable.
        with connection.begin():
            _insert_audit_row(connection)


def test_retention_policy_validates_and_approval_is_audited(app, clean_db):
    _upgrade(app)
    with app.app_context(), db.engine.connect() as connection:
        for values in ((0, "approver", "legal basis"), (5, "   ", "legal basis"), (5, "approver", "  ")):
            transaction = connection.begin()
            with pytest.raises(DBAPIError):
                connection.execute(text("""
                    INSERT INTO audit_retention_policy (retention_days, approver, legal_basis)
                    VALUES (:days, :approver, :basis)
                """), {"days": values[0], "approver": values[1], "basis": values[2]})
            transaction.rollback()

        with connection.begin():
            connection.execute(text("""
                INSERT INTO audit_retention_policy (retention_days, approver, legal_basis)
                VALUES (365, 'authorized policy owner', 'approved retention basis for test')
            """))
        row = connection.execute(text("""
            SELECT action, actor_label, after_data->>'retention_days' AS days
            FROM audit_logs WHERE action = 'audit.retention_policy_approved'
        """)).one()
        assert row.action == "audit.retention_policy_approved"
        assert row.actor_label == "authorized policy owner"
        assert row.days == "365"
        connection.commit()

        for statement in (
            "UPDATE audit_retention_policy SET retention_days = 1",
            "DELETE FROM audit_retention_policy",
            "TRUNCATE audit_retention_policy",
        ):
            transaction = connection.begin()
            with pytest.raises(DBAPIError):
                connection.execute(text(statement))
            transaction.rollback()
