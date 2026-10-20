# Documentation gaps

Updated 2026-10-10 after the owner supplied `doc.md`, `prompt.md` (version 2) and `seed_data.md`.
Nothing here is assumed. Items stay listed until the owner supplies the material or approves a replacement.

## 1. Files

| File | Status | Notes |
|---|---|---|
| `doc.md` | **Received and read in full** | Describes itself as a proposed requirements document that follows the approved documents. Its rank in the source-of-truth order is pending (proposed change D-47). |
| `prompt.md` version 2 | **Received and read in full** | Appears to supersede `frontend_prompt.md`. Supersession is pending confirmation (D-47). |
| `seed_data.md` | **Received and read in full** | Overlaps `database_seed_prompt.md` and is stricter in places. Supersession is pending confirmation (D-47). |
| `Design/` reference screenshots, brand assets, component and inspiration references | **STILL MISSING** | `reference_register.md` lists every entry as "To be added". Blocks final visual decisions (P-09). Until supplied, the provisional `design_tokens.md` is the only visual source, as `prompt.md` section 2 also states. |

Review of the three files: `docs/proposals/SPEC_REVIEW_DOC_PROMPT_SEED.md`. Proposed register changes: `docs/proposals/REGISTER_CHANGES_PROPOSED.md`.

## 2. Requirements the new files refer to that no document defines

These are specification gaps, not missing files. Each needs an owner decision or a document before the phase that needs it. I have not filled any of them in.

| ID | Missing specification | Referenced by | Needed before |
|---|---|---|---|
| G-01 | Permitted customer profile fields (what a customer may view and edit) | PRD FR-CUST-001; `doc.md` section 4; approved P-29 | The `/account` page |
| G-02 | What an unverified user may and may not do | Approved P-26; `doc.md` section 4 | Identity |
| G-03 | UGX display format and the "approved UGX formatting helper" | `prompt.md` section 8 (the helper does not exist) | First page that shows a price |
| G-04 | Display timezone strategy | `doc.md` sections 2 and 11; `prompt.md`; P-10 | First page that shows a time |
| G-05 | Location selection mechanism (typed address, zone list, map, or geolocation) and any map provider. Geolocation is currently denied by the Permissions-Policy (A-04) | `doc.md` section 4; `prompt.md` section 5 landing header | Geography phase |
| G-06 | Vendor and rider application status vocabulary. PRD and `doc.md` differ (see C-16) | PRD FR-VEND-003; `doc.md` section 5 | Applications phase |
| G-07 | Vendor and rider required documents and review rules | PRD section 8 question 8; `doc.md` sections 5 and 6 | Applications phase |
| G-08 | Supported business categories, including regulated ones such as pharmacy | PRD section 8 question 13; P-22; `seed_data.md` layer 1 | Catalogue phase |
| G-09 | Ranking rules for "popular", "featured" and "top sellers" sections | PRD section 8 question 15; `doc.md` section 4 | Discovery. Until approved these sections stay off |
| G-10 | Search behaviour for businesses, products and categories (matching method, any database extension) | `doc.md` section 4 | Catalogue phase |
| G-11 | Meaning of the "service/outbox abstraction" for notifications (a delivery interface, or a database outbox table with a delivery worker) | `doc.md` sections 8 and 11 | Identity (email) and notifications phase |
| G-12 | How internal dashboards are organised: separate support, operations, finance and super-admin areas, or one `admin/` area with permission-gated sections | `doc.md` sections 7 to 10; `page_inventory.md`; `Architecture.md` | First internal dashboard |
| G-13 | Whether roles and permissions are editable in an admin screen or defined in code | `doc.md` section 10; `page_inventory.md`; approved D-36 | First admin screen |
| G-14 | Audit-log viewer: what filters are "privacy-conscious" | `doc.md` section 10 | Admin audit screen |
| G-15 | Default page sizes and the sort and filter allowlists for lists | `doc.md` section 2 | First list page |
| G-16 | Business questions in PRD section 8 (15), plus tax, legal and data-retention policy | PRD; `backend_prompt.md` | Per phase (see the decision register) |
| G-17 | Delivery state names and payment state names (sources disagree) | C-08, C-09 | Orders and payments phases |
| G-18 | Proof-of-pickup and proof-of-delivery specification | `doc.md` section 6 | Delivery phase |
| G-19 | Support case statuses and escalation categories | `doc.md` section 7 | Support phase |
| G-20 | Which internal roles may suspend, reinstate, disable accounts and assign roles. Phase 1 proposes `super_admin` only | Approved D-35, D-39; PRD FR-ADM-008 names no role | Identity |
| G-21 | Retention and privacy handling of IP addresses and other personal data stored in audit rows | `doc.md` section 10 audit viewer; PRD data-retention question | Identity |

## 3. Foundation items that still need manual work

- Browser checks listed in `docs/manual_checks.md` have not been executed.
