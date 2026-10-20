"""Operational routes. Contract: docs/contracts/foundation.md."""
from flask import current_app, g, jsonify
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app import verify_shared_rate_limit_storage
from app.extensions import db, limiter

from . import bp


def _no_store(response):
    response.headers["Cache-Control"] = "no-store"
    return response


@bp.get("/health")
@limiter.exempt
def health():
    """Liveness: the process is up. Does not touch the database."""
    return _no_store(jsonify({"status": "ok"}))


@bp.get("/health/ready")
@limiter.exempt
def ready():
    """Readiness checks the database and production's required shared limiter store."""
    try:
        db.session.execute(text("SELECT 1"))
        db.session.rollback()
    except SQLAlchemyError as exc:
        db.session.rollback()
        current_app.logger.warning(
            "Readiness database check failed request_id=%s type=%s",
            getattr(g, "request_id", "-"), type(exc).__name__
        )
        return _no_store(jsonify({"status": "unavailable"})), 503

    if current_app.config.get("APP_ENV") == "production":
        try:
            verify_shared_rate_limit_storage(limiter)
        except RuntimeError:
            current_app.logger.warning(
                "Readiness shared storage check failed request_id=%s",
                getattr(g, "request_id", "-")
            )
            return _no_store(jsonify({"status": "unavailable"})), 503
    return _no_store(jsonify({"status": "ready"}))
