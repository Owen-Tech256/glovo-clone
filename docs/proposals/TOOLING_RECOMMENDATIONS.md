# Tooling recommendations: CI (P-19), system tests (P-20), JavaScript quality (P-21)

**Status:** recommendations only. No CI configuration has been added and no dependency has been added.

## P-19 CI platform

**What CI must do for this project** (from `Architecture.md` section 13 and `testing_security_prompt.md`):
1. Start a real PostgreSQL 16 database.
2. Install `requirements-dev.txt` on Python 3.12.
3. Run `pip check`, `pytest` (which includes the migration upgrade, downgrade and upgrade tests), and `pip-audit -r requirements.txt`.
4. Run the audit again on a schedule, because advisories appear without any code change (this is how the Werkzeug issue was found).
5. Block merging when any step fails.

**Recommendation:** use the CI built into wherever the repository is hosted. If it is on GitHub, GitHub Actions: PostgreSQL runs as a service container, Python 3.12 setup and pip caching are built in, and scheduled workflows cover the weekly audit. If it is on GitLab, GitLab CI/CD does the same with a `postgres:16` service. The hosting choice decides this, so I need to know where the repository will live. I have not assumed it.

**Practices to adopt whichever platform is chosen:** least-privilege token permissions; third-party actions or images pinned to a full commit or digest rather than a moving tag; no secrets in the workflow (tests need only a throwaway database URL generated inside the job); required status checks on the main branch; the audit job allowed to fail a release but reported separately from the test job so a new advisory is visible without hiding test results. Check current free-tier limits on the chosen platform before relying on it; I have not verified them.

**Not done:** no workflow file, no pipeline, no branch protection.

## P-20 System-level tests with Flask's test client

Approved approach (D-30): multi-step flows run through `app.test_client()` in `tests/system/`, no browser dependency.

What this covers: sign-in and redirect chains, CSRF token round trips (read the token from the rendered form, post it back), cookie behaviour at the header level, role-based access across several requests, the reset flow end to end using the development outbox, and that rendered pages contain the expected structure.

What it cannot cover and **stays manual** (listed in `docs/manual_checks.md`):
- Real layout at phone, tablet and desktop widths, wrapping, overflow and clipping.
- How the focus outline actually looks, and tab order on real pages with a keyboard.
- Content-Security-Policy violations, which only show in a browser console.
- Cookie behaviour over real HTTPS (the `Secure` flag, `SameSite` handling) and in more than one browser.
- Screen reader behaviour and landmark navigation.
- Touch target size and tap behaviour on a real phone.
- Colour as perceived, beyond the computed contrast ratio.
- Print output, if any page is meant to be printed.
- How a real email client renders messages.

If you later decide browser automation is worth it, the usual choices are Playwright or Selenium. Both are new dependencies and need your approval. I would first check that the sandbox or CI can install the browser binaries, since a test setup that cannot run is worse than none.

## P-21 Lightweight JavaScript testing and quality, no build system

**Constraints:** the Foundation Content-Security-Policy forbids inline scripts, `frontend_prompt.md` forbids a frontend build system, and there is no JavaScript yet.

**Recommendation, in order of cost:**

1. **Keep scripts small and structural.** Plain files under `app/static/js/`, loaded as native ES modules (`<script type="module" src=...>`). No bundler, no transpiler, no framework. Pages must work without JavaScript wherever the feature allows it.
2. **Separate logic from the page.** Put pure functions (validation, formatting, state) in modules that do not touch the DOM. Those can be unit tested without a browser.
3. **Test the pure modules with Node's built-in test runner** (`node --test`). It needs Node installed on developer machines and in CI, but **no npm packages**. Node v22 is present in the sandbox I am using; I have not added any file or dependency for it.
4. **Test the server side of every enhancement through the Flask test client**, because the real contract (form fields, validation errors, CSRF) lives on the server.
5. **Verify DOM behaviour manually** in a browser, using the checklist in `manual_checks.md`. A DOM simulation library (for example jsdom) is an npm dependency and I do not recommend it until there is enough JavaScript to justify it.
6. **Linting:** the common choice is ESLint, which means a `package.json` and a development dependency. It is not a build system, but it does add Node tooling to the repository, so it needs your approval. A zero-dependency alternative is `node --check` to catch syntax errors.

**Decision for you:** whether to allow a `package.json` containing development-only tooling (ESLint) once the first JavaScript file exists. Until you decide, the plan is items 1 to 5 and nothing is installed.

## P-23 Fictional development zones (applies from the geography phase)

Constraints I will follow (D-32): zones in development data are clearly fictional and carry an unmistakable label, for example a name starting `DEV FIXTURE:`, plus the seed marker approved under P-13. They never appear in documentation, screens or tests as approved launch zones. Launch zones remain a separate business decision. No real place boundaries are used, so none can be mistaken for coverage claims.
