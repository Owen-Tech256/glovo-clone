# Local Windows Run Guide

## 1. Prerequisites

- Python compatible with the pinned dependencies (the project baseline specifies Python 3.12).
- PostgreSQL 16.
- Two separate databases: `marketplace_dev` and `marketplace_test`.

## 2. Create the environment

Open PowerShell in the folder containing `wsgi.py` and `requirements.txt`:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements-dev.txt
Copy-Item .env.example .env
```

Edit `.env` and replace the placeholder database credentials with your local PostgreSQL credentials. Keep `DATABASE_URL` pointed at `marketplace_dev` and `TEST_DATABASE_URL` pointed at `marketplace_test`. Never point the test URL at development or production: the integration fixtures drop and recreate the test database's `public` schema.

## 3. Create tables and demo data

```powershell
flask --app wsgi.py db upgrade
flask --app wsgi.py seed-dev
flask --app wsgi.py run --debug
```

Open `http://127.0.0.1:5000/`.

### Fictional local demo accounts

The `seed-dev` command only runs when `APP_ENV` is `development` or `testing`, the explicit seed flag is enabled, and the database name ends in `_dev` or `_test`. It is refused in production. It is not run automatically.

After seeding, use one of these accounts with password `LocalDemoOnly-ChangeMe-123!`:

- `customer.demo@example.test` — customer shopping flow.
- `vendor.demo@example.test` — vendor owner; sample shop is already approved for product tests.
- `admin.demo@example.test` — operations manager; vendor and rider review, dispatch and support queues.
- `rider.demo@example.test` — rider role. A separate rider application still needs approval before assignment.

These accounts and products are fictional development fixtures. Never reuse their passwords outside a local environment.

## 4. Tests

```powershell
python -m compileall -q app migrations tests
python -m pytest tests/integration/test_migrations.py tests/integration/test_identity_schema.py tests/integration/test_marketplace_smoke.py -v
python -m pytest -v
```

PostgreSQL integration tests must run against `marketplace_test`. Tests are not considered passed until they have been executed in your local test environment.

## 5. Current MVP limits

- Checkout currently accepts items from one vendor per order; place separate orders for different vendors.
- Payment rows are internal records. No mobile-money or online payment provider is connected, and payment status must not be marked successful without a verified provider integration.
- Email delivery/password recovery, identity-document storage and verification, GPS collection, automated dispatch, commissions/payouts, refunds, and production shared rate-limit storage remain incomplete or blocked on approved provider/legal/operational decisions.
- Vendor and rider applications are recorded, but production verification requirements and secure document upload/review are not implemented.
- Promotions are drafts only; there is no ad billing or automated publication.
