# Proposed changes to the decision register (for approval)

**Nothing below is recorded as approved.** Decision Register v3.1 (`docs/DECISIONS_NEEDED.md`) holds only your decisions. Reply with the numbers you approve, change or reject. Details and evidence: `SPEC_REVIEW_DOC_PROMPT_SEED.md`.

## A. Needed before the Identity plan can be approved

| ID | Proposed decision | Source finding |
|---|---|---|
| D-47 | `doc.md`, `prompt.md` v2 and `seed_data.md` rank with the prompt pack, below the PRD. `prompt.md` v2 supersedes `frontend_prompt.md` and `seed_data.md` supersedes `database_seed_prompt.md` where they differ. The "avoid" and trust-cue guidance in `frontend_prompt.md` stays in force. | C-13, C-27 |
| D-48 | Phase 1 (Identity) includes email verification, resend, and signed-in password change, in addition to registration, sign-in, sign-out, reset, roles and audit. `/account` stays minimal (D-45). Profile editing waits for G-01. | C-15 |
| D-49 | Unverified-user permissions (the list for D-42, proposed below). | G-02 |
| D-50 | Seed labelling uses `[DEV SAMPLE]` for visible fictional vendors, zones and categories. Sample categories are never the launch list. | C-19, C-22 |
| D-51 | One roles and permissions manifest module in code, read by `seed-dev`. The bootstrap command stays unimplemented (D-36). | C-21 |
| D-52 | Seeded suspended and disabled accounts are created through the status service with a system actor label such as `seed-dev`, so each has an audit row. | C-23 |
| D-53 | "Clear account-status messaging" means: unverified users see a clear banner after sign-in. Suspended and disabled users get the generic sign-in message (D-41) and are directed to support separately. | C-24 |
| D-54 | Phase 1 email goes through a mail-sending interface with a development file outbox only. A database outbox is designed in the notifications phase. | C-25 |

### Proposed unverified-user permissions (D-49)

These are proposals. I have not found them in any document (G-02).

| Action | Unverified | Verified |
|---|---|---|
| Sign in, view `/account`, sign out | Yes | Yes |
| Request a new verification email (rate limited) | Yes | Not needed |
| Change password, reset password | Yes | Yes |
| Submit a vendor or rider application (Phase 3) | No | Yes |
| Place an order (Phase 5) | No | Yes |

The last two rows describe future features. They are recorded now so those phases do not invent a rule, and they are enforced when those features exist.

## B. Can wait until the phase that needs them

| ID | Proposed decision | Source finding | Needed by |
|---|---|---|---|
| D-55 | Rider applications join vendor applications in Phase 3. Phase 7 keeps availability, dispatch and delivery. | C-14 | Before Phase 3 |
| D-56 | Application status vocabulary starts from PRD FR-VEND-003. You decide on "needs changes" versus "more information required", and on draft and suspended for riders. | C-16 | Phase 3 |
| D-57 | Role and permission definitions stay in code. An admin screen assigns roles to users, audited. | C-17 | First admin screen |
| D-58 | Template layout follows `Architecture.md` plus the existing `partials/`, adding `public/`. Internal dashboard structure is decided when the first one is built. | C-18 | First internal dashboard |
| D-59 | The development payment adapter is its own step after the order lifecycle. | C-26 | Phase 5 |

## C. Housekeeping, documentation only

| ID | Proposed change |
|---|---|
| D-60 | Add a root `Design/` folder with the four design documents. Add `docs/specs/` with `doc.md`, `prompt.md` and `seed_data.md`, unchanged. |
| D-61 | Add the missing check widths (390 to 430 and 1440 px) to `docs/manual_checks.md`. |
| D-62 | Replace `DEV FIXTURE:` with `[DEV SAMPLE]` in `TOOLING_RECOMMENDATIONS.md` once D-50 is approved. |

## D. Proposed Foundation amendment (needs approval, because Foundation is approved)

Scope: `seed-dev` only (C-20).
- Before reporting, check that the database is reachable. If not, print a safe message and exit non-zero.
- Print: environment classification, database name (never the URL or credentials), safety-check result, registered seeders, and created and skipped counts where reliable.
- Update the F-25 test and add tests for the unreachable-database case and for the report contents (no credentials in output).
- No other Foundation file changes.

## E. Roadmap

The proposed phase table is in section 6 of the review. It changes only phases 1, 3, 5, 6 and 7, and only if D-48, D-55 and D-59 are approved. The roadmap in `IMPLEMENTATION_PLAN.md` is unchanged until then.

## F. Added by the revised Identity package (all PENDING)

| ID | Proposed decision |
|---|---|
| D-63 | Token design: `revoked_at` column, one atomic single-use statement, the revocation rules in the Identity proposal, and the redirect-to-token-less-URL reset flow. |
| D-64 | Neutral registration response, identical for new and existing addresses, with sign-in as the confirmation. |
| D-65 | Audit scope. Audited: registration, email verification, password change and reset, status changes, role grants and revocations, sign-in with correct credentials on a blocked account. Application log only: successful sign-in, sign-out, failed attempts. |
| D-66 | Append-only `audit_logs` through database triggers in a separate revision, with the documented limits. |
| D-67 | In Phase 1 the role-grant service refuses `vendor_owner`, `vendor_staff` and `rider` unconditionally. |
| D-68 | The four Phase 1 permission codes are held by `super_admin` only. Wider assignment is a business decision (G-20). |
| D-69 | Log masking scope: our request log, a filter on the `werkzeug` logger, and release blocker RB-07 for production servers. |
| D-70 | Add `email-validator` (needed by Flask-WTF's email check), pinned and audited. Alternative: a deliberately simple custom check. |
| D-71 | Phase 1 seeds the four customer personas only. Staff, vendor and rider personas wait for their features. |
| D-72 | Migration chain split: `0002` users and roles, `0003` tokens, `0004` audit, `0005` append-only. |
| D-73 | `/account` shows email, verification state and role display names only. No dates until G-04, no editable fields until G-01. |
| D-74 | Approve or replace the proposal values in the Identity proposal section 4 (password length, rate limits, token lifetimes). |

## G. What happens next

The revised Identity package now exists in `IDENTITY_PHASE_PROPOSAL.md` (revision 2): migration design, authorization matrix, route contracts and acceptance tests. Identity stays a proposal. No code will be written until you approve the revised plan, meaning your answers on D-47 to D-54 and D-63 to D-74 (approve, change or reject each).
