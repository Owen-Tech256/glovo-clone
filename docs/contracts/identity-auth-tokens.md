# Contract: Identity token persistence batch (`0003_auth_tokens`)

This batch adds token persistence only. It does **not** issue, email, consume, or revoke tokens and does not add authentication routes.

| Field | Specification |
|---|---|
| URL and method | None; database schema only |
| Role / permission required | Not applicable in this schema-only batch |
| Authentication and ownership check | Token services must require an active user and verify purpose, expiry, and single-use state before acting; service implementation is deferred |
| Persisted fields | `user_id`, `purpose`, unique SHA-256 token hash, `created_at`, `expires_at`, `used_at`, `revoked_at` |
| Validation rules | Purpose is `password_reset` or `email_verification`; expiry must be later than creation; raw token values must never be persisted |
| Database relationship | `auth_tokens.user_id` references `users.id` with `ON DELETE RESTRICT` |
| Index | Partial lookup index on `(user_id, purpose)` for rows with `used_at IS NULL AND revoked_at IS NULL`; expiration is checked by the query because PostgreSQL partial-index predicates cannot use non-immutable `now()` |
| Success | Migration `0003` upgrades cleanly after `0002`; metadata matches migration |
| Failure | Database constraints reject invalid purpose, non-positive lifetime, duplicate token hashes, and missing users |
| CSRF | Not applicable; no route is introduced |
| Rate limit | Not applicable to schema alone; token-issuing routes must be rate-limited in the service/routes batch |
| Covering tests | `tests/integration/test_identity_schema.py`, `tests/integration/test_migrations.py` |

## Security invariants for the later service batch

- Generate a cryptographically random 32-byte token and show/send the raw token only once.
- Persist only the lowercase/hex SHA-256 digest (64 characters), never the raw token.
- Consume atomically with a conditional update requiring matching purpose, unused, unrevoked, and unexpired state.
- Require the associated user to be active before consuming.
- An unauthenticated forgot-password request must not revoke previously issued reset tokens.
- A completed reset revokes the user's other reset tokens; signed-in password change revokes that user's reset tokens; signed-in verification resend revokes older verification tokens.
- Do not log token-bearing URLs or token values.
