# Conventions

## Money (decision D-07)

- Launch currency: **UGX**. UGX has no minor unit, so `CURRENCY_EXPONENT = 0` and every amount is a whole number of shillings.
- Database type: `Numeric(14, 0)` (up to 99,999,999,999,999 UGX). Use `CHECK (amount >= 0)` where a negative value is invalid.
  The currency code is stored on each transaction record, not assumed.
- Python: use `decimal.Decimal` for every calculation. Never use `float` for money. Build `Decimal` values from strings or integers.
- **Rounding is not finalized.** Calculations that can produce fractions (percentages, discounts) must round to whole shillings
  at documented points. The rounding mode and whether rounding happens per line or per order total are pending owner approval
  (decision P-06). Until then no feature may invent a rounding rule.
- No commission rate, delivery charge, provider fee or refund rule is defined anywhere in the code. Those need owner approval (D-11).

## Time

- Store every timestamp as UTC in `timestamptz` columns (`TimestampMixin`).
- The display time zone for users is pending (proposal: Africa/Kampala, decision P-10). Convert only at the presentation layer.

## Identifiers (decision D-05)

- Internal key: integer identity column `id` (`PrimaryKeyMixin`). Never put it in URLs, forms or API-style responses.
- External identifier: `public_id` UUID (`PublicIdMixin`) on records that need one.
- A UUID is not authorization. Every route still checks authentication, role/permission and resource ownership.

## Database

- PostgreSQL only. `postgresql://` and `postgres://` URLs are rewritten to the psycopg 3 driver (`postgresql+psycopg://`).
- Constraint names follow `NAMING_CONVENTION` in `app/models/base.py`. PostgreSQL truncates identifiers at 63 characters.
- Schema changes go through Alembic migrations only. Do not edit applied migrations.

## Configuration

- Built from environment variables at app creation (`app/config.py`). See `.env.example`.
- Unset `APP_ENV` means production. Production refuses missing or placeholder secrets.
- Placeholder detection treats values starting with `change-me`, `replace-with`, `your-`, `dev-only` or `testing-` as placeholders.

## Security defaults

- Session cookies: `HttpOnly`, `SameSite=Lax`, `Secure` in production. Flask-Login session protection is `strong`.
- CSRF protection is on everywhere, including tests.
- Every response gets an `X-Request-ID` (an inbound value is kept only if it is 1-64 characters of letters, digits, `.`, `_`, `-`).
- Headers: `X-Content-Type-Options`, `X-Frame-Options: DENY`, `Referrer-Policy`, a strict `Content-Security-Policy`
  (no inline scripts or styles), `Permissions-Policy` denying camera, microphone and geolocation, and HSTS in production.
  Features that need an exception (for example geolocation for riders) must change the header deliberately with owner approval.
- Request logs record method, path, status and request id only. Never log query strings, bodies, cookies or authorization values.
- Rate limiting: the default in-memory storage is **not production-ready**. See `docs/release_blockers.md` RB-01.
- Request bodies are capped at 1 MiB by default (`MAX_CONTENT_LENGTH`). Upload routes will set their own limits.

## Frontend

- No frontend build system. Plain CSS with custom properties from `tokens.css`, small JavaScript modules by feature (none yet).
- No gradients, no emoji as interface icons, no inline styles, visible focus, status never by colour alone,
  `prefers-reduced-motion` respected. These rules are enforced by tests.
- Breakpoints (provisional): `sm` 40rem, `md` 64rem, mobile first.
