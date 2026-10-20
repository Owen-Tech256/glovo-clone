# Release blockers

Production deployment is **blocked** until every item below is closed. This list is maintained alongside `DECISIONS_NEEDED.md`.

| ID | Blocker | Why | Closed when |
|---|---|---|---|
| RB-01 | Shared, persistent rate-limit storage (decision P-02, assumption A-14). | The default `memory://` storage is per process. With several workers, or after a restart, limits reset or divide, so login and password-reset throttling is not effective. The application logs a warning at startup under production to keep this visible. It is not production-ready. | A shared store is chosen, configured through `RATELIMIT_STORAGE_URI`, and a test or documented check shows limits holding across workers. |
| RB-02 | Hosting, HTTPS and proxy configuration (P-03). | HSTS and `Secure` cookies assume HTTPS. Behind a reverse proxy the client IP seen by the rate limiter is the proxy's address unless trusted proxy headers are configured, which would make per-IP limits wrong. | Hosting decided, TLS in place, proxy header handling configured and tested. |
| RB-03 | Password-reset email provider (P-01). | Reset links cannot be delivered without one. Production keeps reset disabled until a provider is approved. | Provider recorded in the decision register and an adapter implemented and tested. |
| RB-04 | Security review of the provisional Foundation assumptions A-01 to A-05 and A-07 to A-13. | Accepted as provisional technical decisions, subject to review and testing. | A recorded security review. |
| RB-05 | No development seed data or `.test` accounts in production. | Seed accounts have known-by-developers credentials. | A deployment check confirms none exist (see the Identity proposal, section 6). |
| RB-06 | Dependency audit clean at release time. | Advisories change. | `pip-audit -r requirements.txt` is re-run on the release commit and reports nothing unresolved. |
| RB-07 | Production access logs must not record password-reset or verification tokens (D-46). | The WSGI server and any reverse proxy write their own access logs, which the application cannot filter. Verified on the Foundation code: the development server's access log prints the full path and query string. | Production server and proxy log settings mask or omit the sensitive paths and query strings, and a documented deployment check confirms it. Needed before the Identity phase goes live. |

Blockers owned by later phases (payment provider, financial policies, storage for private documents, data retention) are tracked in `DECISIONS_NEEDED.md`.
