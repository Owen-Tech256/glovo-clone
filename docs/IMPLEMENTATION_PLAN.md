# Implementation Plan, Decision Register and Foundation Phase Plan

**Status:** Version 2, approved. Foundation (phase 0) is implemented. Identity Revision 6 is approved for staged implementation; the completed schema batches add migration 0002 user/role schema, migration 0003 auth-token persistence, migration 0004 audit-log persistence, and migration 0005 append-only audit safeguards; authentication services remain staged and production role provisioning/verification remains required. Phase 2 remains blocked until Identity acceptance is verified and the owner explicitly approves the transition.
**Decision register:** see `docs/DECISIONS_NEEDED.md` (supersedes section 1 below).
**Baseline documents read:** `prd.md`, `Architecture.md`, `Architecture_essential.md`, `Agents.md`, `Claude.md`, `README.md`, `Design/README`, `design_tokens.md`, `page_inventory.md`, `reference_register.md`, and the prompt pack: `README.md`, `backend_prompt.md`, `database_seed_prompt.md`, `frontend_prompt.md`, `integration_prompt.md`, `testing_security_prompt.md`.

## 0. Outstanding specifications (not available, not read)

| Item | Status | Effect |
|---|---|---|
| `doc.md` | Received and reviewed | See `docs/documentation_gaps.md`; proposed source-of-truth rank remains subject to the decision register. |
| `prompt.md` (version 2) | Received and reviewed | See `docs/documentation_gaps.md`; supersession status remains subject to the decision register. |
| `seed_data.md` | Received and reviewed | See `docs/documentation_gaps.md`; overlap with the seed prompt is documented. |
| `Design/` reference screenshots, brand, components | Missing | Visual design remains limited to provisional `design_tokens.md`. |
| Implementation prompts | **Received and read** | Requirements folded into this plan. |

## 1. Decision register

Moved to `docs/DECISIONS_NEEDED.md` (version 3: approved D-01..D-34, assumptions A-01..A-14, pending P-01..P-29, contradictions C-01..C-12).

## 2. Updated roadmap

Every phase ends with: tests run, migration round-trip, contract document in `docs/contracts/`, and the completion report from `Agents.md` section 9.

| Phase | Scope | Depends on | Gate decisions |
|---|---|---|---|
| 0 Foundation | Factory, config, extensions, health, base layout, tokens, error pages, test harness, baseline migration, seed skeleton | Owner approval | B-01..B-05 |
| 1 Identity and access (Revision 6 approved; implementation is staged) | Migrations 0002 users/roles, 0003 auth tokens, 0004 audit logs, and 0005 append-only safeguards; later batches: authentication services and UI; no production bootstrap command | 0 | See `docs/IDENTITY_REVISION_6_APPROVAL.md`; later stages retain their own acceptance gates |
| 2 Geography and customer profile | Categories, delivery zones, serviceability check service, customer profile, addresses | 1 | Launch zones; fee model (structure only until approved) |
| 3 Vendor onboarding | Application workflow, private document storage, admin review, vendor/staff memberships, approval gate | 1, 2 | Vendor document requirements |
| 4 Catalogue and discovery | Branches, products, availability/inventory, public listing and search of approved vendors only | 3 | Product types in scope |
| 5 Orders (core lifecycle) | Cart, checkout, server-side totals, order and item snapshots, order state machine, status history, in-web status timeline, development-only payment adapter | 2, 3, 4 | One-vendor-per-order rule; cancellation rules; P-06, P-07 |
| 6 Payment service boundary | Payment records, idempotency, webhook verification, reconciliation; real provider adapter only after selection | 5 | Provider, methods, cash on delivery |
| 7 Delivery | Rider onboarding, availability, dispatch rule, delivery state machine, proof of delivery | 5 | Dispatch rule; proof method |
| 8 Finance | Commission rules and snapshots, ledgers, refunds, payouts | 6, 7 | **All financial policies approved by owner** |
| 9 Growth and operations | Promotions, sponsored placements, reviews, support/disputes, notification delivery, analytics, exports | 5-8 | Promotion funding; channels; pricing |
| 10 Hardening | Security review, accessibility, load, backups, deployment | all | P-02, P-03 |

No phase was reordered or removed by the prompt pack. Additions only:

- **Every phase:** contract document in `docs/contracts/` using the integration-matrix columns (URL, method, role, fields, validation, handler or service, records read or written, success, errors, authorization failures, CSRF, covering tests); a seed layer for models that exist; the security checklist from `testing_security_prompt.md` applied to that phase; completion report with verified working, verified failing, not yet tested, and blocked.
- **Phase 1 adds:** production reference-data bootstrap and explicit admin creation (P-12), account status (P-16), seed markers (P-13), strong session protection, reset tokens kept out of logs.
- **Phase 2 adds:** labelled development zone fixtures (P-23).
- **Phase 3 adds:** private storage decision gate (P-18), retention and privacy decision (P-11).
- **Phase 5 adds:** the development payment adapter is labelled as simulated and is disabled by configuration in production, with a test. End-to-end approach decided (P-20).
- **Phase 6 adds:** payment state vocabulary decided (P-17).
- **Phase 10:** final security review and release gate. Security checks are continuous, not deferred to here.

Assumption to confirm: PRD FR-NOT-001 (P0, in-web status updates) is met in Phase 5 by the order timeline. The notifications module follows in Phase 9.

## 3. Proposed folder structure (Foundation only)

Only what Foundation needs is created. Other `Architecture.md` modules are added in the phase that needs them.

```text
marketplace/
├── app/
│   ├── __init__.py            # create_app(config_name=None)
│   ├── config.py              # Development / Testing / Production
│   ├── extensions.py          # db, migrate, csrf, login_manager, limiter
│   ├── cli.py                 # registers the seed-dev command
│   ├── errors.py              # central error handlers
│   ├── security.py            # security headers, request id
│   ├── main/
│   │   ├── __init__.py        # blueprint
│   │   └── routes.py          # /health, /health/ready
│   ├── models/
│   │   ├── __init__.py
│   │   └── base.py            # naming convention, mixins
│   ├── services/__init__.py
│   ├── seeding/
│   │   ├── __init__.py        # guard + seeder registry (empty in Foundation)
│   │   └── guard.py
│   ├── templates/
│   │   ├── base.html
│   │   ├── partials/_flash.html
│   │   └── errors/error.html
│   └── static/css/
│       ├── tokens.css         # from design_tokens.md
│       └── base.css
├── migrations/
├── tests/
│   ├── conftest.py
│   ├── unit/
│   └── integration/
├── docs/
│   ├── IMPLEMENTATION_PLAN.md
│   ├── DECISIONS_NEEDED.md
│   ├── conventions.md         # UGX money rules and timezone strategy
│   └── contracts/
│       ├── TEMPLATE.md
│       └── foundation.md
├── .env.example
├── .gitignore
├── pytest.ini
├── requirements.txt
├── requirements-dev.txt
├── wsgi.py
└── README.md
```

`tests/system/` is added in the phase that first needs it (P-20). Deviations from `Architecture.md`: seeding logic lives in `app/seeding/` behind the single `flask seed-dev` command (no `scripts/seed_dev.py`); `scripts/` is deferred until `create_admin` is built in Phase 1; `docs/` and `docs/contracts/` are added. No JavaScript file is created in Foundation because there is no working behaviour for it to enhance.

## 4. First migration and models

### 4.1 Metadata naming convention (set in `app/models/base.py`)

```python
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}
```

PostgreSQL truncates identifiers at 63 characters, so long table and column names must be checked when constraints are named.

### 4.2 Reusable mixins (no tables)

- Integer identity primary key `id`.
- `public_id` UUID, unique, not null, server default `gen_random_uuid()`. Added only to tables whose records are exposed externally.
- `created_at`, `updated_at`: `timestamptz`, UTC, server default `now()`.

### 4.3 Money and time rules (documented in `docs/conventions.md`, constants in config)

- `CURRENCY_CODE = "UGX"`, `CURRENCY_EXPONENT = 0` (no minor unit).
- Amounts: `Numeric(14, 0)` with `CHECK (amount >= 0)` where negatives are not valid. Currency stored per transaction.
- Timezone strategy: all timestamps stored as UTC `timestamptz`. Display zone is pending (P-10).
- Calculations use `Decimal`, never `float`. Rounding mode and rounding points are pending (P-06). No rates or fees are defined.

### 4.4 Baseline migration

- **Option A (recommended):** `0001_baseline` is an intentionally empty revision. It proves Alembic against PostgreSQL with the naming convention in place and enables a real upgrade/downgrade/upgrade test. Foundation has no business tables, so the seed skeleton seeds nothing.
- **Option B:** `0001` also creates the identity tables below. This pulls Phase 1 forward.

### 4.5 Preview: `0002_identity` (Phase 1, not built now)

| Table | Key columns and constraints |
|---|---|
| `users` | `id`, `public_id`, `email` (stored normalized to lowercase), unique on email, `password_hash`, `status` (pending P-16, replaces a boolean), `seed_key` (nullable, unique, pending P-13), `email_verified_at`, `last_login_at`, timestamps. No phone column. Phone later goes in a separate verified-contact table. |
| `roles` | `id`, unique `code`, `name` |
| `permissions` | `id`, unique `code` |
| `role_permissions` | composite unique (`role_id`, `permission_id`), FKs |
| `user_roles` | composite unique (`user_id`, `role_id`), FKs. Subject to P-05. |
| `password_reset_tokens` | `user_id` FK, `token_hash`, `expires_at`, `used_at` (single-use) |
| `audit_logs` (Revision 6, migration `0004`) | `id`, `public_id`, nullable `actor_user_id` FK (`ON DELETE RESTRICT`), nullable `actor_label`, `action`, `entity_type`, public `entity_id`, `before_data` / `after_data` / `event_metadata` (JSONB), `ip_address` (INET), `request_id`, `created_at`. At least one actor identifier is required. Append-only enforcement and controlled retention evidence are implemented by `0005`; production role separation and deployment verification remain separate release requirements. |

Login goes through a service function that resolves an identifier to a user. Email is the only strategy now. A phone strategy can be added later without changing callers.

## 5. Dependencies and commands

### 5.1 Dependencies

Versions were checked on PyPI on 2026-10-09 and chosen to be at least 14 days old. They are re-verified at install time and checked with `pip check`.

`requirements.txt`

```text
Flask==3.1.3
Werkzeug==3.1.9
Flask-SQLAlchemy==3.1.1
SQLAlchemy==2.0.54
Flask-Migrate==4.1.0
alembic==1.20.0
psycopg[binary]==3.3.6
Flask-Login==0.6.3
Flask-WTF==1.3.0
Flask-Limiter==4.1.1
python-dotenv==1.2.3
```

`requirements-dev.txt`

```text
-r requirements.txt
pytest==9.1.1
pip-audit==2.10.1
```

SQLAlchemy is pinned to 2.0.x. Release 2.1.0 is under three weeks old and Flask-SQLAlchemy 3.1.1 has not been verified against it.

Not added in Foundation: `email-validator` (Phase 1 forms), a production WSGI server (P-03), Redis or any shared store (P-02), any task queue.

### 5.2 Commands

```powershell
# Setup (Windows PowerShell; bash equivalents are the same minus activation path)
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements-dev.txt
pip check
pip-audit -r requirements.txt
Copy-Item .env.example .env

# Databases (local only)
createdb marketplace_dev
createdb marketplace_test

# Migrations
flask --app wsgi.py db init
flask --app wsgi.py db migrate -m "baseline"
flask --app wsgi.py db upgrade

# Seed (development/testing only)
flask --app wsgi.py seed-dev

# Tests
pytest

# Run
flask --app wsgi.py run --debug
```

The sandbox used for verification has no PostgreSQL yet. PostgreSQL 16 is available from the system package repository and will be installed there for testing. If installation fails, that will be reported and no database-dependent test will be claimed as passing.

### 5.3 Configuration (`.env.example`, placeholders only)

`APP_ENV`, `SECRET_KEY`, `DATABASE_URL`, `TEST_DATABASE_URL`, `RATELIMIT_STORAGE_URI`, `LOG_LEVEL`, `SITE_NAME`. Production refuses to start when `SECRET_KEY` or `DATABASE_URL` is missing or still a placeholder. Session cookies: `HttpOnly`, `SameSite=Lax`, `Secure` in production. Security headers and a request ID are added to every response.

## 6. Foundation acceptance tests

All run with `pytest` against a real PostgreSQL test database.

**Factory and configuration**
- F-01 `create_app` succeeds for development, testing and production configs.
- F-02 An unknown config name raises a clear error.
- F-03 Production fails to start without `SECRET_KEY` or with a placeholder value.
- F-04 Production sets `Secure`, `HttpOnly` and `SameSite` on session cookies.
- F-05 The testing config refuses to use the development database (name guard).
- F-06 db, migrate, csrf, login_manager and limiter are registered on the app.
- F-07 CSRF is enabled under testing: a state-changing request to a test-only route without a token is rejected.

**Health and errors**
- F-08 `GET /health` returns 200 and a small JSON body with no configuration data.
- F-09 `GET /health/ready` returns 200 with the database up and 503 with the database unreachable, with no error details in the body.
- F-10 Unknown URL returns an HTML 404 using the base layout.
- F-11 `abort(403)` and a disallowed method render their error pages.
- F-12 An unhandled exception returns a generic 500 page with no traceback in production.
- F-13 Error responses include the request ID. JSON is returned when the client asks for JSON.
- F-14 Exceeding a rate limit returns the 429 page.

**Templates, tokens and design rules**
- F-15 `base.html` has `lang`, viewport meta, skip link and a `main` landmark.
- F-16 `tokens.css` is served and defines the tokens from `design_tokens.md`.
- F-17 Static CSS and templates contain no gradients and no emoji.
- F-18 Text/background token pairs meet WCAG 2.x AA contrast (4.5:1 for text).
- F-19 Security headers are present on responses.

**Migrations**
- F-20 `upgrade head` succeeds on an empty database.
- F-21 `downgrade base` then `upgrade head` round-trips.
- F-22 No pending model changes: autogenerate diff is empty.
- F-23 Metadata uses the approved naming convention.

**Seed command**
- F-24 `seed-dev` exits non-zero and writes nothing under the production config.
- F-25 `seed-dev` runs twice under development/testing with exit 0 and unchanged database state. It states that no seeders are registered and nothing was seeded.
- F-29 A seeder that raises is rolled back, the command exits non-zero, and the message contains no secrets.
- F-30 `seed-dev` refuses when the database name does not end in `_dev` or `_test` (if B-07 approved).
- F-26 Seeders are not invoked during `create_app` (startup spy).

**Security and design rules (added from the prompt pack)**
- F-31 Production config has `DEBUG` and `TESTING` off.
- F-32 `base.css` defines visible keyboard focus and a `prefers-reduced-motion` rule.
- F-33 Templates contain no inline `style` attributes.
- F-34 Request logs record the path only, with no query string, body, cookie or authorization values.

**Environment**
- F-27 `pip check` reports no broken requirements. `pip-audit` reports no known vulnerabilities (command, if approved).
- F-28 `.env.example` lists every variable the config reads, with placeholders only.

**Manual (reported separately, not claimed as automated)**
- M-01 Error page layout at 320, 768 and 1280 px widths, keyboard focus visible. No browser is available in the sandbox, so I will not claim this was checked. A manual checklist will be provided.

## 7. Completion report

When Foundation is built, the report follows `Agents.md` section 9 and separates verified working, verified failing, not yet tested, and blocked: summary, files changed, behaviour, database, security, exact commands and results, not tested, risks, owner decisions needed.

## Marketplace MVP build overlay (2026-10-14)

The codebase now includes a first marketplace-domain implementation in migration `0006_marketplace_core` and the `app.marketplace` blueprint. This adds a usable local storefront and initial customer/vendor/rider/operations/support/finance flows while preserving the approved modular Flask architecture. It does **not** waive the Identity batch acceptance gates above: Batch 0005's PostgreSQL integration tests and full suite still need local verification before the next Identity batch is accepted. The implementation report and `docs/LOCAL_RUN_GUIDE.md` identify current limits and verification commands.
