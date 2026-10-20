"""Environment safeguards for seeding (decision D-08 and B-07)."""
from flask import Flask
from sqlalchemy.engine import make_url

ALLOWED_ENVIRONMENTS = ("development", "testing")
ALLOWED_DATABASE_SUFFIXES = ("_dev", "_test")


def check_seed_allowed(app: Flask) -> tuple[bool, str]:
    """Return (allowed, reason). There is no override: production is refused outright."""
    if app.config.get("APP_ENV") not in ALLOWED_ENVIRONMENTS:
        return False, "seeding is only available in the development and testing environments."
    if not app.config.get("SEED_DEV_ENABLED"):
        return False, "seeding is disabled by configuration."
    name = make_url(app.config["SQLALCHEMY_DATABASE_URI"]).database or ""
    if not name.endswith(ALLOWED_DATABASE_SUFFIXES):
        return False, "the target database name must end in _dev or _test."
    return True, ""
