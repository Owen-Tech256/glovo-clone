# Identity and Access Phase: Proposal (Phase 1), revision 6

**Status: APPROVED FOR IMPLEMENTATION on 2026-10-12. This document is the approved Identity Phase Revision 6 plan. The Foundation implementation was unchanged at the time of approval; implementation must preserve its architecture and proceed in small, tested batches.**

What changed in revision 6:
1. **D-75 and D-80 approved and applied:** `failed_attempts` and the five-failure rule are gone. Forgot-password never revokes tokens (section 2.2, 5.2).
2. **D-76 safeguards documented and prototyped** (section 2.4): fixed empty `search_path`, narrow execution rights, no dynamic SQL, role separation, forgery and policy protection, exact deletion thresholds and evidence. The prototype caught one bug, now fixed in the design.
3. **D-78:** the licence check is finished. **The condition is not met**, so `zxcvbn` is not approved and nothing is added (Appendix A.8).
4. **D-81 approved:** password change limited to 5 attempts per user per hour, with an IP-based limit proposed (D-82).
5. **D-79 completion:** shared-store verification and fail-closed behaviour (section 5.6), and the fuller `seed-dev` report (section 12.1).
6. **Role-dependent tests** run on a separate disposable cluster (section 9.1).
7. Exact scope (section 12), final outstanding risks (section 14).

How to read it:
- **[Dxx approved]** means you decided it. The exact value is in register section 8.
- **Decision status (2026-10-12):** D-78 is rejected (do not add `zxcvbn`); D-82, D-83, D-84, D-85, the restricted disposable test-cluster approach, and O-1 are approved. See `docs/DECISIONS_NEEDED.md` for the dated confirmation record.
- Open gaps stay open and are named: G-01 profile fields, G-04 display timezone, G-22 support or recovery contact, G-23 word-list licence.

## 1. Scope

**In:** registration, sign-in, sign-out, session expiry, password hashing, email verification with resend [D-48 approved], password reset, signed-in password change [D-48 approved], minimal `/account` [D-45, D-73 approved], many roles per user [D-35], role and permission checks, account statuses [D-39], audit log, one token table [D-43], enumeration protections [D-40, D-64], generic sign-in failures [D-41, D-53], log masking for token URLs [D-46, D-69], development accounts through `seed-dev` [D-37, D-38, D-71].

**Out:** vendor and rider applications; any admin page [D-44]; production bootstrap and administrator-creation commands [D-36]; an email provider; phone login; multi-factor authentication; social login; remember-me (not in Phase 1, D-74); profile editing (G-01); self-deactivation; idle timeout (none in Phase 1, D-74).

**Operational roles stay blocked [D-35, D-67 approved].** The role-assignment service refuses `vendor_owner`, `vendor_staff` and `rider` unconditionally in Phase 1, with no override. They are lifted only in the phase that supplies the approved onboarding record and the approved authorization rules.

## 2. Migration design

Four revisions after `0001_baseline` [D-72 approved]. Each can be reviewed and reverted on its own, subject to the protections in section 2.5. All timestamps are `timestamptz` (UTC). Names follow the approved convention.

### 2.1 `0002_users_roles`

**`users`**: `id` identity key; `public_id` UUID unique; `email` varchar(254) not null unique with `CHECK (email = lower(email))`; `password_hash` text not null; `status` varchar(16) not null default `active`, `CHECK` in (`active`, `suspended`, `disabled`) [D-39]; `status_changed_at` not null; `email_verified_at` null (null means unverified); `last_login_at` null; `session_version` integer not null default 0, `CHECK (>= 0)`; `created_at`, `updated_at`.
No phone column. Phone later means a separate verified-contact table and a second lookup strategy in the sign-in service, so this table does not change [D-03].

**`roles`**: `id`, `code` varchar(40) unique with a lowercase-letters-and-underscore check, `name` varchar(80), `created_at`.
**`permissions`**: `id`, `code` varchar(60) unique, `description`, `created_at`.
**`role_permissions`**: composite primary key (`role_id`, `permission_id`), foreign keys `ON DELETE RESTRICT`.
**`user_roles`**: composite primary key (`user_id`, `role_id`), foreign keys `ON DELETE RESTRICT`, `granted_at`. Many roles per user [D-35]. Index on `role_id`.

### 2.2 `0003_auth_tokens` [D-43, D-63 approved]

**`auth_tokens`**: `id`; `user_id` FK `ON DELETE RESTRICT`; `purpose` varchar(32), `CHECK` in (`password_reset`, `email_verification`); `token_hash` char(64) unique (SHA-256 of a 32-byte random token, never the token); `created_at`; `expires_at` with `CHECK (expires_at > created_at)`; `used_at` null; `revoked_at` null. Index on (`user_id`, `purpose`) limited to active rows.
Active means `used_at` and `revoked_at` are null and `expires_at` is in the future.
**Atomic consumption:** `UPDATE ... SET used_at = now() WHERE token_hash = ? AND purpose = ? AND used_at IS NULL AND revoked_at IS NULL AND expires_at > now() RETURNING id`. No row returned means unusable. Prototyped: the first call returned the row, the second returned none.
**Revocation [D-63 approved; correction D-80 approved]:** only an authenticated or token-holding action may revoke a token.
- Forgot-password is unauthenticated. It issues a new reset token and **does not revoke earlier ones**, otherwise anyone could invalidate a victim's emailed link by requesting resets for the victim's address. The limit of 3 per hour per email caps the number of live reset tokens at 3. (Revision 4 revoked older tokens here, which conflicts with your rule that unauthenticated requests must not revoke another user's valid token.)
- A completed reset revokes all that user's reset tokens. Possession of the token is the proof.
- A signed-in password change revokes that user's reset tokens.
- Verification resend is signed in, so it revokes that user's older verification tokens.
- Moving a user to `disabled` revokes all their active tokens (administrator action).
- Consuming any token requires an active account, otherwise the generic failure is returned.

### 2.3 `0004_audit_logs`

**`audit_logs`**: `id`; `public_id` UUID unique; `actor_user_id` FK `ON DELETE RESTRICT`, null; `actor_label` varchar(80) null (for `seed-dev` and maintenance operators); `CHECK (actor_user_id IS NOT NULL OR actor_label IS NOT NULL)`; `action` varchar(80); `entity_type` varchar(40); `entity_id` varchar(64) (the entity's public id as text, never the internal id); `before_data`, `after_data`, `event_metadata` JSONB null; `ip_address` inet null; `request_id` varchar(64) null; `created_at`.
Indexes: (`entity_type`, `entity_id`, `created_at`), (`actor_user_id`, `created_at`), (`action`, `created_at`).
Allowlist rule: each entity has a fixed list of fields allowed in `before_data` and `after_data`. `password_hash`, tokens and email addresses are never allowed.
IP address is stored only for audited events [G-21 approved]. No audit data is deleted until an approved retention period and legal basis exist (RB-09).

### 2.4 `0005_audit_append_only` [D-66, D-76 approved with safeguards]

**Your D-76 conditions, exactly:** the `audit_maintenance` role, an empty `audit_retention_policy` table and automatic deletion records. The application role must not grant itself maintenance privileges or switch to the maintenance role. A separately authorized operator is required. The approved retention threshold is enforced in the database. Deletion activity is recorded. With no approved retention policy, nothing may be deleted. **You also approved** the `SECURITY DEFINER` recorder, the forgery guard, the extended closure-evidence queries and revocation of `CREATE` on the public schema, and required these five safeguards to be documented and tested before implementation.

**Design (items marked (R) are approved under D-85, confirmed 2026-10-12):**

| Safeguard | How it is met |
|---|---|
| 1. Fixed, safe `search_path` | Every privileged function sets `search_path` to the **empty string** (R: stronger than a pinned list) and schema-qualifies every table and function (`public.audit_logs`, `pg_catalog.now()`). `session_user` and `current_user` are used unqualified because they are SQL keywords that do not depend on the path |
| 2. Narrow execution rights and no SQL injection | (R) `REVOKE ALL ON FUNCTION ... FROM PUBLIC` for every privileged function. Only table triggers run them. No role, including the application and maintenance roles, holds `EXECUTE`. The functions contain **no dynamic SQL**: no `EXECUTE`, no `format()`, no string-built statements. They read only trigger rows and the policy table through static, qualified queries |
| 3. Role separation | Three roles with different rights. **Table owner / migrator**: owns the tables and functions, runs migrations, writes the policy table, never used by the running application. **Application role**: `SELECT` and `INSERT` on `audit_logs` only. **`audit_maintenance`**: `NOLOGIN` group role with `SELECT` and `DELETE` on `audit_logs` and `SELECT` on the policy table, no `INSERT`. An operator reaches it only by temporary membership granted by a database administrator under change control |
| 4. No forged records, no unauthorized policy changes | A `BEFORE INSERT` trigger rejects `audit.maintenance_run` and (R) `audit.retention_policy_approved` rows unless written by the database recorders, for **every** role including the table owner (it checks trigger depth). The policy table is writable only by the owner role. (R) It is append-only (no `UPDATE`, `DELETE` or `TRUNCATE`), requires positive days, a non-empty approver and legal basis, and (R) the database itself writes an `audit.retention_policy_approved` row for every approval |
| 5. Thresholds, evidence, and no deletion without a policy | `UPDATE` and `TRUNCATE` are refused for every role. `DELETE` is refused for every role except `audit_maintenance`. Even that role succeeds only if an approved policy row exists, only for rows **strictly older** than the newest policy's retention days, and a delete touching any row inside the period fails as a whole. The recorder, running as `SECURITY DEFINER`, writes `audit.maintenance_run` with count, (R) oldest and newest deleted times, (R) policy id and retention days, and the operator's login name. The policy table is **empty in Phase 1**, so nothing can be deleted |

**Prototype results (real login roles, scratch database, removed afterwards).** One bug was found and fixed: `pg_catalog.session_user` is not valid syntax. With the empty `search_path` the first version of the policy recorder failed. The failure was safe, because without a policy nothing can be deleted, and it is corrected in the design above. After the fix:
- **Static checks on all six privileged functions:** owner is the table-owner role; `search_path` is fixed to empty; `EXECUTE` is held by neither `PUBLIC`, the application role nor the maintenance role; no dynamic SQL.
- **Application role:** could not call the recorder functions directly (permission denied); creating a temporary table named `audit_logs` in its own session did not weaken the guards; it could not write the policy table, grant itself the maintenance role, switch to it, switch session authorization, create or alter roles, change the table or its triggers, create objects in the schema, or insert a recorder-only audit action.
- **Policy table:** an update, a delete and an empty-approver insert were all refused; the owner's valid insert succeeded and the database wrote `audit.retention_policy_approved` with the approver and days.
- **Forgery:** the table owner and the application role both failed to insert `audit.maintenance_run` and `audit.retention_policy_approved` directly.
- **Threshold, tested inside one transaction so `now()` is identical:** a row exactly at the 5-day boundary was refused ("within the retention period"); a row one second older was deleted.
- **Operator run:** with temporary membership and a 5-day policy, deleting only older rows succeeded and the database recorded `deleted: 2`, oldest and newest deleted times, policy id, `retention_days: 5` and the operator's login name. Before any policy existed, every delete was refused.

**RB-08 closure evidence (read-only queries, validated):** owner of `audit_logs`, the policy table and each privileged function; the application role's `superuser`, `createrole`, `createdb` and `bypassrls` flags (all false); its `UPDATE`, `DELETE`, `TRUNCATE` and `TRIGGER` privileges on `audit_logs` and its write privileges on the policy table (all false); its `CREATE` privilege on the schema (false); its `EXECUTE` privilege on each privileged function (false); membership in `audit_maintenance` (false); current members of `audit_maintenance` (none outside a maintenance window); each audit trigger's enabled state (`O`; a disabled trigger shows `D`).

**Limits stated plainly:**
- In development and tests the application connects as the table owner, so ordinary tests prove the triggers but not production role separation. The role-dependent tests run on a disposable cluster (section 9.1). Otherwise they are reported **not tested**.
- Roles and grants belong to the database cluster, so a deployment script creates them, not a migration. The script also runs `REVOKE CREATE ON SCHEMA public FROM PUBLIC`.
- A database superuser can bypass any of this. The operator login name in the record is only as good as the rule that each operator has a named login, never a shared one.
- Test fixtures wipe the schema with `DROP SCHEMA`, which the triggers do not block.

### 2.5 Dependencies and rollback risks [D-72 approved; protections D-77 approved]

| Revision | Depends on | Creates | Downgrade effect | Risk and protection |
|---|---|---|---|---|
| `0002` | `0001` | users, roles, permissions, links | Drops all accounts and role grants | Cannot be reached in production: `0004` and `0003` hold foreign keys to `users` and must be downgraded first, and `0004` is refused in production |
| `0003` | `0002` | `auth_tokens` | Drops all tokens | Low risk. Tokens are short-lived |
| `0004` | `0002` | `audit_logs` | **Destroys all audit data** | Refused under the production configuration even with confirmation. Elsewhere refused if rows exist unless `AUDIT_DOWNGRADE_CONFIRM=destroy-audit-data` is set |
| `0005` | `0004` | triggers, `audit_retention_policy` | Removes append-only protection and the policy table | Refused under the production configuration |

A refused downgrade leaves `alembic_version` and every table unchanged. **Prototyped in a throwaway copy of the project:** with an empty table the downgrade ran; with a row and no confirmation it was refused and nothing changed; with confirmation outside production it ran; under the production configuration it was refused even with confirmation, and the version and table were unchanged. Upgrades are always additive.

### 2.6 Roles and permissions manifest [D-51 approved]

`app/auth/manifest.py`, read by `seed-dev`. No bootstrap command is built [D-36].

| Permission | Meaning | Held by (Phase 1) |
|---|---|---|
| `roles.assign` | Grant or revoke an allowed role on another user | `super_admin` |
| `users.suspend` | Move an active user to `suspended` | `super_admin` |
| `users.reinstate` | Move a suspended user to `active` | `super_admin` |
| `users.disable` | Move an active or suspended user to `disabled` | `super_admin` |

Roles: `customer`, `vendor_owner`, `vendor_staff`, `rider`, `support_agent`, `operations_manager`, `finance_operator`, `super_admin`. `super_admin` only holds these permissions [G-20 approved, D-68].

## 3. Privileged actions: safeguards and audit records [D-68 approved]

All seven safeguards are retained and tested (I-44 to I-48):
- SG-1 A user cannot change their own status or roles.
- SG-2 Phase 1 role assignment may grant only `customer`, `support_agent`, `operations_manager` and `finance_operator`. It refuses `vendor_owner`, `vendor_staff`, `rider` and `super_admin`.
- SG-3 `super_admin` can come only from the unbuilt, unapproved bootstrap path or a test fixture. No web or service path grants it.
- SG-4 Role-to-permission mapping changes only through the code manifest.
- SG-5 The last active `super_admin` cannot be suspended, disabled, or have the role revoked.
- SG-6 Every grant, revoke and status change is audited with actor, target, previous and new values and reason.
- SG-7 Permissions are checked server-side at call time against the actor's current roles, so revocation takes effect on the next call even with a valid session.

**Audit record catalogue [D-65 approved provisionally]:**

| Action | Entity | Allowed data |
|---|---|---|
| `user.registered` | user | `after_data`: status, verified flag |
| `user.email_verified` | user | `after_data`: verified flag |
| `auth.password_changed`, `auth.password_reset` | user | metadata only: request id |
| `user.status_changed` | user | `before_data`, `after_data`: status. Metadata: reason, revoked token count |
| `user.role_granted`, `user.role_revoked` | user | metadata: role code |
| `auth.login_blocked` | user | metadata: `suspended` or `disabled`, only when the correct password was presented |
| `audit.maintenance_run` | audit | written by the database: operator, count, newest deleted time |

Not audited, application log only: successful sign-in, sign-out, failed attempts (email hashed). **Successful sign-in auditing and repeated failed attempts are revisited in the security review (RB-04).** No password, raw token or other authentication secret is ever logged or audited.

## 4. Account status and verification [D-39 approved]

Two independent facts: `status` (`active`, `suspended`, `disabled`) and `email_verified_at`.

| Transition | Who | Reason | Recorded |
|---|---|---|---|
| active to suspended | `users.suspend` | required | `user.status_changed` |
| suspended to active | `users.reinstate` | required | `user.status_changed` |
| active or suspended to disabled | `users.disable` | required | `user.status_changed` |
| disabled to anything | not allowed in this phase (retention policy undecided) | | |

No web page [D-44]. A service function and its tests exist. The audit log is the one record of the reason. Every change increments `session_version`, and the user loader returns no user unless `status = 'active'`, the session's version matches, and the session is within its maximum age. Suspended or disabled users are signed out on the next request.

## 5. Security design

### 5.1 Policy values [D-74 approved, exact]

| Item | Value |
|---|---|
| Password length | 12 to 128 characters. Must differ from the email |
| Composition rules | None |
| Password strength check | **`zxcvbn` is not approved and not added.** The licence condition is not met (Appendix A.8) [D-78 rejected]. If approved: score of at least 3, first 72 characters evaluated, the entire original password hashed, length policy 12 to 128 unchanged, offline |
| Sign-in | 5 per minute per IP and 10 per hour per email. Generic errors. No permanent account lockout |
| Forgot-password | 3 per hour per email, 5 per hour per IP |
| Registration | 5 per hour per IP |
| Verification resend | 3 per hour per user |
| Reset and verification submissions | 10 per hour per IP, plus the token-level protections in section 5.2 |
| Signed-in password change | **5 attempts per user per hour** [D-81 approved]. Additional IP-based protection: proposed 20 per hour per IP [D-82 approved]. Only attempts that reach the current-password check count. Page views and form-validation failures do not, so ordinary typing mistakes do not lock a user out |
| Reset-token lifetime | 1 hour |
| Verification-token lifetime | 24 hours |
| Session maximum age | 24 hours **absolute** from sign-in, enforced server-side from a timestamp in the signed session, so activity does not extend it |
| Idle timeout | None in Phase 1. Documented limitation for the security review |
| Remember-me | Not included |
| Rate-limit storage | Shared storage in production. The in-memory limiter is not production-ready (RB-01) |

### 5.2 Token-level protections [D-75 approved: failed-attempt rule removed; D-80 approved]

**Approved as you stated:** exact-hash lookup, generic failures, token expiry, revocation, and atomic single-use consumption.

**Your question: how can `failed_attempts` be incremented safely when an incorrect token hash matches no stored row?** It cannot. A wrong token matches no row, so there is nothing to increment, and it would be wrong to blame any user for it. Unknown tokens are counted nowhere. They are limited only by the per-IP limit (10 per hour).

The only requests that could be counted per token are submissions that already prove possession of a valid token: a POST to `/password/reset` that carries the session reference created by a valid link. A stranger cannot reach that state, so a counter there could not be used to revoke someone else's token. A narrow counter would therefore be technically safe. But it protects nothing. Someone who holds the valid token and is rejected (weak password, mismatched confirmation) gains nothing by retrying. The counter would only add a column, a write on every failure, a concurrency case, and a way for a legitimate user to lock out their own link by mistyping.

**Approved: the five-failure revocation rule and the `failed_attempts` column are removed.**

**A related problem your principle exposed [D-80 approved].** Revision 4 had forgot-password revoke older reset tokens. Forgot-password is unauthenticated, so anyone could invalidate a victim's emailed link by requesting resets for the victim's address. That breaks your rule that unauthenticated requests must not revoke another user's valid token. The plan now makes forgot-password add a token and never revoke one (section 2.2). This changes revocation wording that you approved under D-63, so it needs your confirmation.

**Token-level protections in the plan:**
- TP-1 Exact SHA-256 hash lookup of 256-bit random tokens. No partial matching.
- TP-2 Every failure returns the same generic response.
- TP-3 The atomic consume also matches `purpose`, so a verification token can never be consumed as a reset token, or the reverse.
- TP-4 Expiry, revocation and single use are checked in the same atomic statement.
- TP-5 Consumption also requires an active account.
- TP-6 The submit page requires CSRF and the session reference. The POST re-validates the token, so a copied cookie is useless once the token is consumed, revoked or expired.
- TP-7 Unauthenticated requests can add tokens through the rate-limited issuance paths and can do nothing else to a token.

### 5.3 Core behaviour
- **Password strength check [D-78 conditional, not approved]:** if approved, applied after the length check. Rule: strength score of at least 3. The library is given only the first 72 characters (its documented limit), with the email local part as user input. **The entire original password is what gets hashed**, never the truncated one. Passwords of 12 to 128 characters are accepted by length. A password whose first 72 characters are weak is rejected even if its tail is strong, which is conservative. Until D-78 is closed, implementation uses the length rule and the "differs from the email" rule only, and says so in the report.
- **Password-change limiter [D-81 and D-82 approved]:** keyed by user (5 per hour) and by IP (20 per hour). Neither limit locks an account permanently. Passwords and tokens are never logged.
- **Hashing:** Werkzeug (approved). Verified on the installed version: scrypt, parameters `32768:8:1`, 162-character hash.
- **Email validation:** `email-validator` [D-70 approved], DNS lookups off. The version is pinned only after checking its release status and known vulnerabilities at implementation. No version is chosen yet.
- **Sign-in:** one response for unknown email, wrong password, suspended and disabled [D-41, D-53]. A dummy hash check runs for unknown emails. The session is cleared before `login_user`. `next` is accepted only as a same-site relative path.
- **Blocked accounts:** a correct password on a suspended or disabled account writes `auth.login_blocked` and shows the generic message. No support contact is shown while none is defined. When one is defined, a secure way for suspended users to ask for help is added without revealing account status to unauthenticated visitors (G-22).
- **Registration [D-40, D-64]:** identical status, body and headers for new and existing addresses, with equivalent work. In production, without a provider, the page states that email cannot be sent yet. It never claims a message was sent.
- **Forgot password:** one page for every address. A message is sent only for an active account. In production it shows an explicit unavailable notice until a provider is configured and tested.
- **Reset flow [D-63 approved]:** `GET /password/reset/<token>` validates the token, keeps only the token's row id in the **signed session cookie** (signed, not encrypted, no secret inside), and redirects to `/password/reset`. The POST re-validates and consumes the token atomically.

### 5.4 Mail [D-54 approved]
- One `MailSender` interface, one adapter: a development file outbox under the git-ignored `instance/outbox/`.
- The adapter refuses to start under the production configuration.
- Production has no sender. It logs a startup warning that email delivery is not configured and disables flows that need email with an explicit notice.
- No message body or token is written to the console or application logs by any adapter.
- **Production email is not represented as configured until it is actually configured and tested** (RB-03).

### 5.5 Reset-token logging [D-46, D-63, D-69 approved; RB-07 strict]

**Evidence from the Foundation code:** requesting `/password/reset/SECRET-TOKEN-ABC123?x=SECRET-QUERY` put secrets in two log lines. Our request log printed the path. The Werkzeug dev-server access log printed the path and the query string. The Foundation test F-34 covers only the query string in our own log.

**Correction [D-63]:** the earlier statement that the emailed link appears once in access logs is withdrawn. **No token-bearing URL may be logged by the application, the WSGI server, the reverse proxy or the hosting platform.**

Application-level safeguards [D-69, application-level only]:
- R-LOG-1 Our request log shows the route pattern for token routes and `<redacted>` for any path under `/password/reset/` or `/verify-email/`, matched or not.
- R-LOG-2 A filter on the `werkzeug` logger removes the query string and redacts the same prefixes.
- R-LOG-3 Tokens never appear in logs, audit rows, error pages, JSON errors or mail-interface logs.
- R-LOG-4 Token pages send `Referrer-Policy: no-referrer` and `Cache-Control: no-store`, and load no external resources.

**Every layer is tested or verified. RB-07 stays open until all applicable layers pass:**

| Layer | How verified | When |
|---|---|---|
| Application request log | Automated tests I-38, I-39 | Implementation |
| Application exception log on token routes | Automated test I-76 | Implementation |
| Werkzeug development server access log | Automated test I-40, with a real local server in a thread | Implementation |
| Production WSGI server access log | Canary request, then a search of that log for the canary values | Deployment, after P-03 |
| Reverse proxy or load balancer log | Same canary procedure | Deployment |
| Hosting platform log collection, CDN or firewall logs | Same canary procedure | Deployment |
| Error-tracking or monitoring tools, if ever added | Same canary procedure | Before adding them |

Canary: request `/password/reset/CANARY-TOKEN?x=CANARY-QUERY` and search each log source. Neither value may be found.

### 5.6 Rate-limit storage failure behaviour [D-79 completion; D-83 and D-84 approved]

**Verification.** Under the production configuration, after the limiter is initialised, startup checks that the shared store answers. If it does not, startup fails with a clear message that never echoes the storage address. Production already refuses an unset or `memory://` value.

**If the store becomes unavailable while running: fail closed.**
- The limiter is configured explicitly with errors **not** swallowed and **no** in-memory fallback.
- Rate-limited routes (sign-in, registration, forgot-password, reset, verification, resend, password change) return the generic error page and do nothing: no sign-in, no password change, no token consumed.
- Health and static routes carry no limit and keep working.
- The log records the request id and the exception class only, never the storage address or any request content.
- Why not fail open: it would silently disable brute-force protection during an outage. Why not an in-memory fallback: limits would reset per worker, which is the unsafe configuration D-79 refuses.
- Cost: authentication is unavailable during an outage. The error is the existing generic 500 page, because showing a 503 would need a change to `app/errors.py`, which is outside the inventory.
- **[D-84 approved]** `/health/ready` reports `unavailable` when the store is unreachable, so an orchestrator can stop routing traffic to a node that fails closed. This needs `app/main/routes.py` added to the inventory.

**What cannot be verified now.** No shared store is chosen (P-02). This is tested with stub storage objects and the in-memory store only. It has not been tested against any real shared store, and RB-01 stays open.

## 6. Authorization matrix (Phase 1)

A suspended or disabled user is treated as signed out on every request.

| Route or action | Guest | Signed in, unverified | Signed in, verified | Notes |
|---|---|---|---|---|
| `GET, POST /register` | Allow | Redirect to `/account` | Redirect to `/account` | |
| `GET, POST /login` | Allow | Redirect to `/account` | Redirect to `/account` | |
| `POST /logout` | Redirect to `/login` | Allow | Allow | CSRF required |
| `GET, POST /password/forgot` | Allow | Redirect to `/account` | Redirect to `/account` | |
| `GET /password/reset/<token>`, `GET, POST /password/reset` | Allow with a valid token | Allow with a valid token | Allow with a valid token | Completing a reset ends all sessions |
| `GET, POST /verify-email/<token>` | Allow with a valid token | Allow with a valid token | Generic page (already verified) | The token proves control of the mailbox |
| `POST /verify-email/resend` | Redirect to `/login` | Allow | No-op redirect | Rate limited |
| `GET /account` | Redirect to `/login?next=/account` | Allow | Allow | Own data only |
| `GET, POST /account/password` | Redirect to `/login` | Allow | Allow | Needs the current password |

Service functions (no web page in Phase 1):

| Function | Who may call | Rules |
|---|---|---|
| change status | Holder of `users.suspend`, `users.reinstate` or `users.disable` | SG-1, SG-5, SG-6, SG-7. Reason required |
| assign or revoke role | Holder of `roles.assign` | SG-1 to SG-7. Allowed roles only (SG-2) |
| read audit log | None in Phase 1 | Viewer deferred [D-44] |

Future rows, recorded so later phases do not invent rules [D-49 approved]: vendor or rider application and placing an order are denied to unverified users.
Failures: anonymous on a protected route redirects to sign-in with a safe `next`. Signed in without the permission gets the 403 page. No route reveals whether another person's resource exists. Every route reads and writes only the signed-in user's own records.

## 7. Route contracts

State-changing routes are POST with CSRF. Successful posts redirect (POST, redirect, GET). Validation failures re-render with HTTP 422, keep entered values except passwords, and show field messages. Submit buttons disable after the first click, and the server is safe if two requests arrive.

| Route | Inputs and validation | Success | Failure and notes |
|---|---|---|---|
| `GET, POST /register` | `email` (required, valid, 254 max, trimmed, lowercased), `password`, `password_confirm` per 5.1 | Redirect to `GET /register/done`, a neutral page identical for new and existing addresses | 422 for invalid input only |
| `GET, POST /login` | `email`, `password`, optional `next` | Clear session, sign in, record the sign-in time, update `last_login_at`, redirect to `next` or `/account` | 422 with one generic message for every cause |
| `POST /logout` | none | End session, redirect to `/login` | Anonymous: redirect |
| `GET, POST /password/forgot` | `email` | Neutral page, identical for every address | Production without a provider: explicit unavailable notice |
| `GET /password/reset/<token>` | token in the path | Keep the token's row id in the session cookie, 302 to `/password/reset` | Any failure: one generic 400 page |
| `GET, POST /password/reset` | `password`, `password_confirm` per 5.1 | Update hash, consume token atomically, revoke other reset tokens, increment `session_version`, audit, redirect to `/login` | No session reference, or an inactive account: generic 400 |
| `GET /verify-email/<token>` | token in the path | Page with a confirm button, so mail scanners cannot consume the token | Generic 400 |
| `POST /verify-email/<token>` | CSRF | Consume token, set `email_verified_at`, revoke other verification tokens, audit, redirect | Generic 400 |
| `POST /verify-email/resend` | none | Revoke older, issue new, send through the mail interface, neutral notice | 429 page when limited |
| `GET /account` | none | Email, verified state with a resend button if unverified, role display names. No ids, no dates (G-04), no editable fields (G-01) | Anonymous: redirect |
| `GET, POST /account/password` | `current_password`, `new_password`, `confirm` per 5.1 | Update hash, keep this session valid, end others, revoke reset tokens, audit, notice mail | 422 |

Token pages send `Referrer-Policy: no-referrer` and `Cache-Control: no-store`. Contract file after approval: `docs/contracts/identity.md`.

## 8. Seed layer for Phase 1 [D-37, D-38, D-52, D-71 approved]

- Four fictional customers: `customer.verified@example.test`, `customer.unverified@example.test`, `customer.suspended@example.test`, `customer.disabled@example.test`, each with the `customer` role only. **No administrator is seeded.** Staff, vendor and rider personas wait for their features.
- The password comes from `DEV_SEED_PASSWORD` in the developer's git-ignored `.env`. There is no default. If it is missing or fails the password policy, `seed-dev` creates no users and says why, without echoing the value.
- A password is hashed only when a user is first created. A rerun skips existing users, never rewrites a hash, **never prints a password or hash**, and the command has no option to reset credentials.
- Suspended and disabled accounts are created through the status service with actor label `seed-dev`, so each has an audit row. A rerun adds nothing.
- The report lists emails, roles and "created" or "skipped (exists)".
- A read-only query and test confirm `.test` users are absent from a production database (RB-05).

## 9. Acceptance tests (none exist or have run)

All against PostgreSQL. Multi-step flows use Flask's test client under `tests/system/` [D-30].

**Migrations and schema**
- I-01 Each of `0002` to `0005` upgrades, downgrades (where permitted, see I-63 to I-66) and upgrades. No pending autogenerate differences.
- I-02 The database rejects mixed-case email, unknown `status`, unknown token `purpose`, and an audit row with no actor.
- I-03 Constraint names follow the convention.
- I-04 Atomic token consume: first succeeds, second returns nothing, concurrent attempts produce exactly one winner.
- I-05 As table owner, `UPDATE`, `DELETE` and `TRUNCATE` on `audit_logs` are rejected.
- I-06 With the maintenance role (membership granted): no retention policy means `DELETE` is refused; with a policy, a delete touching a row inside the retention period is refused as a whole and older rows are deleted; `UPDATE` and `TRUNCATE` are always refused. Skipped and reported **not tested** if the test database user cannot create roles.

**Registration and sign-in**
- I-07 Registration stores a hash, never plaintext, and writes an audit row.
- I-08 Responses for new and existing addresses are identical in status, body and headers.
- I-09 Invalid email, short password and mismatched confirmation return 422 and keep the email.
- I-10 Sign-in replaces the session. An external `next` is ignored.
- I-11 Wrong password, unknown email, suspended and disabled return identical responses.
- I-12 Correct password on a suspended or disabled account writes `auth.login_blocked` and shows the generic message. Wrong passwords write no audit row.
- I-13 Unknown-email response time is not distinguishable by a loose bound.
- I-14 Sign-in, registration, forgot-password and resend are rate limited and return the 429 page.
- I-15 Every POST route rejects a missing or wrong CSRF token.
- I-16 Logout requires POST and ends the session.

**Sessions, status and roles**
- I-17 A suspended or disabled user's existing session is rejected on the next request.
- I-18 Password change keeps the current session and ends others. Password reset ends all.
- I-19 The status service enforces allowed transitions, requires a reason, and writes one audit row with actor, previous and new status, reason and time.
- I-20 A user without the permission cannot change status or assign roles.
- I-21 Granting `vendor_owner`, `vendor_staff` or `rider` is refused and no row is written.
- I-22 A user can hold several roles. A duplicate grant is rejected.

**Tokens**
- I-23 Only the hash is stored. The raw token never appears in the database.
- I-24 Expired, used, revoked and tampered tokens all give the same generic 400.
- I-25 Verification resend revokes older verification tokens. A completed reset and a signed-in password change revoke that user's reset tokens. Disabling revokes all. **Forgot-password never revokes any token** [D-80 approved].
- I-26 Verification: GET shows a confirm page and does not consume. POST consumes. A second use fails. `email_verified_at` is set once.
- I-27 Forgot-password responses are identical for existing, unknown, suspended and disabled addresses, and no message is sent for the last three.

**Authorization**
- I-28 One parametrized test walks the whole matrix in section 6.
- I-29 Anonymous access to `/account` redirects with a safe `next`.
- I-30 With two users, every route and token touches only the signed-in or token owner's records.
- I-31 No response contains `password_hash`, token values or internal integer ids.
- I-32 An unverified user can do exactly the listed actions and nothing else.

**Audit**
- I-33 Each audited action writes exactly one row, and `before_data` and `after_data` never contain a hash, token or email.
- I-34 Successful sign-ins, sign-outs and failed attempts write no audit row but write an application log line without the password or email.

**Seed**
- I-35 `seed-dev` creates the four `.test` customers with hashed passwords and prints no password.
- I-36 Reruns change nothing, including password hashes and audit rows.
- I-37 Without a valid `DEV_SEED_PASSWORD` it creates no users and exits non-zero. A production configuration still refuses.

**Log masking (D-46, D-63, D-69)**
- I-38 Our request log never contains a token for matched routes.
- I-39 Our request log redacts any path under the sensitive prefixes, including unmatched ones (the case reproduced above).
- I-40 With a real local server in a thread, a request to `/password/reset/SECRET...?x=SECRET` leaves neither value in captured `werkzeug` and application log output.
- I-41 Audit rows, error pages and JSON errors never contain a token.
- I-42 Token pages send `Referrer-Policy: no-referrer`, `Cache-Control: no-store`, and load no external resource.

**Environment**
- I-43 All 89 Foundation tests still pass. `pip check` and `pip-audit` are clean.

**Safeguards and mail**
- I-44 A user cannot change their own status or roles (SG-1).
- I-45 Only `customer`, `support_agent`, `operations_manager` and `finance_operator` can be granted. `super_admin` and the three operational roles are refused with no row written (SG-2, SG-3).
- I-46 After every Phase 1 flow, `role_permissions` equals the manifest (SG-4).
- I-47 The last active `super_admin` cannot be suspended, disabled or have the role revoked (SG-5).
- I-48 Revoking a role removes the ability on the next call, even with a valid session (SG-7).
- I-49 Each audit action in the catalogue writes only its allowed fields.
- I-50 The development outbox writes files only under `instance/outbox/`, never prints bodies or tokens to console or logs, and refuses to start under the production configuration. Production startup logs that email delivery is not configured.
- I-51 In production, registration and forgot-password never claim a message was sent.
- I-52 Seed reruns leave every existing password hash unchanged and print nothing about passwords. The CLI has no credential-reset option.
- I-53 `DEV_SEED_PASSWORD` never appears in seed output, errors or logs.
- I-54 The session cookie in the reset flow holds only the token's row id. Replaying a copied cookie after the token was consumed cannot reset the password.
- I-55 The mail interface never logs a message body containing a token, under any adapter.
- I-56 The `.test` check finds the four seeded users in a seeded development database and none in a clean one.
- I-57 A session older than 24 hours is rejected, and activity does not extend it. No remember-me cookie exists.

**Added by revision 4, from your D-74 values and safeguards**
- I-58 Password length boundaries: 11 rejected, 12 accepted, 128 accepted, 129 rejected. No composition rule is applied.
- I-59 Password strength rule [only if D-78 is approved]: the 16 agreed samples (10 weak, 6 strong, listed in the Appendix A behaviour table) are classified at threshold 3 as in the review, with weak ones rejected and strong ones accepted. Only the first 72 characters are passed to the library (asserted on the call arguments). The check runs with all sockets blocked.
- I-60 Rate-limit values: the 6th sign-in per minute per IP and the 11th per hour per email return 429. The same for forgot-password (4th per hour per email, 6th per IP), registration (6th per hour per IP), resend (4th per hour per user) and submissions (11th per hour per IP). After the window the correct password works, so there is no lockout. Responses stay generic.
- I-61 Token protections: lookup by exact hash only; a token of one purpose cannot be consumed as the other; unknown tokens change no stored row; no unauthenticated request can revoke, consume or alter an existing token, including forgot-password for a victim's address; a suspended or disabled user's token gives the generic failure.
- I-62 (Foundation F-36, D-79) Production refuses `memory://` rate-limit storage at startup.
- I-63 Downgrading `0004` or `0005` under the production configuration is refused even with confirmation [D-77 approved].
- I-64 Outside production, downgrading `0004` is refused when `audit_logs` has rows unless `AUDIT_DOWNGRADE_CONFIRM=destroy-audit-data`, and allowed when empty or confirmed.
- I-65 Downgrading `0005` is refused in production and allowed elsewhere.
- I-66 After any refused downgrade, `alembic_version` and every table are unchanged.
- I-67 No row in `audit_retention_policy` means no `DELETE` succeeds for any role [D-76 approved].
- I-68 With a policy, only the maintenance role can delete, only rows older than the policy.
- I-69 Every maintenance deletion automatically writes an `audit.maintenance_run` row with the operator, count and newest deleted time.
- I-70 The application role cannot grant itself or switch to the maintenance role, switch session authorization, create or alter roles, alter or drop `audit_logs` or its triggers, create objects in the schema, or write the policy table. Skipped and reported **not tested** if roles cannot be created.
- I-71 The RB-08 evidence queries (owner, role flags, privileges, schema privilege, membership, trigger state) return the expected values in a two-role setup. Reported **not tested** if skipped.
- I-72 `instance/` is git-ignored, so the outbox files cannot be committed.
- I-73 A suspended account's sign-in failure is identical in status, body and headers (apart from the request id) to a wrong-password failure.
- I-74 Across every flow, no password, raw token or other authentication secret appears in captured application logs.
- I-75 The pinned `email-validator` (and any blocklist package) has been checked for release status and known vulnerabilities, `pip check` and `pip-audit` are clean.
- I-76 An exception raised on a token route logs no path segment, query or token.

**Added by revision 5**
- I-77 Only the purge recorder can create `audit.maintenance_run` rows. A direct insert by any other role is rejected, and a normal audit insert is accepted.
- I-78 The maintenance role holds no `INSERT`, `UPDATE` or `TRUNCATE` privilege on `audit_logs`, and the recorder pins its `search_path`.
- I-79 A maintenance deletion writes its `audit.maintenance_run` row automatically, with the operator's login name, even though the maintenance role cannot insert.
- I-80 Password-change limiter: attempts that reach the current-password check count, page views and form-validation failures do not. The 6th counted attempt in an hour for one user returns 429. A different user on the same IP is unaffected until the IP limit [D-82 approved]. Passwords and tokens never appear in logs. There is no permanent lockout.
- I-81 A refused downgrade leaves `alembic_version` and every table unchanged, for each of `0004` and `0005`, in each refusal case (D-77).

**Added by revision 6**
- I-82 Every privileged function has an empty fixed `search_path`, is owned by the table-owner role, has no `EXECUTE` for `PUBLIC`, the application role or the maintenance role, and contains no dynamic SQL (static scan of the catalog).
- I-83 The application role cannot call the privileged functions directly, and a temporary table with the same name created in its session does not change guard behaviour.
- I-84 The policy table rejects `UPDATE`, `DELETE` and `TRUNCATE` for every role, rejects non-positive days and empty approver or legal basis, and every inserted policy is recorded in `audit_logs` by the database [D-85 approved].
- I-85 `audit.maintenance_run` and `audit.retention_policy_approved` rows cannot be inserted directly by any role, including the table owner.
- I-86 Retention boundary: a row exactly at the threshold is refused, a row one second older is deleted, and a delete touching any row inside the period fails as a whole.
- I-87 A maintenance deletion record contains the count, oldest and newest deleted times, the policy id, the retention days and the operator's login name.
- I-88 Password hashing uses the entire original password: a 100-character password verifies against its full text and not against its 72-character prefix [if D-78 approved; the full-hash property is tested regardless].
- I-89 Role-dependent tests run only against the disposable cluster named in `ROLE_TEST_DATABASE_URL`, never the development database, and verify afterwards that every role they created is gone.
- I-90 Rate-limit storage failure: with a stub store that raises, every rate-limited route fails closed (generic error, no sign-in, no password change, no token consumed). The log has only the request id and exception class. Health and static routes still work.
- I-91 Production startup with a stub store whose check fails refuses to start with a message that does not echo the address.
- I-92 With the same stub failing, `/health/ready` reports `unavailable` [D-84 approved].
- I-93 The password-change counting rule: a form-validation failure leaves the budget unchanged, a wrong current password and a success each consume one attempt.

**Foundation regression tests for D-79 (Foundation numbering)**
- F-36 (replaces the old warning test) Production refuses `RATELIMIT_STORAGE_URI` that is unset, `memory://`, upper-case `MEMORY://`, or padded with spaces. The error names the variable and RB-01 and never echoes the configured value. Development and testing are unaffected.
- F-37 Production accepts a shared-storage URI at configuration level.
- F-38 `seed-dev` with an unreachable database exits non-zero. The message names only the exception class. The output contains no host, port, user, password or URL, and nothing is seeded.
- F-39 The same, with a seeder registered: the seeder never runs.
- F-40 The environment guard still runs first: under the production configuration `seed-dev` refuses without attempting any database connection.
- F-41 On a safe database the report prints, in order: environment classification, the database name only, the safety-check result, the registered seeders, and created and skipped counts per seeder where the seeder reports them (otherwise "counts not reported"). The existing sentence "No seeders are registered yet. Nothing was seeded." is kept for an empty registry.
- F-42 A refusal prints the environment classification and a failed safety-check result with the reason.
- F-43 An unreachable database prints the safety-check line with the reachability check failed, then the safe message.
- F-44 With a password in the database URL, no seed output contains the password, the host, the port or the URL, in any scenario (success, refusal, unreachable, seeder failure).
- F-45 A seeder returning counts is reported as "created N, skipped M". A seeder returning nothing is reported as "counts not reported".
- F-46 Under a production configuration the report never reveals a database name beyond what the refusal needs.
- All 89 existing Foundation tests still pass, apart from the fixture changes listed in section 12.1.

**Not testable in the application, tracked as release blockers:** RB-07 (production server, proxy and hosting logs), RB-08 (production database roles), RB-03 (real email), RB-09 (retention policy and legal basis). Browser behaviour is in `manual_checks.md`.

### 9.1 Role-dependent test environment [approved with restrictions]

You allowed `CREATEROLE` only for the dedicated test role, in an isolated, disposable test database, solely for the role-dependent tests, and never for the application role, a shared development role or any production role. `CREATEROLE` is a cluster-wide capability, so a separate cluster is the cleanest way to keep it away from the shared development role [PENDING confirmation].

Procedure (not yet executed; nothing has been granted):
1. Create a separate PostgreSQL 16 cluster on its own port, for example with `pg_createcluster`.
2. In that cluster only, create a dedicated role (for example `roletest_runner`) with `CREATEROLE` and `CREATEDB`, and a database whose name ends in `_test`.
3. Point `ROLE_TEST_DATABASE_URL` at it. It is a test-only variable, not read by the application, so it is not part of the `.env.example` comparison.
4. Run the role-dependent tests (I-06, I-70, I-71, I-82 to I-87 as they apply). They create their own temporary roles and remove them.
5. Record the environment (PostgreSQL version, port, role and database names, commands, results) in `docs/runbooks/role_tests.md`.
6. Destroy the cluster (`pg_dropcluster`) and confirm no extra roles or clusters remain.
If the cluster cannot be created, those tests are reported **not tested**.

## 10. Release blockers and gaps that stay open

- **Blockers:** RB-01 shared rate-limit storage (production will refuse `memory://` under D-79, but no shared store is chosen, installed or tested); RB-02 hosting and HTTPS; RB-03 email provider and "not represented as configured until tested"; RB-04 security review (agenda: D-65 sign-in auditing and repeated failures, no idle timeout, cookie-held session contents, D-68 safeguards); RB-05 no seed data in production; RB-06 dependency audit; **RB-07 strict**; **RB-08 strict**; RB-09 retention policy and legal basis.
- **Gaps:** G-01 profile fields; G-04 display timezone; G-22 support or recovery contact; G-23 licence of the word lists (D-78). G-11 is partly closed (file outbox only). `Design/` reference assets are still missing.

## 11. What this document does not decide

The email provider (P-01), hosting (P-03), the CI platform (P-19), admin user-management pages (P-28, deferred), the common-password solution (D-78, licence condition not met), and the document synchronisation you have asked me to hold.

## 12. Complete file inventory

### 12.1 Foundation files that will change [O-1: frozen until you confirm this plan]

| File | Change | Decision |
|---|---|---|
| `app/config.py` | Production refuses an unset or `memory://` `RATELIMIT_STORAGE_URI` with a clear error that never echoes the value. Sets the limiter explicitly: errors not swallowed, no in-memory fallback. Reads `DEV_SEED_PASSWORD` (development and testing only), `SESSION_MAX_AGE_SECONDS` (86400), `OUTBOX_DIR` | D-79, D-83, D-54, D-74 |
| `app/__init__.py` | Register the `auth` blueprint, initialise the mail adapter, add the production "email not configured" warning, remove the in-memory warning branch that D-79 makes unreachable, and verify the shared store is reachable at production startup | D-79, D-83, D-54 |
| `app/cli.py` | `seed-dev`: environment classification, database name only, safety-check result, registered seeders, created and skipped counts, a reachability check, a non-zero exit with a credential-free message when the database is unreachable | D-79 |
| `app/seeding/__init__.py` | A small result type (created, skipped) that a seeder may return, so counts can be reported. A seeder returning nothing is reported as "counts not reported". Registers the identity seeder | D-79, D-71 |
| `app/extensions.py` | Replace the placeholder user loader with the real one (active status, `session_version`, 24-hour maximum age) | D-41, D-74 |
| `app/security.py` | Path redaction for token routes and the `werkzeug` logger filter hook | D-46, D-69 |
| `app/models/__init__.py` | Import the identity models so Alembic sees them | Migrations |
| `app/main/routes.py` | **[D-84 approved; added to inventory]** `/health/ready` also reports `unavailable` when the rate-limit store is unreachable | D-83, D-84 |
| `app/templates/base.html` | Sign-in and sign-out navigation, script include | Identity UI |
| `app/static/css/base.css` | Small navigation styles only | Identity UI |
| `.env.example` | Document `DEV_SEED_PASSWORD`, `SESSION_MAX_AGE_SECONDS`, `OUTBOX_DIR`, and that production needs shared rate-limit storage | D-79, F-28 |
| `requirements.txt` | Add `email-validator` (pinned only after the release-status and vulnerability check, D-70). **`zxcvbn` is not added** unless D-78 is approved and its licence condition closed | D-70, D-78 |
| `tests/conftest.py` | New fixtures. Production fixtures use a shared-storage URI plus a test-only override to `memory://` so an app can be built without a shared store. Reads the test-only `ROLE_TEST_DATABASE_URL` | D-79, 9.1 |
| `tests/unit/test_config.py` | Production cases supply a shared-storage URI. Apps built for production use the test-only override. Refusal tests added | D-79 |
| `tests/unit/test_environment.py` | The `.env.example` comparison covers the new variables | F-28 |
| `tests/integration/test_health_errors.py` | F-36 replaced by the refusal tests. Production fixtures adjusted. Readiness test if D-84 is approved | D-79, D-84 |
| `tests/integration/test_seed.py` | New unreachable-database and fuller-report tests (F-38 to F-46) | D-79 |

Not changed: `wsgi.py`, `pytest.ini`, `.gitignore` (already ignores `.env` and `instance/`), `app/errors.py`, `app/models/base.py`, `app/seeding/guard.py`, `app/static/css/tokens.css`, `migrations/env.py`, `migrations/versions/0001_baseline.py`, and every document apart from the new Identity documents in 12.4.

**D-79 specifics, kept minimal and within the inventory.**
1. Production refuses `memory://`, verifies the store at startup, and fails closed at run time (section 5.6). No store client library is added, because the store is not chosen (P-02). Other storage types of the rate-limit library each need an extra package, which is why the production test fixtures use a test-only override and the failure behaviour is tested with stub stores.
2. `seed-dev` prints the report required by `seed_data.md` section 7 and exits non-zero for an unreachable database or a refusal. Sample output on success:
```
Environment: development
Database: marketplace_dev
Safety checks: environment OK; configuration OK; database name OK; database reachable OK
Registered seeders: identity
identity: created 4, skipped 0
```
Unreachable: the same header, with `database reachable FAILED`, then `Cannot reach the database (OperationalError). Nothing was seeded.` Never printed: passwords, tokens, host, port, user, URL or private paths.
No unrelated Foundation code is refactored.

### 12.2 New Identity files

| Area | Files |
|---|---|
| Models | `app/models/identity.py` (users, roles, permissions, links, tokens, audit logs, retention policy) |
| Blueprint | `app/auth/__init__.py`, `routes.py`, `forms.py`, `decorators.py`, `manifest.py` |
| Services | `app/services/auth.py`, `tokens.py`, `audit.py`, `roles.py`, `account_status.py`, `mail.py`, `passwords.py`, `sessions.py` |
| Support | `app/log_redaction.py`, `app/migration_guards.py` |
| Seeding | `app/seeding/identity.py` |
| Templates | `app/templates/auth/` (`login.html`, `register.html`, `register_done.html`, `forgot_password.html`, `reset_password.html`, `token_invalid.html`, `verify_email.html`, `account.html`, `change_password.html`), `app/templates/partials/_form_field.html` |
| Static | `app/static/css/forms.css`, `app/static/js/forms.js` (disables the submit button after the first click; not covered by automated tests) |
| Tests | `tests/system/` (`test_auth_flows.py`, `test_authorization_matrix.py`, `test_token_flows.py`), `tests/unit/` (`test_manifest.py`, `test_passwords.py`, `test_log_redaction.py`), `tests/integration/` (`test_identity_schema.py`, `test_status_service.py`, `test_audit_append_only.py`, `test_audit_functions.py`, `test_downgrade_guards.py`, `test_roles_privileges.py`, `test_rate_limit_failure.py`, `test_seed_identity.py`) |

### 12.3 Migrations

| Revision | File | Creates | Downgrade protection |
|---|---|---|---|
| `0002` | `migrations/versions/0002_users_roles.py` | users, roles, permissions, role_permissions, user_roles | Reachable only after `0004` and `0003` are downgraded, which blocks it in production |
| `0003` | `0003_auth_tokens.py` | auth_tokens | None needed |
| `0004` | `0004_audit_logs.py` | audit_logs | Refused in production even with confirmation. Elsewhere refused if rows exist unless `AUDIT_DOWNGRADE_CONFIRM=destroy-audit-data` |
| `0005` | `0005_audit_append_only.py` | append-only audit_retention_policy, guard and recorder functions with empty `search_path`, triggers | Refused in production |

`0001_baseline` is unchanged. All upgrades are additive.

### 12.4 Documents and deployment files

New at implementation: `docs/contracts/identity.md`, `docs/runbooks/audit_maintenance.md`, `docs/runbooks/log_redaction_check.md`, `docs/runbooks/database_roles.md`, `docs/runbooks/role_tests.md` (test environment record and cleanup), `docs/runbooks/database_roles.sql` (roles and grants, run by an administrator, never by the app), `docs/runbooks/rb08_checks.sql` (read-only evidence queries).
Updated only after you allow documentation synchronisation: `README.md`, `docs/conventions.md`, `docs/release_blockers.md`, `docs/documentation_gaps.md`, `docs/IMPLEMENTATION_PLAN.md`, `docs/manual_checks.md`, `docs/DECISIONS_NEEDED.md`.

### 12.5 Dependencies
`email-validator` (version chosen and pinned at implementation after checking release status, known vulnerabilities and `pip-audit`). `zxcvbn` **not added**, and only if D-78 is approved and the licence condition is closed. Nothing else.

## 13. Final implementation scope (for your confirmation)

**In:**
- Everything in section 1, plus the D-79 amendments including the shared-store verification, fail-closed behaviour and fuller `seed-dev` report.
- Migrations `0002` to `0005` with the guarded downgrades, the hardened audit functions and the append-only policy table.
- The 16 Foundation files in 12.1 (17 if D-84 is approved), the new Identity files in 12.2, and the documents in 12.4.
- The acceptance tests in section 9: **I-01 to I-93 and F-36 to F-46**. Nothing in them has been run.

**Out:** the items listed under "Out" in section 1; any admin page; production bootstrap commands; an email provider; any change to a file outside 12.1; synchronising other documents.

**Order of work, each step tested and reported before the next:**
1. D-79 amendments and their regression tests, adjusting the listed fixtures.
2. Migrations `0002` to `0005`, guards, and the schema and audit-function tests.
3. Services, in this order: tokens, audit, roles, status, mail, sessions, passwords. The password-strength rule is added last and **only if D-78 is resolved**. Otherwise the length rule and the "differs from the email" rule ship, and the report says the blocklist is missing.
4. Routes, templates and navigation.
5. Log redaction and its regression tests.
6. Seed layer.
7. Role-dependent tests on the disposable cluster, then its destruction and the record in `docs/runbooks/role_tests.md`.
8. Full test run, `pip check`, `pip-audit`, and the completion report: files changed, commands, results, and what was not tested.

## 14. Final outstanding risks and known limitations

| # | Risk or limitation | Status |
|---|---|---|
| 1 | **Word-list licence of `zxcvbn` (G-23).** Not fully verified. Blocks only the password-strength step | Needs your D-78 decision |
| 2 | **Shared rate-limit store not chosen (P-02).** Fail-closed behaviour and startup verification are tested with stubs only, never against a real store | RB-01 open |
| 3 | **Fail-closed means authentication stops during a store outage**, with a generic 500 page rather than a 503 | Accepted by design, approved under D-83 |
| 4 | **Production role separation** (RB-08) and **production log redaction** (RB-07) cannot be proven in development. I ship the scripts and checks, not the proof | Open, strict blockers |
| 5 | **Retention policy and legal basis not approved** (RB-09). Nothing can be deleted until they are | Open, pre-launch |
| 6 | **No email provider** (RB-03). No verification or reset email in production, and the pages say so | Open |
| 7 | **Privileged `SECURITY DEFINER` functions** are a sensitive surface. Mitigated by the empty `search_path`, no dynamic SQL, no execute rights, and the static tests | Needs the security review (RB-04) |
| 8 | **Operator identity in deletion records** depends on each operator having a named login, never a shared one | Runbook rule, cannot be enforced by the database |
| 9 | **No idle timeout; successful sign-ins and repeated failures not audited; session cookie signed but not encrypted** (it carries the session version, sign-in time and, during reset, a token row id) | Documented for RB-04 |
| 10 | **Rate limits keyed by email** let someone slow a victim's sign-in for up to an hour. No permanent lockout exists | Accepted, D-74 |
| 11 | **`zxcvbn` weaknesses if approved:** 30,000-entry password list, first 72 characters only, predictable local words can score as strong | Documented, Appendix A |
| 12 | **No browser here.** Layout, focus appearance and the submit-button script are unchecked. No JavaScript tooling exists (P-21) | Manual checklist |
| 13 | **Role-dependent tests** depend on the disposable cluster. If it cannot be created, I-06, I-70, I-71, I-82 to I-87 are reported not tested | Plan in 9.1 |
| 14 | **Foundation fixture changes** touch five test files. Risk of regressions is contained by running all 89 existing tests after each step | Process |
| 15 | **Windows PowerShell steps and other Python minor versions** are untested | Open |
| 16 | **A database superuser can bypass the audit protections.** Standard for PostgreSQL | Stated, not fixable |
| 17 | **Seeded accounts** exist only in development and test databases, and `.test` addresses must never reach production (RB-05) | Check provided |

Nothing in this list stops implementation from starting except item 1, which stops only one step.

## Appendix A. D-78 review of `zxcvbn` (complete)

**Method.** `zxcvbn` 4.5.0 was installed only in an isolated scratch environment outside the project. The project environment and `requirements.txt` do not contain it, and nothing was added. Python 3.12.3 on Linux, the project's version. Results are from 2026-10-10.

| Check | Result |
|---|---|
| Python version and platform | Pure-Python wheel (`py2.py3-none-any`, 409 KB), so no compiler is needed on Windows or Linux. Ran correctly on Python 3.12.3 here. The project README states testing on Python 3.8 to 3.13. **Not tested on Windows or other Python minor versions.** |
| Licence | MIT, with the licence file shipped (copyright 2016 Daniel Wolf). **I did not separately verify the licences of the embedded word lists**; the package declares MIT for the whole |
| Dependency tree | None. Installing it added no other package |
| Known vulnerabilities | PyPI lists none for 4.5.0. `pip-audit` reported "No known vulnerabilities found" |
| Maintenance status | **Low activity, not abandoned.** One release in 2025 (4.5.0, 2025-02-19) after a gap since 4.4.28 (2019-05-29). One maintainer. The repository shows 175 commits, 5 open issues, 5 open pull requests. The page I fetched did not show the latest commit date, so I cannot state recent commit activity. The README says it is the most up-to-date Python port and is recommended by the original Dropbox authors. Linux distributions package 4.5.0 (Arch rebuilt it 2025-12-14), and it is a test dependency of Flask-Security-Too according to the Arch package page |
| Network use | None. The library worked with every socket blocked |
| Data | Password list of 30,000 entries, plus 30,000 English Wikipedia words, 19,160 TV and film words, 10,000 surnames and about 4,700 first names. 30,000 is a small password list |
| Input limit | Rejects inputs over 72 characters with an error by default. The README strongly advises against raising the limit because of denial-of-service risk |

**Behaviour on sample passwords** (score 0 to 4; R1 = reject only if the whole password is a listed common password; R2 = reject if score is below 3):

| Password | R1 | R2 | Library warning |
|---|---|---|---|
| `password1234` | reject | reject | very common password |
| `Password123456` | accept | reject | similar to a common password |
| `P@ssw0rd12345` | accept | reject | similar to a common password |
| `qwertyuiop12` | accept | reject | similar to a common password |
| `123456789012` | accept | reject | similar to a common password |
| `iloveyou1234` | accept | reject | similar to a common password |
| `letmein123456` | accept | reject | similar to a common password |
| `aaaaaaaaaaaa` | accept | reject | repeats are easy to guess |
| `abcdefghijkl` | accept | reject | sequences are easy to guess |
| `marketplace123` | accept | reject | none |
| `nakawagroceries` | accept | accept | none |
| `kampala2024!!` | accept | accept | none (a predictable local word and year scores as strong) |
| `correcthorsebatterystaple` | accept | accept | none |
| `purple-giraffe-skates-quietly` | accept | accept | none |
| `Tr0ub4dor&3xyz9` | accept | accept | none |
| `k7#Vq2!zLp9@xW4m` | accept | accept | none |

User-specific input works: with the email local part supplied, a password built from it scored low and was matched as a user input.

**Performance.** Time grows steeply with length and varies with content:
- up to 72 characters: 12 to 151 ms (worst of 40 random 72-character passwords: 151 ms);
- 80 to 100 characters: 78 to 260 ms in the samples;
- 128 characters: 44 to 584 ms in some samples, and **about 2.2 seconds** for a pseudo-random 128-character password.
A 2-second CPU cost per submission is a denial-of-service risk. At 72 characters it is bounded at roughly 150 ms in these samples.

**Findings.**
1. It passes compatibility, dependency, licence and vulnerability checks as far as I tested.
2. Used as a **pure blocklist** (R1) it is weak: it rejected 1 of 10 weak samples, because most weak passwords are a common word plus digits, not a list entry.
3. Used with a **score threshold** (R2) it rejected all 10 weak samples and accepted all 6 strong ones. This goes beyond a "common-password blocklist", so it is a policy choice for you. It is not a composition rule, because it does not require character classes.
4. Its password list is small and old, so it will not catch every common password, and it cannot know local words.
5. Maintenance cadence is thin. It qualifies as maintained only marginally.

**Options and recommendation (needs your decision, D-78).**
- Approve `zxcvbn` with: evaluation limited to the first 72 characters (the library default, never raised); R2 with a threshold of 3 (my recommendation, because R1 failed to catch obvious cases), or R1 if you want a strict blocklist only; the email local part passed as user input; and a signed-in password-change limit (D-81), because every submission costs hashing and strength-check CPU. The library's warning text may be shown to users as guidance.
- Or choose another solution. `zxcvbn-rs-py` was **not reviewed**, because you asked for it only if `zxcvbn` failed compatibility or security review, and it did not fail either. It remains the next candidate if you reject `zxcvbn` for its maintenance cadence.
- Neither package is added until you approve the selection.

### A.8 Word-list licence verification (D-78 condition)

**Result: the condition "the embedded word-list licence is verified" is NOT met.** I am not a lawyer, and this is a provenance and licence check, not legal advice.

What the package itself says: `LICENSE.txt` and the metadata declare **MIT** for the whole package (copyright 2016 Daniel Wolf). Nothing inside the installed package states where the word lists come from or under what terms. I could not read the repository's own data directory, so provenance below comes from the upstream build script and README of the original project (Dropbox `zxcvbn`) and from search results.

| List | Entries | Upstream source | Licence evidence found | Status |
|---|---|---|---|---|
| `surnames`, `male_names`, `female_names` | 10,000 surnames, about 4,700 first names | US Census 2000 name tables from census.gov (named in the upstream build script) | The Census Bureau lists the surnames dataset as public, "intended for public access and use". US federal government works are generally not copyrighted in the US. That general rule is my background knowledge, and I found no explicit "public domain" sentence on the page | Largely verified |
| `passwords` | 30,000 | Credited upstream to Mark Burnett's password research | Burnett wrote in 2015 that his ten-million-credential dataset was released "to the public domain" (quoted by several outlets). **I found no licence statement for the specific list `zxcvbn` credits, and nothing explaining how the 30,000 were derived** | **Not verified** |
| `us_tv_and_film` | 19,160 | Wiktionary frequency lists compiled from TV and film subtitles | Wiktionary subtitle-derived lists by the same contributor are offered under "CC-BY-SA, GFDL or LGPL" (I could read the German and Spanish list notes, **not** the English list page). Creative Commons Attribution-ShareAlike requires attribution and share-alike for adaptations | Partly verified. Share-alike question open |
| `english_wikipedia` | 30,000 | Word counts computed from Wikipedia text | Wikipedia text is CC BY-SA. Whether a ranked word list built from counts is an adaptation is a legal question. I found no statement from the maintainers | **Not verified.** Share-alike question open |

**What this means.** Two lists derive from CC BY-SA sources and one list's licence is unconfirmed. Whether those obligations reach a project that only installs and runs the package, without redistributing the data, is a legal question I cannot settle. Widely used distributions package this library, which is evidence of common practice, not of legal clearance.

**Effect of removing the two share-alike-derived lists (tested in the scratch environment):** of 19 test passwords only two changed at threshold 3. `marketplace123` went from rejected (score 1) to **accepted (score 4)**, and `nakawagroceries` from 3 to 4. The other weak examples stayed rejected, but detection of "common word plus digits" patterns clearly degrades.

**Options (your decision under D-78):**
- **A. Accept `zxcvbn` and record the residual risk.** Add an attribution notice listing the sources above, and optionally get a lawyer to confirm. Best protection, unresolved legal doubt.
- **B. Use `zxcvbn` with those two lists disabled.** Not recommended: it weakens detection.
- **C. Reject it.** Review `zxcvbn-rs-py` (likely the same data lineage, so the same question) or build a blocklist from a source with clear terms, for example a list derived from Burnett's public-domain release plus the length rule. This is more work and needs your approval of the approach.

**My recommendation:** A only if you accept the residual risk. Otherwise C. Until you decide, nothing is added and the strength step ships as the length rule only.
