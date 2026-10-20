# Decision Register (v3.5)

Supersedes v3.4. Version 3.5 records the owner's decisions of 2026-10-11 (section 8, third round), the outcome of the word-list licence check, and the remaining pending items (section 9). Decisions D-47 to D-79 stand unless a third-round decision says otherwise. `docs/proposals/REGISTER_CHANGES_PROPOSED.md` is superseded by this file and is not edited. **Status clarification (2026-10-13):** This register's original implementation-gate wording predates the separate `docs/IDENTITY_REVISION_6_APPROVAL.md` record, which confirms that the owner approved Revision 6 on 2026-10-12 for implementation in small, testable batches. That approval record governs the Identity implementation gate. It does not declare production readiness and does not authorize Phase 2; Phase 2 remains blocked until Identity acceptance is verified and the owner explicitly approves the transition.

Source-of-truth order: owner decision, `Architecture_essential.md`, `Architecture.md`, `prd.md`, feature-specific documents including the prompt pack (`Agents.md` section 2 and the prompt-pack README agree).

## 1. Files reviewed and files still missing

| File | Status |
|---|---|
| `prd.md`, `Architecture.md`, `Architecture_essential.md`, `Agents.md`, `Claude.md` | Read in full |
| Docs-pack `README.md`, `Design/README` (uploaded as `README__1_.md`), `design_tokens.md`, `page_inventory.md`, `reference_register.md` | Read in full |
| Prompt pack: `README.md`, `backend_prompt.md`, `database_seed_prompt.md`, `frontend_prompt.md`, `integration_prompt.md`, `testing_security_prompt.md` | Read in full |
| `doc.md` (dashboards and operations specification) | **Received and read in full.** Reviewed in `docs/proposals/SPEC_REVIEW_DOC_PROMPT_SEED.md` |
| `prompt.md` version 2 (frontend implementation prompt) | **Received and read in full.** Same review |
| `seed_data.md` (PostgreSQL development seed specification) | **Received and read in full.** Same review |
| `Design/` reference screenshots, brand assets, component references | **MISSING** (`reference_register.md` lists every entry as "To be added") |

Only the `Design/` reference assets remain missing. The three files received describe themselves as proposed and subordinate to the approved documents. Their rank in the source-of-truth order is a pending question (see the proposed changes). Gap list: `docs/documentation_gaps.md`.

## 2. Approved by the owner

| ID | Decision |
|---|---|
| D-01 | Greenfield restart. No React or separate-API architecture without explicit approval. |
| D-02 | Flask, Jinja, HTML, CSS, JavaScript, PostgreSQL, SQLAlchemy, Flask-Migrate/Alembic. |
| D-03 | Email is the initial login identifier. Phone verification possible later without redesign. |
| D-04 | Flask-Login, Flask-WTF, Flask-Limiter, pytest, Werkzeug password hashing. |
| D-05 | Integer internal primary keys, public UUIDs where externally exposed. UUIDs never replace authorization. |
| D-06 | SQLAlchemy naming convention before the first migration. |
| D-07 | UGX launch currency. Decimal-safe money. No invented commission, delivery, provider-fee or refund values. |
| D-08 | Single `flask seed-dev`: refuses production, never at startup, fictional and deterministic, repeat-safe, hashed dev passwords, only existing models, tested. |
| D-09 | Vendor approval and zone/serviceability before real checkout. |
| D-10 | Order lifecycle before any payment provider. Development-only payment adapter until a provider is selected. |
| D-11 | Payments, commissions, refunds, payouts behind services. Financial policy not finalized without approval. |
| D-12 | Documented route, data and validation contracts per phase. |
| D-13 | Foundation scope fixed. |
| D-14 to D-21 | Foundation approvals: dependencies (Flask-SQLAlchemy, psycopg 3, python-dotenv, pip-audit; ruff not installed), Python 3.12 and PostgreSQL 16, empty baseline migration, folder deviations, prompts received, provisional design tokens, seed database-name guard, Foundation extras. |
| D-22 **NEW** | Foundation assumptions A-01 to A-05 and A-07 to A-13 accepted as provisional technical decisions, subject to security review and testing. |
| D-23 **NEW** | A-06: keep Werkzeug 3.1.9. Never downgrade to a vulnerable version to satisfy the maturity guideline. Reason documented in `requirements.txt` and below. |
| D-24 **NEW** | A-14: in-memory rate limiting is not production-ready. The warning stays visible. Production deployment is blocked until shared, persistent rate-limit storage is configured (`docs/release_blockers.md` RB-01). |
| D-25 **NEW** | P-12: no production bootstrap command yet. Behaviour and security implications documented first. Approval required before implementing. |
| D-26 **NEW** | P-13: no seed markers on every table. Propose the smallest maintainable solution. |
| D-27 **NEW** | P-14: no hardcoded development passwords. Strategy proposed. Owner approval before any seeded credential is exposed. |
| D-28 **NEW** | P-16: design statuses for active, suspended, disabled and unverified where applicable, recording reason, actor and timestamp through the audit mechanism. Present the model before implementing. |
| D-29 **NEW** | P-19: recommend a CI platform. No platform-specific configuration until approved. |
| D-30 **NEW** | P-20: Flask test client for system-level tests. No browser-testing dependency without approval. Manual visual checks documented. |
| D-31 **NEW** | P-21: recommend a lightweight JavaScript approach without a build system. No dependencies without approval. |
| D-32 **NEW** | P-23: only clearly labelled fictional development zones. Never presented as approved launch zones. |
| D-33 **NEW** | Missing documents are not invented or claimed as reviewed. They stay on the gap list. |
| D-34 **NEW** | Foundation stays separate from Identity, onboarding, catalogue, order, payment, delivery and finance phases. No production payment integration. No invented commission, delivery charge, refund, payout or other financial policy. Ask before expanding scope. |
| D-35 **NEW** | P-05: one user can hold multiple roles. Vendor and rider applications are separate, reviewable records. Approval is required before operational vendor or rider permissions are granted. |
| D-36 **NEW** | P-12: the bootstrap and administrator-creation proposal is approved as documentation only. No production bootstrap or administrator-creation command is to be implemented yet. |
| D-37 **NEW** | P-13: seeded users use reserved `.test` email addresses. Additional seed tracking is evaluated only when non-user entities are first seeded. |
| D-38 **NEW** | P-14: the development seed password comes from the git-ignored development `.env`, with no default. Credentials are never exposed in source code or logs. |
| D-39 **NEW** | P-16: account statuses are `active`, `suspended` and `disabled`. Email verification is tracked separately. Administrative status changes are recorded in the audit log. |
| D-40 **NEW** | P-24: appropriate protections against account and email enumeration. |
| D-41 **NEW** | P-25: consistent public-facing sign-in failure messages for suspended and disabled accounts, with secure internal audit detail retained. |
| D-42 **NEW** | P-26: unverified-user permissions are documented and enforced. Security-sensitive actions are audited. Append-only audit protection is proposed before implementation. |
| D-43 **NEW** | P-27: a shared token table is used, provided purpose, expiry, single use and revocation are enforced. Token hashes are stored, never raw tokens. |
| D-44 **NEW** | P-28: admin user-management pages are deferred until `doc.md` is supplied or a replacement is approved. (`doc.md` has now been supplied. Its coverage of this area is high level; see the review.) |
| D-45 **NEW** | P-29: a minimal authenticated `/account` page, limited to permitted profile information. |
| D-46 **NEW** | Identity security requirement: password-reset tokens appear in the URL path, so token-bearing URL segments are masked in logs, with a regression test. Identity stays a proposal until the missing documentation is addressed and the revised plan is approved. No unresolved business rule is invented. |
| D-47 to D-81 **NEW** | Identity decisions of 2026-10-10 and 2026-10-11. Exact approved values and conditions are in section 8. |

## 3. Foundation assumptions (status)

| ID | Assumption | Status |
|---|---|---|
| A-01 | Unset `APP_ENV` starts as production | Accepted, provisional |
| A-02 | Production rejects short or placeholder secrets and placeholder database credentials (a password starting `dev-only` counts) | Accepted, provisional |
| A-03 | Request bodies capped at 1 MiB by default | Accepted, provisional |
| A-04 | Strict Content-Security-Policy, Permissions-Policy denying camera, microphone and geolocation | Accepted, provisional |
| A-05 | HSTS in production, `max-age=31536000`, no `includeSubDomains`, no preload | Accepted, provisional |
| A-06 | Werkzeug 3.1.9 | **Kept.** See below |
| A-07 | `user_loader` returns no user until Identity | Accepted, provisional |
| A-08 | Errors return JSON when the client prefers JSON; `/health*` always JSON | Accepted, provisional |
| A-09 | Placeholder site name `Marketplace` | Accepted, provisional |
| A-10 | `DEV_SEED_PASSWORD` not read yet; no lint tool installed | Accepted, provisional |
| A-11 | `migrations/env.py` uses `db.engine` | Accepted, provisional |
| A-12 | Breakpoints `sm` 40rem, `md` 64rem | Accepted, provisional |
| A-13 | Inbound `X-Request-ID` kept only if it matches `^[A-Za-z0-9._-]{1,64}$` | Accepted, provisional |
| A-14 | In-memory rate limiting | **Not production-ready.** Release blocker RB-01 |

**A-06 detail.** `pip-audit` reported GHSA-g6x2-hccm-hh4m (CVE-2026-102598) against Werkzeug 3.1.8, fixed in 3.1.9. PyPI's advisory data describes it as `safe_join` accepting Windows device names when they carry an empty NTFS alternate-data-stream marker, a follow-up to earlier `safe_join` advisories. Werkzeug 3.1.9 was uploaded 2026-09-27 and PyPI lists no known vulnerabilities for it. After the upgrade `pip-audit -r requirements.txt` reported nothing. A separate web search corroborated the family of earlier `safe_join` Windows-device-name advisories (fixed in 3.1.4, 3.1.5 and 3.1.6), but did not return a page for this exact identifier, so the specific advisory rests on `pip-audit` and PyPI metadata. The project is developed on Windows, where this class of issue applies. The 14-day maturity guideline was mine, not a requirement, and a published security fix outweighs it. The audit is re-run at every release (RB-06).

## 4. Pending decisions

| ID | Decision | Status | Needed by |
|---|---|---|---|
| P-01 | Password-reset email provider | Open. Production reset stays disabled | Phase 1, production |
| P-02 | Production rate-limit storage | **Shared, persistent storage required (D-74). Release blocker RB-01.** The in-memory limiter is not production-ready | Before deployment |
| P-03 | Production WSGI server, hosting, HTTPS, proxy headers | Open. RB-02 | Hardening |
| P-04 | Session lifetime, password policy, token lifetimes, rate-limit values | **Decided (D-74).** See section 8 | Done |
| P-05 | One or many roles per user | **Decided (D-35):** many. Vendor and rider applications are separate reviewable records | Done |
| P-06 | UGX rounding mode and rounding points | Open | Phase 5 |
| P-07 | Order reference format | Open | Phase 5 |
| P-08 | Icon library or SVG set | Open | First UI with icons |
| P-09 | Brand, logo, typography, final tokens | Open | Before launch |
| P-10 | Display timezone | Open. Storage is UTC. `doc.md` and `prompt.md` both assume a documented display strategy, so this is needed before any page shows a time | Before first UI showing times |
| P-11 | PRD section 8 business questions (15), tax and legal, data retention and privacy | Open | Per phase |
| P-12 | Production bootstrap commands | **Proposal approved as documentation only (D-36).** Not to be implemented | Later |
| P-13 | Seed markers | **Decided for users (D-37):** `.test` emails. Non-user tracking evaluated when first needed | Phase 2 |
| P-14 | Development credential strategy | **Decided (D-38):** password from git-ignored `.env`, no default | Done |
| P-15 | Seed reset mode and dataset sizes | Open. Recommend not building | Later |
| P-16 | Account status model | **Decided (D-39):** active, suspended, disabled; verification separate; changes audited | Done |
| P-17 | Payment state vocabulary (PRD versus backend prompt) | Open | Phase 6 |
| P-18 | Private file storage for identity documents | Open | Phase 3 |
| P-19 | CI platform | **Recommendation documented.** Needs repository host | Before Phase 1 ends |
| P-20 | End-to-end tests | **Decided (D-30).** Test client first | Done |
| P-21 | JavaScript tooling | **Recommendation documented.** Needs a decision on a dev-only `package.json` | First JavaScript |
| P-22 | Regulated categories (pharmacy, health retail) | Open | Phase 4 |
| P-23 | Development zone fixtures | **Constraints decided (D-32)** | Phase 2 |
| P-24 | Registration and email enumeration protection | **Decided in principle (D-40).** Exact behaviour is in the Identity proposal | Phase 1 |
| P-25 | Sign-in messages for suspended and disabled accounts | **Decided (D-41):** consistent public messages, internal audit detail | Done |
| P-26 | Unverified-user permissions, audit scope, append-only audit protection | **Decided (D-49, D-65, D-66).** D-65 provisional; D-66 mechanism details pending D-76 | Phase 1 |
| P-27 | Shared `auth_tokens` table and verification flow | **Decided (D-48, D-63).** Token-level extras pending D-75 | Phase 1 |
| P-28 | Admin user-management pages | **Deferred (D-44).** `doc.md` supplied, but only lists the feature at a high level | Needs decision |
| P-29 | Minimal `/account` page | **Decided (D-45, D-73).** Fields G-01 and dates G-04 stay open | Phase 1 |

## 5. Contradictions and resolutions

| ID | Finding | Resolution |
|---|---|---|
| C-01 | Source-of-truth order, prompt pack versus `Agents.md` | No conflict |
| C-02 | Seed prompt allows a production override | D-08 is stricter and prevails: no override |
| C-03 | Seed prompt describes a reset mode | Not built (P-15) |
| C-04 | `DECISIONS_NEEDED.md` versus `decision_register.md` | This file |
| C-05 | Integration matrix versus contract documents | `docs/contracts/` with the matrix columns |
| C-06 | Deterministic seed versus salted hashes | Deterministic identities and passwords. Repeat runs skip existing users |
| C-07 | Seed layer 1 "approved categories and configuration" versus production needs | Bootstrap commands (P-12) |
| C-08 | Order and delivery state names differ between `Architecture.md` and PRD FR-DEL-007 | Open until Phase 5 |
| C-09 | Payment states differ | P-17 |
| C-10 | Empty seed skeleton exiting 0 | Resolved: states that nothing was seeded |
| C-11 | No browser in the sandbox | Layout and browser checks reported as not executed. See `manual_checks.md` |
| C-12 **NEW** | Password-reset tokens sit in the URL path, and Foundation request logs record the path | A real gap, found while writing the Identity proposal. The log path must mask that segment, with a test, in Phase 1 |

## 6. Reporting format

Phase reports follow `Agents.md` section 9 and separate: verified working, verified failing, not yet tested, blocked by missing provider, configuration or decisions. Nothing is reported as passed unless it was executed and the result checked.

## 7. Provisional owner direction on Identity (2026-10-10)

The owner's provisional direction of 2026-10-10, given before the decisions in section 8. The decisions in section 8 now supersede it where they are more specific. These conditions remain binding. **O-1 still applies: nothing is implemented until the owner gives explicit implementation approval.**

| ID | Condition |
|---|---|
| O-1 | Foundation stays unchanged until the revised Identity plan is finalized and you explicitly approve implementation. |
| O-2 | `vendor_owner`, `vendor_staff` and `rider` role assignment stays blocked until the corresponding approved onboarding records and authorization rules exist. |
| O-3 | Account suspension and role assignment are limited to explicitly authorized administrators. Permissions, audit records and self-escalation safeguards are defined and tested. |
| O-4 | Tokens are hashed, expiring and single use, with atomic consumption. Raw tokens and sensitive reset URLs are never logged. |
| O-5 | Production application, WSGI server, reverse proxy and hosting logs are separate security boundaries. RB-07 stays open until redaction is configured and verified. |
| O-6 | Mail is a development-only outbox. Nothing implies production email delivery is configured. |
| O-7 | Seeded accounts are fictional `.test` accounts with a password from a git-ignored `.env`. Existing credentials are never printed or reset on seed reruns. |
| O-8 | Audit logs are append-only during ordinary application operation, with a documented and controlled retention and maintenance process. |
| O-9 | The exact password policy, rate limits, token lifetimes and all remaining D-47 to D-54 and D-63 to D-74 entries are reviewed before they are finalized. Approval is never assumed for unspecified values. |

## 8. Approved Identity decisions and exact values (2026-10-10)

Each row is the owner's decision. "Exact value" is what was approved. Conditions are binding on the implementation.

| ID | Decision | Exact approved value | Conditions and notes |
|---|---|---|---|
| D-47 | Rank of `doc.md`, `prompt.md` v2, `seed_data.md` | **Approved.** Rank 5 with the prompt pack. `prompt.md` v2 supersedes `frontend_prompt.md`. `seed_data.md` supersedes `database_seed_prompt.md` where they differ. Old "avoid" and trust-cue guidance stays | |
| D-48 | Phase 1 scope | **Approved.** Email verification with resend and signed-in password change are in Phase 1 | |
| D-49 | Unverified-user permissions | **Approved.** Can sign in, view `/account`, resend verification (rate limited), change or reset password, sign out. Cannot submit a vendor or rider application or place an order (enforced when those features exist) | Closes G-02 for Phase 1 |
| D-50 | Sample label | **Approved.** `[DEV SAMPLE]` prefix on fictional vendors, zones, categories. Sample categories are never the launch list | Applies from the phase that seeds them |
| D-51 | Roles and permissions manifest | **Approved.** One code module, `app/auth/manifest.py`, read by `seed-dev`. Eight roles, four permissions (`roles.assign`, `users.suspend`, `users.reinstate`, `users.disable`). No bootstrap command | D-36 still applies |
| D-52 | Seeded non-active accounts | **Approved.** Created through the status service with actor label `seed-dev` | |
| D-53 | Status messaging | **Approved with condition.** Sign-in failure messages stay generic for every cause. No support contact is shown while none is defined | **Condition:** when a support or recovery contact is defined, provide a secure way for suspended users to seek assistance without revealing account status to unauthenticated visitors. Tracked as G-22 |
| D-54 | Mail | **Approved.** Development-only file outbox under git-ignored `instance/outbox/`. Adapter refuses to start in production. Production has no sender | **Conditions:** never log message bodies or tokens. Production email must not be represented as configured until it is actually configured and tested (RB-03) |
| D-63 | Token design | **Approved subject to correction.** Hashed (SHA-256), expiring, single-use tokens with atomic consumption, revocation rules and the token-less reset redirect as in revision 3 | **Correction:** the earlier statement that an emailed link "appears once in any access log" is withdrawn. **No token-bearing URL may be logged by the application, the WSGI server, the reverse proxy or the hosting platform.** Every relevant layer is tested (see the layer table in the Identity proposal). Approved separately: the session cookie is signed but not encrypted and holds only the token row id |
| D-64 | Registration | **Approved.** Identical response for new and existing emails | |
| D-65 | Audit scope | **Approved provisionally.** As proposed | **Condition:** revisit successful sign-in auditing and repeated failed sign-in attempts in the security review (RB-04). Never log passwords, raw tokens or other authentication secrets |
| D-66 | Append-only audit | **Approved with safeguards.** Database triggers in migration `0005` | **Safeguards:** (1) the ordinary application role cannot alter or delete audit records; (2) maintenance deletion is separately authorized, explicitly recorded and tested; (3) no record may be deleted until an approved retention policy exists. The mechanism that implements them is proposed as D-76 |
| D-67 | Operational roles | **Approved.** No Phase 1 override for `vendor_owner`, `vendor_staff`, `rider` | |
| D-68 | Privileged permissions | **Approved.** All seven safeguards SG-1 to SG-7 retained and tested, including protection of the last active `super_admin` and prevention of self-escalation | |
| D-69 | Log masking | **Approved as an application-level safeguard only** | **RB-07 remains open** until every applicable logging layer is configured and verified |
| D-70 | `email-validator` | **Approved.** | Pin a compatible version **only after** checking its release status and known vulnerabilities, at implementation. No version has been chosen or pinned |
| D-71 | Seeds | **Approved.** Four fictional customer accounts only | Do not seed an administrator. Never print existing credentials during reruns |
| D-72 | Migration chain | **Approved with safeguards.** `0002` users and roles, `0003` tokens, `0004` audit log, `0005` append-only | **Safeguards:** document migration dependencies and rollback risks; prevent audit-data-destroying downgrades in production; test the protections. Details proposed as D-77 |
| D-73 | `/account` | **Approved.** Email, verified state, role display names. No ids, dates or editable fields | |
| D-74 | Policy values | See the table below | |

### D-74 exact values

| Item | Approved value |
|---|---|
| Password length | **12 to 128 characters** |
| Composition rules | None |
| Common-password blocklist | **Include a maintained solution if it passes compatibility and security review.** Not yet selected (D-78) |
| Sign-in limit | **5 per minute per IP and 10 per hour per email.** Generic errors. No permanent account lockout |
| Forgot-password limit | 3 per hour per email, 5 per hour per IP |
| Registration limit | 5 per hour per IP |
| Verification resend limit | 3 per hour per user |
| Reset and verification submission limit | **10 per hour per IP, with suitable additional token-level protections** (proposed as D-75) |
| Reset-token lifetime | 1 hour |
| Verification-token lifetime | 24 hours |
| Session maximum age | **24 hours** |
| Idle timeout | **None in Phase 1.** The limitation is documented for the security review (RB-04) |
| Remember-me | Not included in Phase 1 |
| Rate-limit storage | **Shared storage for production deployments.** The in-memory limiter is not production-ready (RB-01) |

### D-75 to D-79 (decided 2026-10-10, second round; the third round below supersedes it where it differs)

| ID | Decision | Exact approved value | Conditions and status |
|---|---|---|---|
| D-75 | Token protections | **Approved in principle.** Exact-hash lookup, generic failures, token expiry, revocation and atomic single-use consumption | **Condition:** explain how `failed_attempts` can be incremented safely when an incorrect token hash matches no row. No unauthenticated request may revoke another user's valid token. If safe per-token counting is not possible, remove the five-failure revocation rule instead of creating a denial-of-service weakness. **Status:** explanation delivered (Identity proposal section 5.2). It cannot count unknown tokens. A narrow counter on requests that already hold a valid token would be safe but protects nothing, so the plan **removes** the five-failure rule and the `failed_attempts` column. Awaiting your confirmation of the corrected mechanism |
| D-76 | Audit maintenance | **Approved with strict privilege separation.** The `audit_maintenance` role, the empty `audit_retention_policy` table and automatic deletion records | **Conditions (exact):** the application database role must not grant itself maintenance privileges or switch to the maintenance role. A separately authorized operator is required. The approved retention threshold is enforced in the database. Deletion activity is recorded. With no approved retention policy, nothing may be deleted. **Status:** re-prototyped with real login roles; all refused as required (Identity proposal section 2.4). Four refinements (R) added by me need your confirmation with the final plan |
| D-77 | Downgrade protections | **Approved.** The downgrade protections and the rollback-risk table | Preserve the production prohibition on destructive audit-data downgrades. Test that a refused downgrade leaves the database unchanged |
| D-78 | Common-password solution | **Review `zxcvbn` first. The dependency is NOT approved.** | **Conditions (exact):** evaluate `zxcvbn` against the project's actual Python version and platforms; check maintenance status, licence, dependency tree, known vulnerabilities, password-strength behaviour and `pip-audit` results; compare with `zxcvbn-rs-py` if the first candidate fails compatibility or security review. Do not add either dependency until the review is documented and the owner approves the selection. **Status:** review documented in Appendix A of the Identity proposal. `zxcvbn` did not fail compatibility or security review, so `zxcvbn-rs-py` was not reviewed. Nothing was added to the project |
| D-79 | Two narrow Foundation amendments | **Approved.** (1) The production configuration refuses `memory://` rate-limit storage and fails clearly at startup instead of continuing with an unsafe configuration. (2) `seed-dev` returns a non-zero exit status when the database is unreachable and reports the failure clearly, without exposing credentials or secrets | **Conditions:** keep the changes minimal, add regression tests, and do not refactor unrelated Foundation code. The Foundation stays unchanged until the final plan is approved |

**Implementation authorization (owner, 2026-10-10):** Identity revision 4 is approved in principle, subject to resolving D-75 and completing the D-78 review. Implementation must not start until the owner has been shown: (1) the register and proposal updated with the exact D-75 to D-79 decisions; (2) the corrected D-75 mechanism and the completed D-78 review; (3) every Foundation file, Identity file and migration that will change; and (4) the final scope, acceptance tests and known limitations. The Foundation stays unchanged until the owner explicitly approves the corrected final plan. Other documents are not synchronised until then.

### Third round (decided 2026-10-11)

| ID | Decision | Exact value | Conditions and status |
|---|---|---|---|
| D-75 | Five-failure token rule | **APPROVED: remove it.** Remove `failed_attempts` and the five-failure revocation rule. Retain exact-hash lookup, purpose matching, expiry, atomic single-use consumption, generic failures and appropriate rate limits | Done in revision 6 |
| D-80 | Forgot-password token revocation | **APPROVED.** An unauthenticated forgot-password request must not revoke existing reset tokens. A successful password reset, a signed-in password change and a signed-in verification resend may revoke the relevant older tokens according to their purpose. Enforce rate limits and prevent token reuse | Done in revision 6 |
| D-76 refinements | Audit-maintenance refinements | **APPROVED WITH SAFEGUARDS.** The `SECURITY DEFINER` recorder, the forgery guard, the extended closure-evidence queries, and revocation of `CREATE` on the public schema | **Before implementation, document and test:** (1) a fixed, safe `search_path` for privileged database functions; (2) narrow execution privileges and protection against SQL injection; (3) separation between the application, table-owner and maintenance roles; (4) prevention of forged maintenance records and unauthorized retention-policy changes; (5) correct deletion thresholds, deletion evidence, and the rule that no records are deleted without an approved retention policy. **Status:** documented and prototyped (Identity proposal section 2.4). One bug found and fixed in the prototype. Additions beyond your list are in D-85 |
| D-78 | Password-strength dependency | **CONDITIONAL APPROVAL.** Approve `zxcvbn` if the embedded word-list licence is verified and the final dependency review remains satisfactory. Strength-score threshold of at least 3, subject to tests with weak and strong examples. Evaluate no more than the first 72 characters if required by the library's documented limit. Hash the entire original password, not a truncated version. Retain the length policy of 12 to 128 characters. Do not add the dependency until the licence and compatibility checks are complete | **Status: condition NOT met. Not approved. Nothing added.** Compatibility checks: complete, satisfactory. Licence check: complete, result **partly verified** (Identity proposal Appendix A.8). The owner must decide (section 9) |
| D-81 | Password-change limit | **APPROVED.** 5 password-change attempts per user per hour. Appropriate additional IP-based protection. The limiter must not unnecessarily lock users out. Never log passwords or tokens | The IP value is proposed as D-82 |
| Test permissions | `CREATEROLE` for role-dependent tests | **APPROVED WITH RESTRICTIONS.** Only the dedicated test role, in an isolated, disposable PostgreSQL test database, solely to run the role-dependent tests. Never to the application role, a shared development database role or any production role. Record the test environment and clean up afterwards | **Not granted yet.** Procedure in the Identity proposal section 9.1 (a separate disposable cluster) |
| D-79 completion | Foundation amendments | **APPROVED WITH COMPLETION REQUIREMENTS.** Keep production refusal of unset or `memory://` rate-limit storage. **Verify shared-store connectivity and define safe behaviour if the store becomes unavailable.** `seed-dev` returns a non-zero exit status for an unreachable database without exposing credentials. **Include the fuller seed report required by `seed_data.md` and test the behaviour** | Specified in Identity proposal sections 5.6 and 12.1. Proposed choices in D-83 and D-84 |
| Final scope | Implementation scope | **APPROVED IN PRINCIPLE** including the stated migrations, acceptance tests and listed Foundation amendments, subject to the conditions above | Before modifying code: finish the licence check (done), update the register and proposal (done), show the final outstanding risks and exact scope (done), keep all changes within the approved inventory, do not alter unrelated files, do not synchronise other documents. **Present the corrected final plan for final confirmation. Do not start implementation before that confirmation. The Foundation stays unchanged until then** |

## 9. Final pending items

Nothing below is approved. Implementation needs your final confirmation of revision 6.

### Needs your answer

| ID | Item | Proposed | Why |
|---|---|---|---|
| D-78 | **Licence decision for `zxcvbn`.** Option A: accept it, recording the residual licence risk and shipping an attribution notice, optionally after a lawyer's review. Option B: disable the two share-alike-derived word lists. Option C: reject it and review another solution | **A only if you accept the residual risk, otherwise C. Not B** | The licence condition is not met. Passwords list and Wikipedia counts are unverified, and two lists derive from Creative Commons share-alike sources. Option B weakens detection: `marketplace123` became acceptable |
| D-82 **NEW** | IP-based limit for signed-in password change | 20 per hour per IP, counting only attempts that reach the current-password check | You asked for appropriate IP protection. The value is mine, and higher than the per-user limit so shared addresses are not locked out |
| D-83 **NEW** | Behaviour if the shared rate-limit store becomes unavailable | **Fail closed.** Rate-limited routes (sign-in, registration, forgot-password, reset, verification, password change) return the generic error and do nothing. No in-memory fallback, no swallowing of errors. Health and static routes keep working. Production verifies the store is reachable at startup and refuses to start if not | Fail-open would disable brute-force protection during an outage. Cost: authentication is unavailable during an outage |
| D-84 **NEW** | Add `app/main/routes.py` to the inventory so `/health/ready` reports an unreachable rate-limit store | Add | Without it a node that fails closed still reports ready. This file was not in the approved inventory |
| D-85 **NEW** | Hardening added beyond your D-76 list: the empty `search_path` (not just a pinned one); the retention-policy table is itself append-only; every policy approval is recorded in the audit log by the database; the maintenance record also carries policy id, retention days, oldest and newest deleted times; the forgery guard covers both recorder-only actions; `REVOKE ALL` on the privileged functions from `PUBLIC` | Adopt | Meets safeguards (2), (4) and (5). The prototype exposed a bug (see Identity proposal 2.4) that is fixed in the design |
| Test cluster | Run the role-dependent tests on a separate, disposable PostgreSQL cluster with its own dedicated role that has `CREATEROLE`, then destroy the cluster | Adopt | `CREATEROLE` is a cluster-wide capability, so a separate cluster keeps it away from the shared development role |
| Final confirmation | Approve the corrected final plan, Identity proposal revision 6 | | O-1 |

### Open gaps

| ID | Gap | Status |
|---|---|---|
| G-01 | Permitted customer profile fields | Open. No editable fields in Phase 1 |
| G-04 | Display timezone | Open. No dates shown in Phase 1 |
| G-11 | Meaning of "outbox" | Partly closed by D-54 |
| G-20 | Who may suspend and assign roles | Approved: `super_admin` only |
| G-21 | IP addresses in audit rows | Approved: only for audited events. No audit deletion until retention period and legal basis are approved. Pre-launch requirement (RB-09) |
| G-22 | Support or recovery contact and a secure path for suspended users | Open |
| G-23 **NEW** | Licence of `zxcvbn`'s embedded word lists | Open (D-78) |

Other open items: P-01 email provider; P-02 shared rate-limit store (not chosen); P-03 hosting and production server; P-19 CI platform; P-28 admin user-management pages (deferred); the business questions in PRD section 8; `Design/` reference assets still missing.

## 10. Release blockers

| ID | Blocker | Status |
|---|---|---|
| RB-01 | Shared, persistent rate-limit storage (A-14). Under D-79 production will refuse `memory://` and will verify the store at startup, but no shared store is chosen, installed or tested against a real store | Open. Reaffirmed by D-74 and D-79 |
| RB-02 | Hosting, HTTPS and proxy configuration | Open |
| RB-03 | Email provider. Production email must not be represented as configured until configured and tested | Open |
| RB-04 | Security review of provisional assumptions A-01 to A-05 and A-07 to A-13. **Agenda added:** successful sign-in auditing and repeated failed attempts (D-65); no idle timeout (D-74); cookie-held session contents; D-68 safeguards | Open |
| RB-05 | No development seed data or `.test` accounts in production | Open |
| RB-06 | Dependency audit clean at release | Open |
| RB-07 | **Strict.** Token-bearing URLs must not appear in application, WSGI server, reverse proxy or hosting logs. Closed only when redaction is verified for each applicable log source with a canary request (`/password/reset/CANARY-TOKEN?x=CANARY-QUERY`) and a search of that source finding neither value | **Open. Approved as strict** |
| RB-08 | **Strict.** The application database role must not own the audit table or be able to disable its triggers. Migration and table ownership, application access, and controlled maintenance privileges are separate roles. Closure evidence: the read-only queries in the Identity proposal section 2.4, run against the production database | **Open. Approved as strict** |
| RB-09 **NEW** | Approved audit-data retention period and legal basis (G-21) | Open. Pre-launch requirement |

`release_blockers.md` and `documentation_gaps.md` still hold earlier wording. They will be synchronised with this section when you approve editing them.

## Final confirmation — Identity Phase Revision 6 (2026-10-12)

The owner confirmed the following decisions for the Identity Phase Revision 6 plan on 2026-10-12. This entry resolves the previously pending items below; historical entries are retained for traceability.

| ID | Final decision | Implementation constraint |
|---|---|---|
| D-78 | **REJECT `zxcvbn` for Phase 1.** The embedded word-list licence condition was not met. | Do not add `zxcvbn` or a substitute strength library in this phase. Enforce the approved 12–128 character password-length policy and the documented email-difference rule. |
| D-82 | **APPROVED:** 20 signed-in password-change attempts per hour per IP, alongside D-81's 5 per user per hour. | Count only attempts that reach the current-password check. No permanent account lockout; never log passwords or tokens. |
| D-83 | **APPROVED: fail closed** when shared rate-limit storage is unavailable. | No swallowed storage errors and no in-memory fallback. Authentication actions do not proceed during a store outage. Production startup checks connectivity; health/static endpoints remain available. |
| D-84 | **APPROVED:** include rate-limit-store status in `GET /health/ready`. | Return generic `unavailable`/503 when the store cannot be reached; expose no connection details or secrets. Keep `/health` as liveness. |
| D-85 | **APPROVED:** all proposed audit-retention safeguards. | Empty fixed `search_path` for privileged functions; least-privilege execution; append-only retention-policy table; database-recorded policy approvals; deletion evidence including policy and time bounds; forgery protection; revoke privileged function execution from `PUBLIC`. |
| Test cluster | **APPROVED WITH RESTRICTIONS:** use a separate disposable PostgreSQL cluster and dedicated test role with `CREATEROLE` only for role-dependent tests. | Never grant this capability to the application, shared development, or production roles. Document and destroy the cluster after testing. |
| O-1 | **APPROVED:** Identity Phase Revision 6 is the implementation plan. | Preserve Foundation architecture, work in small batches, verify each batch, document tests that cannot run, and do not start Phase 2 without the owner's explicit approval after Identity acceptance. |

These approvals do not close production release blockers such as selection and real deployment verification of shared rate-limit storage, access-log canary checks, application/database role separation, email-provider setup, or the approved audit-retention legal basis.
