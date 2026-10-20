# Contract: Foundation (phase 0)

| Field | `GET /health` | `GET /health/ready` | Error pages |
|---|---|---|---|
| Role required | none | none | none |
| Authentication / ownership | none | none | none |
| Input | none | none | none |
| Handler | `app/main/routes.py: health` | `app/main/routes.py: ready` | `app/errors.py` |
| Database | not touched | runs `SELECT 1`, writes nothing | none |
| Success | 200 `{"status": "ok"}` | 200 `{"status": "ready"}` | not applicable |
| Failure | not applicable | 503 `{"status": "unavailable"}`, no error details in the body | 400, 401, 403, 404, 405, 409, 413, 422, 429, 500 |
| Content type | JSON always | JSON always | HTML, or JSON when the client prefers `application/json` |
| CSRF | not applicable (GET) | not applicable (GET) | not applicable |
| Rate limit | exempt | exempt | applies to the route being limited (429 page) |
| Headers | `Cache-Control: no-store`, security headers, `X-Request-ID` | same | security headers, `X-Request-ID`; `Retry-After` on 429, `Allow` on 405 |
| Covering tests | `tests/integration/test_health_errors.py` F-08, F-19 | F-09 | F-10 to F-14 |

Error JSON shape: `{"error": {"code": <int>, "title": <str>, "request_id": <str>}}`.
Error HTML shows the code, title, a plain-language message and the request id as a support reference. Tracebacks and exception text are never shown.
