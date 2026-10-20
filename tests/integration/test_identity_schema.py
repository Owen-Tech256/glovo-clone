"""PostgreSQL integration tests for Identity migrations 0002 and 0003."""
import pytest
from sqlalchemy import inspect, text
from sqlalchemy.exc import IntegrityError
from flask_migrate import upgrade

from app.extensions import db


def _upgrade(app):
    with app.app_context():
        upgrade()


def test_identity_migration_creates_approved_tables_and_constraints(app, clean_db):
    _upgrade(app)

    with app.app_context():
        inspector = inspect(db.engine)
        tables = set(inspector.get_table_names())
        assert {
            "users",
            "roles",
            "permissions",
            "role_permissions",
            "user_roles",
            "auth_tokens",
            "audit_logs",
            "audit_retention_policy",
            "customer_profiles", "service_zones", "vendor_profiles", "products",
            "cart_items", "orders", "order_items", "deliveries", "payments",
            "support_tickets", "promotions", "rider_applications",
            "alembic_version",
        } <= tables

        user_columns = {column["name"] for column in inspector.get_columns("users")}
        assert {
            "id",
            "public_id",
            "email",
            "password_hash",
            "status",
            "status_changed_at",
            "email_verified_at",
            "last_login_at",
            "session_version",
            "created_at",
            "updated_at",
        } <= user_columns
        assert "phone" not in user_columns

        user_unique = {
            constraint["name"]
            for constraint in inspector.get_unique_constraints("users")
        }
        assert {"uq_users_email", "uq_users_public_id"} <= user_unique

        user_checks = {
            constraint["name"]
            for constraint in inspector.get_check_constraints("users")
        }
        assert {
            "ck_users_email_lowercase",
            "ck_users_status_allowed",
            "ck_users_session_version_nonnegative",
        } <= user_checks

        user_role_fks = inspector.get_foreign_keys("user_roles")
        assert {fk["options"].get("ondelete") for fk in user_role_fks} == {"RESTRICT"}
        role_permission_fks = inspector.get_foreign_keys("role_permissions")
        assert {
            fk["options"].get("ondelete") for fk in role_permission_fks
        } == {"RESTRICT"}

        user_role_indexes = {
            index["name"] for index in inspector.get_indexes("user_roles")
        }
        assert "ix_user_roles_role_id" in user_role_indexes


def test_one_user_can_have_multiple_roles(app, clean_db):
    _upgrade(app)

    with app.app_context():
        with db.engine.begin() as connection:
            user_id = connection.execute(
                text(
                    """
                    INSERT INTO users (email, password_hash, status_changed_at)
                    VALUES ('owner@example.test', 'not-a-real-hash', now())
                    RETURNING id
                    """
                )
            ).scalar_one()

            role_ids = []
            for code, name in (
                ("customer", "Customer"),
                ("support_agent", "Support agent"),
            ):
                role_ids.append(
                    connection.execute(
                        text(
                            """
                            INSERT INTO roles (code, name)
                            VALUES (:code, :name)
                            RETURNING id
                            """
                        ),
                        {"code": code, "name": name},
                    ).scalar_one()
                )

            connection.execute(
                text(
                    """
                    INSERT INTO user_roles (user_id, role_id)
                    VALUES (:user_id, :first_role), (:user_id, :second_role)
                    """
                ),
                {
                    "user_id": user_id,
                    "first_role": role_ids[0],
                    "second_role": role_ids[1],
                },
            )

            assigned_count = connection.execute(
                text("SELECT count(*) FROM user_roles WHERE user_id = :user_id"),
                {"user_id": user_id},
            ).scalar_one()

        assert assigned_count == 2


@pytest.mark.parametrize(
    "email, status",
    [
        ("UPPER@example.test", "active"),
        ("valid@example.test", "unknown"),
    ],
)
def test_users_reject_invalid_email_case_and_status(app, clean_db, email, status):
    _upgrade(app)

    with app.app_context():
        with db.engine.connect() as connection:
            transaction = connection.begin()
            with pytest.raises(IntegrityError):
                connection.execute(
                    text(
                        """
                        INSERT INTO users (email, password_hash, status, status_changed_at)
                        VALUES (:email, 'not-a-real-hash', :status, now())
                        """
                    ),
                    {"email": email, "status": status},
                )
            transaction.rollback()


def test_auth_tokens_have_approved_constraints_and_active_lookup_index(app, clean_db):
    _upgrade(app)

    with app.app_context():
        inspector = inspect(db.engine)
        columns = {column["name"] for column in inspector.get_columns("auth_tokens")}
        assert {
            "id", "user_id", "purpose", "token_hash", "created_at",
            "expires_at", "used_at", "revoked_at",
        } <= columns

        checks = {item["name"] for item in inspector.get_check_constraints("auth_tokens")}
        assert {
            "ck_auth_tokens_purpose_allowed",
            "ck_auth_tokens_expiry_after_creation",
        } <= checks

        uniques = {item["name"] for item in inspector.get_unique_constraints("auth_tokens")}
        assert "uq_auth_tokens_token_hash" in uniques

        foreign_keys = inspector.get_foreign_keys("auth_tokens")
        assert len(foreign_keys) == 1
        assert foreign_keys[0]["referred_table"] == "users"
        assert foreign_keys[0]["options"].get("ondelete") == "RESTRICT"

        indexes = {item["name"]: item for item in inspector.get_indexes("auth_tokens")}
        assert "ix_auth_tokens_user_purpose_active" in indexes
        assert indexes["ix_auth_tokens_user_purpose_active"]["column_names"] == ["user_id", "purpose"]


def test_auth_tokens_reject_invalid_purpose_and_expiry(app, clean_db):
    _upgrade(app)

    with app.app_context():
        with db.engine.begin() as connection:
            user_id = connection.execute(
                text("""
                    INSERT INTO users (email, password_hash, status_changed_at)
                    VALUES ('token-owner@example.test', 'not-a-real-hash', now())
                    RETURNING id
                """)
            ).scalar_one()

        for purpose, created_at, expires_at in (
            ("unknown", "2026-01-01T00:00:00+00:00", "2026-01-02T00:00:00+00:00"),
            ("password_reset", "2026-01-02T00:00:00+00:00", "2026-01-01T00:00:00+00:00"),
        ):
            with db.engine.connect() as connection:
                transaction = connection.begin()
                with pytest.raises(IntegrityError):
                    connection.execute(
                        text("""
                            INSERT INTO auth_tokens
                                (user_id, purpose, token_hash, created_at, expires_at)
                            VALUES (:user_id, :purpose, :token_hash, :created_at, :expires_at)
                        """),
                        {
                            "user_id": user_id,
                            "purpose": purpose,
                            "token_hash": ("a" if purpose == "unknown" else "b") * 64,
                            "created_at": created_at,
                            "expires_at": expires_at,
                        },
                    )
                transaction.rollback()


def test_auth_token_hash_must_be_unique(app, clean_db):
    _upgrade(app)

    with app.app_context():
        with db.engine.begin() as connection:
            user_id = connection.execute(
                text("""
                    INSERT INTO users (email, password_hash, status_changed_at)
                    VALUES ('token-unique@example.test', 'not-a-real-hash', now())
                    RETURNING id
                """)
            ).scalar_one()
            connection.execute(text("""
                INSERT INTO auth_tokens (user_id, purpose, token_hash, expires_at)
                VALUES (:user_id, 'password_reset', :token_hash, now() + interval '1 hour')
            """), {"user_id": user_id, "token_hash": "c" * 64})

        with db.engine.connect() as connection:
            transaction = connection.begin()
            with pytest.raises(IntegrityError):
                connection.execute(text("""
                    INSERT INTO auth_tokens (user_id, purpose, token_hash, expires_at)
                    VALUES (:user_id, 'email_verification', :token_hash, now() + interval '1 hour')
                """), {"user_id": user_id, "token_hash": "c" * 64})
            transaction.rollback()


def test_audit_logs_have_approved_schema_constraints_and_indexes(app, clean_db):
    _upgrade(app)

    with app.app_context():
        inspector = inspect(db.engine)
        columns = {column["name"]: column for column in inspector.get_columns("audit_logs")}
        assert {
            "id", "public_id", "actor_user_id", "actor_label", "action",
            "entity_type", "entity_id", "before_data", "after_data",
            "event_metadata", "ip_address", "request_id", "created_at",
        } <= set(columns)
        assert columns["before_data"]["type"].__class__.__name__ == "JSONB"
        assert columns["after_data"]["type"].__class__.__name__ == "JSONB"
        assert columns["event_metadata"]["type"].__class__.__name__ == "JSONB"
        assert columns["ip_address"]["type"].__class__.__name__ == "INET"

        checks = {item["name"] for item in inspector.get_check_constraints("audit_logs")}
        assert "ck_audit_logs_actor_present" in checks
        uniques = {item["name"] for item in inspector.get_unique_constraints("audit_logs")}
        assert "uq_audit_logs_public_id" in uniques
        foreign_keys = inspector.get_foreign_keys("audit_logs")
        assert len(foreign_keys) == 1
        assert foreign_keys[0]["referred_table"] == "users"
        assert foreign_keys[0]["options"].get("ondelete") == "RESTRICT"

        indexes = {item["name"]: item for item in inspector.get_indexes("audit_logs")}
        assert indexes["ix_audit_logs_entity_created"]["column_names"] == [
            "entity_type", "entity_id", "created_at"
        ]
        assert indexes["ix_audit_logs_actor_created"]["column_names"] == [
            "actor_user_id", "created_at"
        ]
        assert indexes["ix_audit_logs_action_created"]["column_names"] == [
            "action", "created_at"
        ]


def test_audit_logs_require_an_actor_and_accept_maintenance_label(app, clean_db):
    _upgrade(app)

    with app.app_context():
        with db.engine.connect() as connection:
            transaction = connection.begin()
            with pytest.raises(IntegrityError):
                connection.execute(text("""
                    INSERT INTO audit_logs (action, entity_type, entity_id)
                    VALUES ('identity.test', 'user', 'public-user-id')
                """))
            transaction.rollback()

        with db.engine.begin() as connection:
            row = connection.execute(text("""
                INSERT INTO audit_logs
                    (actor_label, action, entity_type, entity_id, before_data,
                     after_data, event_metadata, ip_address, request_id)
                VALUES
                    ('seed-dev', 'identity.test', 'user', 'public-user-id',
                     '{"status":"disabled"}'::jsonb,
                     '{"status":"active"}'::jsonb,
                     '{"source":"test"}'::jsonb, '192.0.2.10'::inet, 'request-123')
                RETURNING public_id, created_at
            """)).one()
            assert row.public_id is not None
            assert row.created_at is not None
