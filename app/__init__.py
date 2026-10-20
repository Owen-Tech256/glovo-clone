"""Application factory."""
import logging
import os
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from flask import Flask

from app.config import build_config


def verify_shared_rate_limit_storage(limiter_instance) -> None:
    """Probe configured rate-limit storage without exposing its URI or backend errors."""
    # Accessing a framework extension's storage property may itself initialize the
    # backend and raise (for example, on an invalid URI). Treat that like any other
    # backend outage so readiness can return a generic 503 and startup fails closed.
    try:
        storage = getattr(limiter_instance, "storage", None)
        if storage is None:
            storage = getattr(limiter_instance, "_storage", None)
        check = getattr(storage, "check", None)
    except Exception:
        raise RuntimeError("shared rate-limit storage is unavailable") from None

    if not callable(check):
        raise RuntimeError("shared rate-limit storage health check is unavailable")

    try:
        healthy = check()
    except Exception:
        # Do not include backend exception text: it can contain hostnames or credentials.
        raise RuntimeError("shared rate-limit storage is unavailable") from None
    if healthy is False:
        raise RuntimeError("shared rate-limit storage is unavailable")
from app.extensions import csrf, db, limiter, login_manager, migrate


def create_app(
    config_name: str | None = None,
    config_overrides: Mapping[str, Any] | None = None,
    environ: Mapping[str, str] | None = None,
) -> Flask:
    env = os.environ if environ is None else environ
    name = (config_name or env.get("APP_ENV") or "production").strip().lower()
    config = build_config(name, env)

    app = Flask(__name__)
    app.config.from_mapping(config)
    if config_overrides:
        app.config.update(config_overrides)

    app.logger.setLevel(getattr(logging, app.config["LOG_LEVEL"], logging.INFO))

    from app import models  # noqa: F401  (registers metadata for migrations)

    db.init_app(app)
    migrate.init_app(
        app, db, directory=str(Path(app.root_path).parent / "migrations"), compare_type=True
    )
    csrf.init_app(app)
    login_manager.init_app(app)
    try:
        limiter.init_app(app)
    except Exception:
        if app.config["APP_ENV"] == "production":
            app.logger.critical("Production startup blocked: shared rate-limit storage could not be initialized.")
            raise RuntimeError(
                "Production startup blocked: shared rate-limit storage unavailable."
            ) from None
        raise

    # D-79 / D-83: production must not start unless shared rate-limit storage is reachable.
    # Development and tests intentionally use memory:// and skip this production probe.
    if app.config["APP_ENV"] == "production":
        try:
            verify_shared_rate_limit_storage(limiter)
        except RuntimeError:
            app.logger.critical("Production startup blocked: shared rate-limit storage unavailable.")
            raise RuntimeError("Production startup blocked: shared rate-limit storage unavailable.") from None

    from app.cli import register_cli
    from app.errors import register_error_handlers
    from app.main import bp as main_bp
    from app.security import register_security

    register_security(app)
    register_error_handlers(app)
    from app.marketplace import bp as marketplace_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(marketplace_bp)
    register_cli(app)
    return app
