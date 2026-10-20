"""Shared fixtures. Tests run against a real PostgreSQL database named *_test.

Required: TEST_DATABASE_URL (in the environment or .env). The schema of that
database is wiped by tests, which is why the name guard below exists.
"""
import os
import secrets
from pathlib import Path

import pytest
from dotenv import load_dotenv
from flask import abort, flash, render_template, session
from flask_wtf.csrf import generate_csrf
from sqlalchemy import create_engine, text

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

from app import create_app  # noqa: E402
from app.config import database_name, normalise_database_url  # noqa: E402
from app.extensions import db, limiter  # noqa: E402

FAKE_PRODUCTION_DB_URL = "postgresql+psycopg://appuser:Zq7pLm29@127.0.0.1:5432/marketplace_test"


@pytest.fixture(scope="session")
def test_database_url() -> str:
    raw = os.environ.get("TEST_DATABASE_URL", "").strip()
    if not raw:
        pytest.exit("TEST_DATABASE_URL is not set. Copy .env.example to .env and fill it in.", returncode=2)
    url = normalise_database_url(raw, "TEST_DATABASE_URL")
    if not database_name(url).endswith("_test"):
        pytest.exit("TEST_DATABASE_URL must point to a database whose name ends in _test.", returncode=2)
    return url


def wipe_schema(url: str) -> None:
    """Drop and recreate the public schema. Refuses any database not named *_test."""
    assert database_name(url).endswith("_test"), "refusing to wipe a non-test database"
    engine = create_engine(url)
    try:
        with engine.begin() as conn:
            conn.execute(text("DROP SCHEMA public CASCADE"))
            conn.execute(text("CREATE SCHEMA public"))
    finally:
        engine.dispose()


def register_test_routes(app) -> None:
    """Routes that exist only in tests, to exercise CSRF, errors, sessions and flashes."""
    app.add_url_rule("/_test/token", "t_token", lambda: generate_csrf())
    app.add_url_rule("/_test/post", "t_post", lambda: ("ok", 200), methods=["POST"])

    def boom():
        raise RuntimeError("super-secret-internal-detail")

    def forbidden():
        abort(403)

    def flashes():
        flash("Saved it", "success")
        flash("Careful now", "warning")
        return render_template("base.html")

    def set_session():
        session["probe"] = 1
        return "ok"

    app.add_url_rule("/_test/boom", "t_boom", boom)
    app.add_url_rule("/_test/forbidden", "t_forbidden", forbidden)
    app.add_url_rule("/_test/flash", "t_flash", flashes)
    app.add_url_rule("/_test/session", "t_session", set_session)
    app.add_url_rule("/_test/limited", "t_limited", lambda: "ok")


@pytest.fixture
def app(test_database_url):
    application = create_app("testing")
    register_test_routes(application)
    yield application
    with application.app_context():
        db.session.remove()
        db.engine.dispose()
    limiter.reset()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def clean_db(test_database_url, app):
    """An empty test database for the duration of the test."""
    with app.app_context():
        db.session.remove()
        db.engine.dispose()
    wipe_schema(test_database_url)
    yield test_database_url


@pytest.fixture
def production_env(test_database_url):
    return {
        "APP_ENV": "production",
        "SECRET_KEY": secrets.token_urlsafe(48),
        "DATABASE_URL": FAKE_PRODUCTION_DB_URL,
        "RATELIMIT_STORAGE_URI": "redis://127.0.0.1:6379/15",
    }


@pytest.fixture
def production_app(production_env, monkeypatch):
    # Tests use in-memory storage explicitly; production configuration itself is
    # still validated with a shared-store URI, while connectivity is tested separately.
    import app as app_module
    monkeypatch.setattr(app_module, "verify_shared_rate_limit_storage", lambda _limiter: None)
    application = create_app(
        "production",
        environ=production_env,
        config_overrides={"RATELIMIT_STORAGE_URI": "memory://"},
    )
    register_test_routes(application)
    yield application
    limiter.reset()
