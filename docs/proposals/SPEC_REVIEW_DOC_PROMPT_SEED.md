# Review of `doc.md`, `prompt.md` (version 2) and `seed_data.md`

Date: 2026-10-10. Nothing in this review has been applied. The Foundation implementation was not modified.

## 1. What was reviewed

Read in full: `doc.md` (215 lines), `prompt.md` (157 lines), `seed_data.md` (149 lines).
Compared against: `prd.md`, `Architecture.md`, `Architecture_essential.md`, `Agents.md`, `Claude.md`, the Design documents, the six prompt-pack files (re-read `frontend_prompt.md` and `database_seed_prompt.md` line by line for the comparison), the implementation plan, Decision Register v3.1, the Identity proposal, and the actual Foundation code.

Two read-only experiments on the Foundation code, run for this review:
- `seed-dev` with an unreachable development database, with no seeders registered: it printed "No seeders are registered yet. Nothing was seeded." and exited 0.
- Search of `app/templates` for `|safe` and `autofocus`: none found.

All three files describe themselves as proposed and subordinate to the approved PRD, architecture, phase plan and decision register. None of them authorizes an unresolved business or financial rule.

## 2. What already agrees (no action)

- Roles: `doc.md` section 3 lists the same nine categories as the PRD, and my proposed role codes match.
- Stack and rules: Python 3.12, PostgreSQL 16, no SPA and no build system (D-02, D-15).
- One person with several roles, and separate reviewable vendor and rider applications that grant nothing until approved (D-35).
- Reset and verification tokens expire, are single use, are stored as hashes, and token-bearing URL segments are masked in logs (D-43, D-46).
- A development outbox is not production email (the Identity proposal says the same).
- Production bootstrap and first-admin creation stay separately gated (D-25, D-36).
- No rider location tracking, camera or background geolocation without approval matches the Foundation Permissions-Policy (A-04).
- Provisional design tokens remain the source of truth, and "warm" is a feel and not permission to change them (matches D-19). This resolves the tension I noted earlier between the frontend prompt and the blue tokens.
- `seed_data.md` forbids any override of the safety checks, any reset mode and any `seed_key` column on every table. That matches D-08, D-20, C-02, C-03 and D-37.
- `seed_data.md` section 3 (password from git-ignored `.env`, no default, hash only on creation) matches D-38 and C-06.
- Reporting format with verified, failing, untested and blocked items: already adopted.

## 3. Conflicts and decisions that need your approval

Each row says what disagrees and what I recommend. Nothing is applied.

| ID | Finding | Recommendation |
|---|---|---|
| C-13 | **Rank and supersession.** The three files do not say where they sit in the source-of-truth order. `prompt.md` version 2 and `frontend_prompt.md` overlap heavily. `seed_data.md` and `database_seed_prompt.md` overlap and differ on reset mode, overrides and markers. | Rank all three with the prompt pack (below the PRD). Treat `prompt.md` v2 as superseding `frontend_prompt.md`, and `seed_data.md` as superseding `database_seed_prompt.md` where they differ. See C-27 for what v2 drops. |
| C-14 | **Rider applications.** PRD section 12 puts rider onboarding in increment 5, with zones and dispatch, and my roadmap followed that (Phase 7). `doc.md` section 15 puts "vendor/rider applications and review" at step 4, before catalogue and orders. | Adopt `doc.md`: Phase 3 covers vendor and rider applications. Phase 7 keeps availability, dispatch and delivery. Consequence: rider document rules (PRD question 8, G-07) and private document storage (P-18) are needed earlier. |
| C-15 | **Identity scope.** `doc.md` sections 4 and 15 and `prompt.md` section 5 put email verification with a resend flow, and password change, in the Identity step. PRD FR-AUTH-006 rates verification P1. My proposal left verification and change-password out unless you asked. You approved a minimal `/account` page. | Include email verification, resend and signed-in password change in Phase 1, since the token table already supports them. Keep `/account` minimal. Profile editing waits until the permitted fields are defined (G-01). |
| C-16 | **Application statuses.** PRD FR-VEND-003 lists: draft, submitted, under review, more information required, approved, rejected, suspended. `doc.md` section 5 lists: submitted, under review, needs changes, approved, rejected. | Use the PRD list as the base. You decide whether "needs changes" and "more information required" are the same state, and whether draft and suspended apply to riders. Can wait until Phase 3. |
| C-17 | **Role administration.** `doc.md` section 10 and `page_inventory.md` list "role/permission administration" as an admin screen. My documented bootstrap design defines roles and permissions in a code manifest. | Keep definitions in code, and let an admin screen assign roles to users, with every assignment audited. It limits the damage of a mistaken or hijacked admin session. Can wait until the first admin screen. |
| C-18 | **Dashboard and template layout.** Three layouts disagree. `Architecture.md`: `public/ auth/ customer/ vendor/ rider/ admin/ errors/`. `prompt.md` section 11: `components/ main/ auth/ customer/ vendor/ rider/ support/ operations/ finance/ admin/`. Foundation: `partials/` and `errors/`. `doc.md` describes four internal dashboards while `Architecture.md` and `page_inventory.md` have one admin area. | `Architecture.md` outranks `prompt.md`, and `prompt.md` itself says to follow the repository's real structure first. Keep `partials/`, add `public/` for public pages, and decide support, operations and finance structure when the first internal dashboard is built (G-12). |
| C-19 | **Sample label.** `seed_data.md` requires `[DEV SAMPLE]` on visible fictional vendors and zones. My tooling document proposed `DEV FIXTURE:`. D-32 only says "clearly labelled". | Use `[DEV SAMPLE]`, and update my wording when approved. |
| C-20 | **Seed command behaviour (Foundation gap).** `seed_data.md` section 7 requires: print environment classification, database name (never the URL), safety-check result and registered seeders; and exit non-zero when the database is unavailable. Foundation prints one line, and exits 0 even when the database cannot be reached (verified above). | A small Foundation amendment: a connectivity check, the report lines, and updated tests. Not applied, because you asked me not to modify Foundation. It needs your approval. |
| C-21 | **Roles in two places.** `seed_data.md` layer 1 seeds roles and permissions in development. Production roles come from the bootstrap design, which you approved as documentation only. Two separate lists would drift apart. | One roles and permissions manifest module in code, read by `seed-dev` now and by the bootstrap command if it is ever approved. This stays within D-36, because the command itself is not built. |
| C-22 | **Development categories.** Layer 1 includes "development categories", but the category list is unapproved (G-08). `[DEV SAMPLE]` is required only for vendors and zones. | Label sample categories `[DEV SAMPLE]` as well, and never treat them as the launch list. |
| C-23 | **Seeded suspended and disabled accounts.** Layer 2 asks for them. Status changes must be audited (D-39). Creating the rows directly would skip the audit record. | Create them through the status service with a system actor label such as `seed-dev`. |
| C-24 | **"Clear account-status messaging."** `doc.md` section 4 lists it. D-41 requires consistent public sign-in failure messages for suspended and disabled accounts. | Reading it as: unverified users see a clear banner after sign-in, while suspended and disabled users get the generic sign-in message and are pointed to support separately. Please confirm that reading. |
| C-25 | **"Outbox."** `doc.md` sections 8 and 11 say "service/outbox abstraction" and "notification/outbox status". That could mean a database outbox table with a delivery worker. No task queue or worker has been approved. | Phase 1: a mail-sending interface with a development file outbox only. A database outbox is designed in the notifications phase (G-11). |
| C-26 | **Payment adapter step.** `doc.md` step 7 is a separate "development payment adapter" after the order lifecycle. My roadmap put it inside the orders phase. D-10 is satisfied either way. | Follow `doc.md`: orders first, then payment service boundary with the development adapter. Low priority. |
| C-27 | **What version 2 drops.** `frontend_prompt.md` has an "avoid" list (overcrowded dashboards, huge hero sections, tiny low-contrast text, fake review counts and delivery estimates) and a trust-cue list. `prompt.md` v2 does not repeat them. | Keep them in force. They do not conflict with v2. |
| C-28 | **Where the documents live.** `Architecture.md` shows a root `Design/` folder, and `prompt.md` section 1 tells agents to read `Design/README.md` and others. The zip I produced has no `Design/`. | Add `Design/` with the four design documents, and put the three new files under `docs/specs/`. Documentation only. |

## 4. Duplicate requirements

These appear in more than one document. I recommend each keeps one authoritative source, with the others pointing to it, so they cannot drift.

| Requirement | Where it appears | Authoritative source |
|---|---|---|
| CSRF on state-changing forms | `Architecture_essential.md`, PRD FR-AUTH-005, `doc.md` sections 2 and 14, `prompt.md` section 7 | `Architecture_essential.md` |
| No inline CSS or JavaScript | `Architecture.md`, `frontend_prompt.md`, `doc.md`, `prompt.md` | `Architecture.md` and the Foundation tests (F-33) |
| No fake data, metrics or ratings | `frontend_prompt.md`, `integration_prompt.md`, `doc.md`, `prompt.md` | `doc.md` section 2 |
| Server-side authorization and ownership checks | PRD, `Architecture_essential.md`, `doc.md` section 3, `prompt.md` | `Architecture_essential.md`, plus the authorization matrix |
| Reduced motion, visible focus, no colour-only status | `design_tokens.md`, both frontend prompts, `doc.md` section 13 | `doc.md` section 13 and the Foundation tests (F-32) |
| Token hashing and masked token URLs | `doc.md` section 11, D-43, D-46 | D-46, with its regression test |
| Seed safety rules | `database_seed_prompt.md`, `seed_data.md`, D-08, D-20 | `seed_data.md` once its rank is approved (C-13) |
| Report with verified, failing, untested, blocked | `testing_security_prompt.md`, `doc.md` section 16, `prompt.md` section 13 | `Agents.md` section 9, extended by the four-way breakdown already adopted |
| Authorization matrix | `testing_security_prompt.md`, `doc.md` section 3 | One matrix in `docs/contracts/` per phase |

## 5. Missing requirements

Nineteen specification gaps are in `docs/documentation_gaps.md` (G-01 to G-19). The ones that block the next phase are G-01 (profile fields), G-02 (what an unverified user may do) and G-04 (display timezone).

Two findings are worth stating plainly:
- `prompt.md` section 8 tells agents to use "the project's approved UGX formatting helper". No such helper exists and no format is approved. It is a decision, not an oversight to fix quietly (G-03).
- `doc.md` section 2 refers to "the documented display-timezone strategy". We documented only that storage is UTC. The display zone is still open (G-04).

## 6. Effect on the roadmap (proposal, not applied)

| Phase | Current (v2) | Proposed after review |
|---|---|---|
| 0 | Foundation (built) | Unchanged. Optional small amendment for the seed report (C-20) |
| 1 | Identity | Adds email verification, resend and signed-in password change (C-15) |
| 2 | Geography and customer profile | Unchanged. Location mechanism needed (G-05) |
| 3 | Vendor onboarding | Becomes vendor and rider applications and review (C-14) |
| 4 | Catalogue and discovery | Unchanged |
| 5 | Orders core, with development payment adapter | Orders core only (C-26) |
| 6 | Payment service boundary | Adds the development payment adapter (C-26) |
| 7 | Delivery: rider onboarding, availability, dispatch | Availability, dispatch and delivery only (C-14) |
| 8 to 10 | Finance, growth and operations, hardening | Unchanged |

`doc.md` numbers its steps from 1 for Foundation, so its step N is my phase N minus 1.

## 7. Foundation versus the new files

| Requirement | Foundation today | Result |
|---|---|---|
| Never run at startup | Tested (F-26) | Matches |
| Refuse production | Tested (F-24) | Matches |
| Refuse database name not ending `_dev` or `_test` | Tested (F-30) | Matches |
| No override | Tested | Matches |
| Never delete or reset tables | No such code | Matches |
| Say plainly when no seeders are registered | Done | Matches |
| Non-zero exit on unsafe configuration or failure | Done | Matches |
| Report environment classification, database name, safety result, registered seeders, counts | Prints one line only | **Gap (C-20)** |
| Database unavailable gives a safe error and non-zero exit | Exits 0 with no seeders (verified) | **Gap (C-20)** |
| No `|safe` in templates, no unexpected autofocus (`prompt.md` sections 7 and 10) | None found | Matches |
| Check layouts at 320 to 375, 390 to 430, 768 and 1280 to 1440 px (`prompt.md` section 9) | Manual checklist lists 320, 768, 1280 | Checklist should add 390 to 430 and 1440. Not applied |

## 8. Items owed from the previous message

Delivered after this review: the revised register (v3.1), and in `IDENTITY_PHASE_PROPOSAL.md` revision 2, the migration design, route contracts, authorization matrix and acceptance tests. Items that depend on unanswered decisions (D-47 to D-54) are marked PENDING in that document.
