"""Central error handling. HTML for browsers, JSON when the client asks for it."""
from flask import Flask, g, jsonify, render_template, request
from werkzeug.exceptions import HTTPException

ERROR_COPY = {
    400: ("Bad request", "The request could not be processed. Check the details and try again."),
    401: ("Sign in required", "You need to sign in to continue."),
    403: ("Access denied", "You do not have permission to view this page."),
    404: ("Page not found", "We could not find the page you asked for."),
    405: ("Method not allowed", "This action is not allowed on this page."),
    409: ("Conflict", "This request conflicts with the current state. Refresh and try again."),
    413: ("Request too large", "The request is larger than the allowed size."),
    422: ("Could not process the details", "Some of the details could not be processed. Check them and try again."),
    429: ("Too many requests", "You have made too many requests. Wait a moment and try again."),
    500: ("Something went wrong", "An unexpected error occurred. Try again later."),
}
_SKIPPED_HEADERS = {"content-type", "content-length"}


def _wants_json() -> bool:
    if request.path.startswith("/health"):
        return True
    accept = request.accept_mimetypes
    best = accept.best_match(["text/html", "application/json"])
    return best == "application/json" and accept[best] > accept["text/html"]


def _render(code: int, extra_headers=None):
    title, message = ERROR_COPY.get(code, ("Error", "The request could not be completed."))
    request_id = getattr(g, "request_id", "-")
    if _wants_json():
        response = jsonify({"error": {"code": code, "title": title, "request_id": request_id}})
    else:
        from flask import make_response

        response = make_response(render_template(
            "errors/error.html", code=code, title=title, message=message, request_id=request_id
        ))
    response.status_code = code
    for key, value in (extra_headers or []):
        if key.lower() not in _SKIPPED_HEADERS:
            response.headers[key] = value
    return response


def register_error_handlers(app: Flask) -> None:
    @app.errorhandler(HTTPException)
    def handle_http_exception(exc: HTTPException):
        code = exc.code or 500
        headers = exc.get_response().headers.items() if code != 500 else []
        return _render(code, headers)

    @app.errorhandler(Exception)
    def handle_unexpected(exc: Exception):
        # Class name only: exception text can contain SQL parameters or other sensitive values.
        app.logger.error(
            "Unhandled exception request_id=%s type=%s", getattr(g, "request_id", "-"), type(exc).__name__,
            exc_info=app.debug,
        )
        return _render(500)
