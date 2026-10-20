"""Extension instances. Initialised in create_app, never at import time."""
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect

from app.models.base import Base

db = SQLAlchemy(model_class=Base)
migrate = Migrate()
csrf = CSRFProtect()
# Authentication must fail closed if the shared store is unavailable. Explicitly
# disable both swallowed backend errors and per-process in-memory fallback.
limiter = Limiter(
    key_func=get_remote_address,
    swallow_errors=False,
    in_memory_fallback_enabled=False,
)

login_manager = LoginManager()
# Guards against session fixation (testing_security_prompt.md). The login view and
# user loader are added in the Identity phase.
login_manager.session_protection = "strong"


@login_manager.user_loader
def load_user(user_id: str):
    """Authentication is not implemented in the schema-only Identity batch.

    Flask-Login injects `current_user` into template renders. Returning ``None``
    keeps anonymous pages and error handlers usable until the approved login
    service and user loader are implemented in a later Identity batch.
    """
    return None
