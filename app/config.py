"""Configuration built from environment variables at app-creation time.

Safe by default: if APP_ENV is unset the app starts as production, which
requires real secrets, disables debugging and refuses to seed.
"""
import os
from collections.abc import Mapping
from typing import Any

from sqlalchemy.engine import make_url
from sqlalchemy.exc import ArgumentError

# Every environment variable this module reads. tests/unit/test_environment.py
# checks that .env.example lists each one.
ENV_VARS = (
    "APP_ENV",
    "SECRET_KEY",
    "DATABASE_URL",
    "TEST_DATABASE_URL",
    "RATELIMIT_STORAGE_URI",
    "LOG_LEVEL",
    "SITE_NAME",
)

KNOWN_ENVIRONMENTS = ("development", "testing", "production")
PLACEHOLDER_PREFIXES = ("change-me", "changeme", "replace-me", "replace-with", "your-", "dev-only", "testing-")
MIN_SECRET_KEY_LENGTH = 32
DEV_SECRET_KEY = "dev-only-not-a-secret"
TEST_SECRET_KEY = "testing-not-a-secret"


class ConfigError(Exception):
    """Raised when configuration is missing or unsafe. Messages never contain secret values."""


def _is_placeholder(value: str) -> bool:
    lowered = value.strip().lower()
    return not lowered or lowered.startswith(PLACEHOLDER_PREFIXES)


def normalise_database_url(raw: str, variable: str) -> str:
    """Return a SQLAlchemy URL using the psycopg 3 driver. PostgreSQL only."""
    try:
        url = make_url(raw)
    except ArgumentError as exc:
        raise ConfigError(f"{variable} is not a valid database URL.") from exc
    if url.get_backend_name() not in ("postgres", "postgresql"):
        raise ConfigError(f"{variable} must be a PostgreSQL URL (PostgreSQL is the only approved database).")
    if url.drivername in ("postgres", "postgresql"):
        url = url.set(drivername="postgresql+psycopg")
    return url.render_as_string(hide_password=False)


def database_name(url: str) -> str:
    return make_url(url).database or ""


def _require(env: Mapping[str, str], name: str) -> str:
    value = env.get(name, "").strip()
    if not value:
        raise ConfigError(f"{name} is required for this configuration.")
    return value


def _common(env: Mapping[str, str], name: str) -> dict[str, Any]:
    return {
        "APP_ENV": name,
        "SITE_NAME": env.get("SITE_NAME", "Marketplace").strip() or "Marketplace",
        "LOG_LEVEL": env.get("LOG_LEVEL", "INFO").strip().upper() or "INFO",
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
        # Money: UGX has no minor unit (docs/conventions.md).
        "CURRENCY_CODE": "UGX",
        "CURRENCY_EXPONENT": 0,
        # Cookies.
        "SESSION_COOKIE_HTTPONLY": True,
        "SESSION_COOKIE_SAMESITE": "Lax",
        "SESSION_COOKIE_SECURE": False,
        "REMEMBER_COOKIE_HTTPONLY": True,
        "REMEMBER_COOKIE_SAMESITE": "Lax",
        "REMEMBER_COOKIE_SECURE": False,
        # Forms and rate limiting.
        "WTF_CSRF_ENABLED": True,
        "RATELIMIT_STORAGE_URI": env.get("RATELIMIT_STORAGE_URI", "memory://").strip() or "memory://",
        "RATELIMIT_HEADERS_ENABLED": True,
        # Technical hardening default (1 MiB). Upload routes will set their own limits later.
        "MAX_CONTENT_LENGTH": 1024 * 1024,
        "HSTS_ENABLED": False,
        "SEED_DEV_ENABLED": False,
        "DEBUG": False,
        "TESTING": False,
    }


def build_config(name: str, environ: Mapping[str, str] | None = None) -> dict[str, Any]:
    env = os.environ if environ is None else environ
    if name not in KNOWN_ENVIRONMENTS:
        raise ConfigError(f"Unknown configuration '{name}'. Expected one of: {', '.join(KNOWN_ENVIRONMENTS)}.")
    cfg = _common(env, name)

    if name == "development":
        cfg["DEBUG"] = True
        cfg["SEED_DEV_ENABLED"] = True
        cfg["SECRET_KEY"] = env.get("SECRET_KEY", "").strip() or DEV_SECRET_KEY
        cfg["SQLALCHEMY_DATABASE_URI"] = normalise_database_url(
            _require(env, "DATABASE_URL"), "DATABASE_URL"
        )

    elif name == "testing":
        test_url = normalise_database_url(_require(env, "TEST_DATABASE_URL"), "TEST_DATABASE_URL")
        if not database_name(test_url).endswith("_test"):
            raise ConfigError("TEST_DATABASE_URL must point to a database whose name ends in _test.")
        dev_raw = env.get("DATABASE_URL", "").strip()
        if dev_raw and normalise_database_url(dev_raw, "DATABASE_URL") == test_url:
            raise ConfigError("TEST_DATABASE_URL must not be the same as DATABASE_URL.")
        cfg.update(
            TESTING=True,
            SEED_DEV_ENABLED=True,
            # Let the 500 handler run in tests instead of re-raising into the test client.
            PROPAGATE_EXCEPTIONS=False,
            SECRET_KEY=TEST_SECRET_KEY,
            SQLALCHEMY_DATABASE_URI=test_url,
            RATELIMIT_STORAGE_URI="memory://",
        )

    else:  # production
        # D-79: never allow the process to start with per-worker memory limits.
        # Normalise whitespace/case for the scheme check, but retain the configured URI
        # unchanged for the storage backend. Do not include its value in any error.
        rate_limit_uri = env.get("RATELIMIT_STORAGE_URI", "").strip()
        if not rate_limit_uri or rate_limit_uri.lower().startswith("memory://"):
            raise ConfigError(
                "RATELIMIT_STORAGE_URI must name a shared, persistent rate-limit store (RB-01)."
            )
        cfg["RATELIMIT_STORAGE_URI"] = rate_limit_uri

        secret = env.get("SECRET_KEY", "").strip()
        if not secret:
            raise ConfigError("SECRET_KEY is required in production.")
        if _is_placeholder(secret) or len(secret) < MIN_SECRET_KEY_LENGTH:
            raise ConfigError(
                f"SECRET_KEY must be a real random value of at least {MIN_SECRET_KEY_LENGTH} characters."
            )
        db_url = normalise_database_url(_require(env, "DATABASE_URL"), "DATABASE_URL")
        parsed = make_url(db_url)
        if parsed.username == "USER" or (parsed.password and _is_placeholder(parsed.password)) or parsed.password == "PASSWORD":
            raise ConfigError("DATABASE_URL still contains placeholder credentials.")
        cfg.update(
            SECRET_KEY=secret,
            SQLALCHEMY_DATABASE_URI=db_url,
            SESSION_COOKIE_SECURE=True,
            REMEMBER_COOKIE_SECURE=True,
            HSTS_ENABLED=True,
        )
    return cfg
