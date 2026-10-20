# Identity migration 0005 implementation report

## Scope

Implements the approved Revision 6 / D-66 / D-76 / D-85 audit append-only database safeguards after migration `0004`:

- append-only `audit_retention_policy` table with positive retention days, non-empty approver and legal basis;
- database-generated `audit.retention_policy_approved` evidence for each policy insertion;
- trigger guards against audit row UPDATE/TRUNCATE and policy UPDATE/DELETE/TRUNCATE;
- direct-insert forgery guards for recorder-only audit actions;
- deletion denied unless the login is a member of `audit_maintenance`, a policy exists, and each deleted row is strictly older than the policy threshold;
- statement-level deletion evidence with count, oldest/newest deleted timestamps, policy id, retention days and operator login;
- privileged trigger functions use `SECURITY DEFINER`, an empty fixed `search_path`, qualified object names, no dynamic SQL, and revoked PUBLIC execution;
- migration downgrade is refused when the active Flask app configuration is production.

## Files changed

- `app/models/identity.py`: `AuditRetentionPolicy` metadata model.
- `app/models/__init__.py`: registers the model.
- `migrations/versions/0005_audit_append_only.py`: safeguards and policy table.
- `tests/integration/test_migrations.py`: expects migration head 0005.
- `tests/integration/test_identity_schema.py`: includes the policy table in schema expectations.
- `tests/integration/test_audit_append_only.py`: tests mutation guards, no-policy deletion denial, forged actions, policy validation and automatic approval evidence.
- `README.md`, `docs/IMPLEMENTATION_PLAN.md`: staged status updates.

## Not implemented / deployment caveats

- No production role provisioning is performed by the migration. Cluster roles and grants must be provisioned separately by a database administrator. In particular, the running app must use a restricted role and must not own the tables or functions.
- The `audit_maintenance` NOLOGIN role and named operator membership are deployment responsibilities. Role-dependent tests must run only on the isolated disposable cluster specified by Revision 6; they have not been run in this build environment.
- No retention days or legal basis are invented. The policy table starts empty; until an authorized owner records a valid policy, deletion is refused.
- A PostgreSQL superuser can bypass database controls. Database role separation and closure-evidence queries remain required.
- No audit-writing service or route integration is added.

## Verification status

Python compilation and ZIP integrity are checked in the build environment. PostgreSQL integration tests could not be run here because the environment does not have the project's Flask/PostgreSQL test dependencies and disposable PostgreSQL cluster. Do not interpret Batch 0004's reported test success as Batch 0005 test evidence. Batch 0005 remains prepared, not accepted, until the owner runs targeted and full tests, reviews the diff, and performs role-dependent tests on the approved disposable cluster or records them as not tested.
