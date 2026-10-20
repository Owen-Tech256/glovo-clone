"""Request id, security headers and request logging.

Logging records the path only. Query strings, bodies, cookies and authorization
values are never logged (password-reset links will carry tokens in the query string).
"""
import re
import uuid

from flask import Flask, Response, g, request

_REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9._-]{1,64}$")

CONTENT_SECURITY_POLICY = "; ".join(
    [
        "default-src 'self'",
        "img-src 'self' data:",
        "style-src 'self'",
        "script-src 'self'",
        "object-src 'none'",
        "base-uri 'self'",
        "form-action 'self'",
        "frame-ancestors 'none'",
    ]
)


def _safe_log_path(path: str) -> str:
    return path[:200].encode("unicode_escape").decode("ascii")


def register_security(app: Flask) -> None:
    @app.before_request
    def assign_request_id() -> None:
        inbound = request.headers.get("X-Request-ID", "")
        g.request_id = inbound if _REQUEST_ID_PATTERN.match(inbound) else uuid.uuid4().hex

    @app.after_request
    def add_headers_and_log(response: Response) -> Response:
        request_id = getattr(g, "request_id", "-")
        response.headers["X-Request-ID"] = request_id
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault("Content-Security-Policy", CONTENT_SECURITY_POLICY)
        response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        if app.config.get("HSTS_ENABLED"):
            response.headers.setdefault("Strict-Transport-Security", "max-age=31536000")
        level = 10 if request.path.startswith("/health") else 20  # DEBUG for probes, INFO otherwise
        app.logger.log(
            level,
            "request_id=%s method=%s path=%s status=%s",
            request_id,
            request.method,
            _safe_log_path(request.path),
            response.status_code,
        )
        return response
