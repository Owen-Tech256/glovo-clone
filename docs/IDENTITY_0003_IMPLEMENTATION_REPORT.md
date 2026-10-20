# Identity migration 0003 implementation report

## Scope

This batch adds only the approved `0003_auth_tokens` schema after `0002_users_roles`:

- `auth_tokens` table with user FK (`ON DELETE RESTRICT`), approved purpose check, unique 64-character token hash, UTC timestamps, and expiry-after-creation check.
- Partial index for unused and unrevoked token lookup by user and purpose.
- SQLAlchemy model registration and migration-head expectations.
- PostgreSQL integration coverage for schema, foreign key, index, invalid purpose, invalid expiry, duplicate token hash, and migration round-trip.
- Schema contract documenting the boundary between persistence and the later token service.

## Explicitly not implemented

- Token generation, token hashing/verification services, atomic consumption service, or revocation workflows.
- Registration, sign-in, sign-out, password reset/change, email verification delivery, authorization services, audit-log migrations, audit triggers, UI, production administrator bootstrap, or Phase 2 geography.
- Production shared rate-limit storage selection/deployment verification.

## Files changed

- `app/models/identity.py`
- `app/models/__init__.py`
- `migrations/versions/0003_auth_tokens.py`
- `tests/integration/test_migrations.py`
- `tests/integration/test_identity_schema.py`
- `docs/contracts/identity-auth-tokens.md`
- `docs/IDENTITY_0003_IMPLEMENTATION_REPORT.md`

## Validation status in the archive-building environment

- Python syntax compilation: to be run after packaging.
- `pytest`: not run here because Flask and psycopg are not installed in this environment.
- PostgreSQL migration upgrade/downgrade/re-upgrade: not run here because no dedicated test PostgreSQL database is available.

The previously reported 112-pass result applies to the preceding `0002` baseline; it is not a test result for this new `0003` batch. Run the commands in the handoff instructions in the project's Windows virtual environment against the dedicated `_test` database before accepting this batch.

## Acceptance gates

- Full test suite passes with the dedicated disposable PostgreSQL test database.
- `0001 -> 0002 -> 0003`, downgrade to base, and re-upgrade all pass.
- Alembic metadata comparison reports no pending model changes.
- Review confirms no raw token values are stored and no authentication/token service was added prematurely.
- Production release blockers remain open as documented in `docs/release_blockers.md` and `docs/IDENTITY_REVISION_6_APPROVAL.md`.
