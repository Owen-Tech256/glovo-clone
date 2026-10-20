# Identity migration 0004 implementation report

## Scope implemented

This batch implements only the approved Revision 6 `0004_audit_logs` schema after `0003_auth_tokens`. It creates the audit-log table, constraints, foreign key, JSONB/INET columns, and three query-supporting indexes. It does not implement audit-writing services or enforce append-only behavior; those are later approved work in `0005_audit_append_only`.

## Files changed

- `app/models/identity.py` — adds the `AuditLog` SQLAlchemy model.
- `app/models/__init__.py` — registers `AuditLog` for Alembic metadata.
- `migrations/versions/0004_audit_logs.py` — adds reversible migration `0004`, parent `0003`.
- `tests/integration/test_migrations.py` — expects migration head `0004` for upgrade and round-trip checks.
- `tests/integration/test_identity_schema.py` — verifies table shape, PostgreSQL types, constraints, foreign key, indexes, actor requirement, and a valid maintenance-label record.
- `docs/contracts/identity-audit-logs.md` — records schema and data-minimization contract, plus explicitly deferred safeguards.
- `docs/IMPLEMENTATION_PLAN.md`, `README.md` — update the staged implementation status.

## Security and scope boundaries

- `actor_user_id` uses `ON DELETE RESTRICT`, as Revision 6 specifies; the older preview table entry using `SET NULL` is superseded.
- At least one of `actor_user_id` and `actor_label` is required.
- `entity_id` is a public identifier stored as text; internal IDs must not be written there.
- Password hashes, authentication tokens and email addresses are prohibited from audit payload allowlists.
- This migration does not provide append-only enforcement. Do not describe the database as tamper-resistant until batch `0005` is separately implemented and its role-dependent PostgreSQL tests pass.
- Retention period and legal basis remain unresolved; this batch does not delete audit records.

## Local verification status

Static compilation and archive integrity checks can be performed in the build environment. PostgreSQL integration tests require the project's Windows virtual environment and dedicated disposable `_test` database/cluster. Do not treat tests as passed until the owner runs the commands in the handoff instructions. The prior batch's test results do not establish the result for this batch.

## Acceptance gate

Review the diff, run targeted migration/schema tests, then run the full test suite against the dedicated test environment. Accept this batch only if upgrade `0001 -> 0002 -> 0003 -> 0004`, downgrade-to-base and re-upgrade, and metadata comparison all pass. Do not start `0005` until this batch is reviewed and explicitly accepted.
