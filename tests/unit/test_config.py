import pytest

from app import create_app
from app.config import ConfigError, build_config, normalise_database_url
from app.extensions import csrf, db, limiter, login_manager

DEV_URL = "postgresql+psycopg://u:p@127.0.0.1:5432/marketplace_dev"
TEST_URL = "postgresql+psycopg://u:p@127.0.0.1:5432/marketplace_test"
STRONG_KEY = "k" * 48 + "Zx9"


def env(**overrides):
    base = {"DATABASE_URL": DEV_URL, "TEST_DATABASE_URL": TEST_URL, "SECRET_KEY": STRONG_KEY, "RATELIMIT_STORAGE_URI": "redis://127.0.0.1:6379/15"}
    base.update(overrides)
    return {k: v for k, v in base.items() if v is not None}


# F-01
@pytest.mark.parametrize(
    "name, debug, testing",
    [("development", True, False), ("testing", False, True), ("production", False, False)],
)
def test_app_builds_for_each_config(name, debug, testing, monkeypatch):
    import app as app_module

    test_env = env()
    if name == "development":
        test_env["RATELIMIT_STORAGE_URI"] = "memory://"

    overrides = None
    if name == "production":
        monkeypatch.setattr(
            app_module,
            "verify_shared_rate_limit_storage",
            lambda _limiter: None,
        )
        # Production URI validation still runs; only the connectivity probe is mocked.
        overrides = {"RATELIMIT_STORAGE_URI": "memory://"}

    app = create_app(
        name,
        environ=test_env,
        config_overrides=overrides,
    )
    assert app.config["APP_ENV"] == name
    assert app.config["DEBUG"] is debug
    assert app.config["TESTING"] is testing


# F-02
def test_unknown_config_name_raises_clear_error():
    with pytest.raises(ConfigError, match="Unknown configuration 'staging'"):
        create_app("staging", environ=env())


def test_unset_app_env_falls_back_to_production_and_fails_safe():
    with pytest.raises(ConfigError, match="SECRET_KEY is required in production"):
        create_app(environ={})


# F-03
@pytest.mark.parametrize(
    "overrides, message",
    [
        ({"SECRET_KEY": None}, "SECRET_KEY is required"),
        ({"SECRET_KEY": "change-me-use-a-long-random-value-0123456789"}, "SECRET_KEY must be a real random value"),
        ({"SECRET_KEY": "dev-only-not-a-secret"}, "SECRET_KEY must be a real random value"),
        ({"SECRET_KEY": "short"}, "SECRET_KEY must be a real random value"),
        ({"DATABASE_URL": None}, "DATABASE_URL is required"),
        ({"DATABASE_URL": "postgresql+psycopg://USER:PASSWORD@localhost/app"}, "placeholder credentials"),
        ({"DATABASE_URL": "sqlite:///x.db"}, "PostgreSQL"),
    ],
)
def test_production_refuses_missing_or_placeholder_values(overrides, message):
    with pytest.raises(ConfigError, match=message):
        build_config("production", env(**overrides))


def test_config_errors_never_echo_the_secret_value():
    with pytest.raises(ConfigError) as exc:
        build_config("production", env(SECRET_KEY="short"))
    assert "short" not in str(exc.value).replace("SECRET_KEY must be a real random value", "")




@pytest.mark.parametrize(
    "value",
    [None, "", "   ", "memory://", "MEMORY://", " memory:// ", "Memory://localhost"],
)
def test_production_refuses_unset_or_in_memory_rate_limit_storage(value):
    with pytest.raises(ConfigError, match="RATELIMIT_STORAGE_URI.*RB-01") as exc:
        build_config("production", env(RATELIMIT_STORAGE_URI=value))
    assert "memory://" not in str(exc.value).lower()


def test_production_accepts_shared_rate_limit_storage_uri_without_echoing_it():
    uri = "redis://user:private-secret@cache.example.test:6379/2"
    cfg = build_config("production", env(RATELIMIT_STORAGE_URI=uri))
    assert cfg["RATELIMIT_STORAGE_URI"] == uri


# F-04 (config part; the header part is in the integration tests)
def test_production_cookie_and_hsts_settings():
    cfg = build_config("production", env())
    assert cfg["SESSION_COOKIE_SECURE"] is True
    assert cfg["SESSION_COOKIE_HTTPONLY"] is True
    assert cfg["SESSION_COOKIE_SAMESITE"] == "Lax"
    assert cfg["REMEMBER_COOKIE_SECURE"] is True
    assert cfg["HSTS_ENABLED"] is True


# F-05
def test_testing_config_requires_a_test_database_url():
    with pytest.raises(ConfigError, match="TEST_DATABASE_URL is required"):
        build_config("testing", env(TEST_DATABASE_URL=None))


def test_testing_config_refuses_a_database_not_named_test():
    with pytest.raises(ConfigError, match="ends in _test"):
        build_config("testing", env(TEST_DATABASE_URL=DEV_URL, DATABASE_URL=None))


def test_testing_config_refuses_the_development_database():
    same = "postgresql+psycopg://u:p@127.0.0.1:5432/marketplace_test"
    with pytest.raises(ConfigError, match="must not be the same as DATABASE_URL"):
        build_config("testing", env(TEST_DATABASE_URL=same, DATABASE_URL=same))


# F-06
def test_extensions_are_registered():
    dev_env = env()
    dev_env["RATELIMIT_STORAGE_URI"] = "memory://"
    app = create_app("development", environ=dev_env)
    assert "sqlalchemy" in app.extensions
    assert app.extensions["migrate"].db is db
    assert app.extensions["csrf"] is csrf
    assert limiter in app.extensions["limiter"]
    assert app.login_manager is login_manager
    assert login_manager.session_protection == "strong"


# F-31
def test_production_debug_and_testing_are_off(monkeypatch):
    import app as app_module
    monkeypatch.setattr(app_module, "verify_shared_rate_limit_storage", lambda _limiter: None)
    app = create_app(
        "production", environ=env(),
        config_overrides={"RATELIMIT_STORAGE_URI": "memory://"},
    )
    assert app.debug is False
    assert app.testing is False


def test_money_constants_are_ugx_with_no_minor_unit():
    cfg = build_config("development", env())
    assert cfg["CURRENCY_CODE"] == "UGX"
    assert cfg["CURRENCY_EXPONENT"] == 0


def test_database_urls_are_normalised_to_psycopg3():
    assert normalise_database_url("postgresql://u:p@h/db", "X").startswith("postgresql+psycopg://")
    assert normalise_database_url("postgres://u:p@h/db", "X").startswith("postgresql+psycopg://")
    with pytest.raises(ConfigError):
        normalise_database_url("not a url", "X")
