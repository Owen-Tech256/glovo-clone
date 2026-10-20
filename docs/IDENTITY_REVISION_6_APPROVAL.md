# Identity Phase Revision 6 — approval record

**Approved by the project owner on 2026-10-12.** This authorizes implementation of the Revision 6 Identity plan in small, testable batches, while preserving the Foundation architecture.

- D-78: reject `zxcvbn`; do not add it.
- D-82: 20 password-change attempts/hour/IP, counting only attempts reaching the current-password check, plus 5/hour/user.
- D-83: fail closed if shared rate-limit storage fails; no swallowed errors or memory fallback; verify connectivity at production startup.
- D-84: readiness checks the rate-limit store as well as the database; liveness stays separate.
- D-85: approve the full audit-retention hardening described in Revision 6.
- Test infrastructure: role-dependent tests use an isolated disposable PostgreSQL cluster and dedicated restricted test role with `CREATEROLE`; never the application or production role; destroy the cluster after tests.
- O-1: Revision 6 is approved for implementation. Phase 2 remains blocked until Identity acceptance is verified and the owner explicitly approves transition.

This approval does not declare the system production-ready or close release blockers. Real shared-store selection and deployment verification, production log canaries, application/database role separation, email provider setup, and the legal basis/retention period remain release requirements.
