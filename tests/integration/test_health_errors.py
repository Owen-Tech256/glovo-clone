import logging

from app import create_app


# F-07
def test_csrf_rejects_post_without_token(client):
    assert client.post("/_test/post").status_code == 400


def test_csrf_accepts_post_with_valid_token(client):
    token = client.get("/_test/token").get_data(as_text=True)
    assert client.post("/_test/post", headers={"X-CSRFToken": token}).status_code == 200


# F-08
def test_health_is_up_and_leaks_nothing(client, app):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}
    assert response.headers["Cache-Control"] == "no-store"
    body = response.get_data(as_text=True)
    assert app.config["SECRET_KEY"] not in body and "postgresql" not in body


# F-09
def test_ready_is_200_with_database_up(client):
    response = client.get("/health/ready")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ready"}


def test_ready_is_503_with_database_down_and_no_details(test_database_url):
    unreachable = "postgresql+psycopg://u:p@127.0.0.1:9/marketplace_test?connect_timeout=2"
    app = create_app("testing", config_overrides={"SQLALCHEMY_DATABASE_URI": unreachable})
    response = app.test_client().get("/health/ready")
    assert response.status_code == 503
    assert response.get_json() == {"status": "unavailable"}
    body = response.get_data(as_text=True)
    assert "127.0.0.1" not in body and "psycopg" not in body and "refused" not in body.lower()


def test_health_routes_are_not_rate_limited(test_database_url):
    app = create_app("testing", config_overrides={"RATELIMIT_DEFAULT": "1 per minute"})
    client = app.test_client()
    assert [client.get("/health").status_code for _ in range(3)] == [200, 200, 200]


# F-10
def test_unknown_url_renders_html_404_in_base_layout(client):
    response = client.get("/nope")
    html = response.get_data(as_text=True)
    assert response.status_code == 404
    assert response.mimetype == "text/html"
    assert "Page not found" in html and '<main id="main"' in html


# F-11
def test_403_and_405_render_error_pages(client):
    forbidden = client.get("/_test/forbidden")
    assert forbidden.status_code == 403 and "Access denied" in forbidden.get_data(as_text=True)
    wrong_method = client.post("/health")
    assert wrong_method.status_code == 405 and "Method not allowed" in wrong_method.get_data(as_text=True)
    assert "GET" in wrong_method.headers["Allow"]


# F-12
def test_unhandled_exception_returns_generic_500_without_traceback_in_production(production_app, caplog):
    with caplog.at_level(logging.INFO):
        response = production_app.test_client().get("/_test/boom")
    html = response.get_data(as_text=True)
    assert response.status_code == 500
    assert "Something went wrong" in html
    assert "super-secret-internal-detail" not in html
    assert "Traceback" not in html and "RuntimeError" not in html
    assert "super-secret-internal-detail" not in caplog.text
    assert "Traceback" not in caplog.text


# F-13
def test_error_responses_carry_the_request_id(client):
    response = client.get("/nope")
    request_id = response.headers["X-Request-ID"]
    assert request_id and request_id in response.get_data(as_text=True)


def test_json_is_returned_when_the_client_asks_for_it(client):
    response = client.get("/nope", headers={"Accept": "application/json"})
    assert response.status_code == 404
    payload = response.get_json()["error"]
    assert payload["code"] == 404 and payload["request_id"] == response.headers["X-Request-ID"]


def test_browser_style_accept_header_still_gets_html(client):
    response = client.get("/nope", headers={"Accept": "text/html,application/xhtml+xml,*/*;q=0.8"})
    assert response.mimetype == "text/html"


def test_unsafe_inbound_request_id_is_replaced(client):
    for unsafe in ("bad id;<script>", "x" * 65):
        assert client.get("/health", headers={"X-Request-ID": unsafe}).headers["X-Request-ID"] != unsafe
    assert client.get("/health", headers={"X-Request-ID": "abc-123"}).headers["X-Request-ID"] == "abc-123"


# F-14
def test_rate_limit_renders_the_429_page(test_database_url):
    app = create_app("testing", config_overrides={"RATELIMIT_DEFAULT": "1 per minute"})
    from tests.conftest import register_test_routes

    register_test_routes(app)
    client = app.test_client()
    assert client.get("/_test/limited").status_code == 200
    response = client.get("/_test/limited")
    assert response.status_code == 429
    assert "Too many requests" in response.get_data(as_text=True)
    assert "Retry-After" in response.headers


# F-19
def test_security_headers_on_success_and_error_responses(client):
    for path in ("/health", "/nope"):
        headers = client.get(path).headers
        assert headers["X-Content-Type-Options"] == "nosniff"
        assert headers["X-Frame-Options"] == "DENY"
        assert headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
        assert "frame-ancestors 'none'" in headers["Content-Security-Policy"]
        assert "script-src 'self'" in headers["Content-Security-Policy"]
        assert "unsafe-inline" not in headers["Content-Security-Policy"]
        assert "Strict-Transport-Security" not in headers


# F-04 (header part)
def test_production_sets_secure_session_cookie_and_hsts(production_app):
    client = production_app.test_client()
    response = client.get("/_test/session", base_url="https://localhost")
    cookie = response.headers["Set-Cookie"]
    assert "Secure" in cookie and "HttpOnly" in cookie and "SameSite=Lax" in cookie
    assert response.headers["Strict-Transport-Security"] == "max-age=31536000"


# F-34
def test_request_logs_contain_the_path_only(client, caplog):
    with caplog.at_level(logging.INFO):
        client.get(
            "/nope?token=SECRET-TOKEN&email=a@b.test",
            headers={"Cookie": "session=SECRET-COOKIE", "Authorization": "Bearer SECRET-AUTH"},
        )
    assert "path=/nope status=404" in caplog.text
    for secret in ("SECRET-TOKEN", "a@b.test", "SECRET-COOKIE", "SECRET-AUTH", "token="):
        assert secret not in caplog.text


def test_log_path_escapes_control_characters(client, caplog):
    with caplog.at_level(logging.INFO):
        client.get("/nope%0AFAKE-LOG-LINE")
    assert not any(line.startswith("FAKE-LOG-LINE") for line in caplog.text.splitlines())
    assert "\\nFAKE-LOG-LINE" in caplog.text


# F-36 (A-14)
def test_production_startup_probes_shared_rate_limit_storage(production_env, monkeypatch):
    import app as app_module
    calls = []
    monkeypatch.setattr(app_module, "verify_shared_rate_limit_storage", lambda _limiter: calls.append("checked"))
    create_app(
        "production", environ=production_env,
        config_overrides={"RATELIMIT_STORAGE_URI": "memory://"},
    )
    assert calls == ["checked"]


def test_readiness_returns_unavailable_when_production_storage_is_down(production_app, monkeypatch):
    import app.main.routes as routes
    monkeypatch.setattr(
        routes, "verify_shared_rate_limit_storage",
        lambda _limiter: (_ for _ in ()).throw(RuntimeError("private backend details")),
    )
    response = production_app.test_client().get("/health/ready")
    assert response.status_code == 503
    assert response.get_json() == {"status": "unavailable"}
    assert "private backend details" not in response.get_data(as_text=True)


def test_production_startup_fails_closed_when_storage_probe_fails(production_env, monkeypatch):
    import app as app_module
    def fail(_limiter):
        raise RuntimeError("private redis credential and hostname")
    monkeypatch.setattr(app_module, "verify_shared_rate_limit_storage", fail)
    try:
        create_app(
            "production", environ=production_env,
            config_overrides={"RATELIMIT_STORAGE_URI": "memory://"},
        )
    except RuntimeError as exc:
        assert "shared rate-limit storage unavailable" in str(exc)
        assert "credential" not in str(exc) and "hostname" not in str(exc)
    else:
        raise AssertionError("production startup should fail closed")
