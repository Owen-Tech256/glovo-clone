# Marketplace

Multi-vendor commerce and on-demand delivery marketplace for Uganda (launch currency UGX).
Stack: Python, Flask, Jinja templates, HTML, CSS, JavaScript, PostgreSQL, SQLAlchemy, Flask-Migrate/Alembic.

**Current implementation status:** Identity migrations `0002`–`0005` are the foundation. Migration `0006_marketplace_core` adds the first working marketplace domain: customer registration/login, catalogue search, persistent carts, single-vendor checkout, order history, vendor applications and product management, rider applications and delivery status, operations review/dispatch, support tickets, finance records, promotion drafts, and fictional development seed data. This is an MVP foundation, not a production-complete marketplace. See `docs/MARKETPLACE_MVP_IMPLEMENTATION_REPORT.md`, `docs/LOCAL_RUN_GUIDE.md`, `docs/IMPLEMENTATION_PLAN.md`, and `docs/DECISIONS_NEEDED.md` for implemented scope, verification status, and remaining release blockers.

## Requirements

- Python 3.12
- PostgreSQL 16 (PostgreSQL is the only approved database)

## Setup

```powershell
# Windows PowerShell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements-dev.txt
Copy-Item .env.example .env
```

```bash
# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements-dev.txt
cp .env.example .env
```

Create two empty local databases and put their URLs in `.env`
(`DATABASE_URL` for development, `TEST_DATABASE_URL` for tests; the test database name must end in `_test`):

```bash
createdb marketplace_dev
createdb marketplace_test
```

## Everyday commands

```bash
flask --app wsgi.py db upgrade        # apply migrations
flask --app wsgi.py seed-dev          # development data (development/testing only)
flask --app wsgi.py run --debug       # start the server, then open /health
pytest                                # full test suite (needs TEST_DATABASE_URL)
pip check
pip-audit -r requirements.txt         # known-vulnerability scan (needs network)
```

Changing models: `flask --app wsgi.py db migrate -m "describe change"`, review the generated file, then `db upgrade`.
Never edit a migration that has already been applied; add a new one. Downgrades of destructive changes
may lose data, so document that in the migration.

## Before deploying

Production deployment is blocked until `docs/release_blockers.md` is cleared. The first item is shared, persistent rate-limit storage.
Missing specifications are listed in `docs/documentation_gaps.md`.

## Safety rules worth knowing

- If `APP_ENV` is unset the app starts as **production**, which requires a real `SECRET_KEY` (32+ characters) and `DATABASE_URL`.
- `seed-dev` refuses production, refuses any database whose name does not end in `_dev` or `_test`, and never runs at startup.
- Tests wipe the schema of `TEST_DATABASE_URL`. They refuse to run against any database not named `*_test`.
- `.env` is git-ignored. Do not commit it.

## Layout

```text
app/            application package (factory, config, extensions, security, errors, cli)
app/main/       health routes
app/models/     SQLAlchemy base, Identity and marketplace persistence models
app/marketplace/ customer, vendor, rider, admin, finance, support and commerce routes/services
app/seeding/    idempotent fictional development seed registry and environment guard
app/templates/  shared layout and marketplace pages
app/static/css/ tokens.css (provisional design tokens), base.css
migrations/     Alembic revisions 0001–0006 (Identity/audit plus marketplace core)
tests/          unit/ and integration/ (PostgreSQL required)
docs/           plan, decisions, conventions, contracts, manual checks
```


For Windows setup, demo accounts, and the MVP limitations, see [`docs/LOCAL_RUN_GUIDE.md`](docs/LOCAL_RUN_GUIDE.md). For a precise list of delivered features and unverified tests, see [`docs/MARKETPLACE_MVP_IMPLEMENTATION_REPORT.md`](docs/MARKETPLACE_MVP_IMPLEMENTATION_REPORT.md).
