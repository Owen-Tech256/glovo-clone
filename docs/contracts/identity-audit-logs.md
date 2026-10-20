# Identity audit-log contract (schema batch 0004)

## Scope

Migration `0004_audit_logs` creates structured audit-event persistence only. It does not add audit-writing services, route integration, triggers, append-only permissions, retention policy, or retention deletion. Those protections belong to the separately reviewed `0005_audit_append_only` batch.

## Schema invariants

- `public_id` is a unique public UUID; internal integer `id` is not an external entity identifier.
- An event must identify its actor using either `actor_user_id` or `actor_label` (or both).
- `actor_user_id` references `users.id` with `ON DELETE RESTRICT` to preserve audit attribution.
- `actor_label` is for explicitly identified maintenance/development operators such as `seed-dev`; do not accept arbitrary user-provided labels as trusted identity.
- `entity_id` stores the entity's public identifier as text, never its internal database ID.
- `before_data`, `after_data`, and `event_metadata` are PostgreSQL JSONB; `ip_address` is PostgreSQL INET.
- Indexes support entity history, actor history, and action history in creation-time order.
- IP addresses are stored only for events that are intentionally audited; this table is not a general request log.

## Data minimization and allowlists

Before any audit writer is implemented, each audited entity must have a fixed allowlist of fields eligible for `before_data` and `after_data`. Never include password hashes, raw or hashed authentication tokens, email addresses, session cookies, credentials, or other secrets. Metadata must be reviewed for the same risk. Do not record an IP address for unaudited page views.

## Required follow-on protections

The schema does not itself make rows append-only. Batch `0005` must implement and test the Revision 6 / D-76 / D-85 protections: separated table-owner, application and maintenance roles; safe privileged functions with empty `search_path`; no dynamic SQL; no forged maintenance/policy events; immutable approved retention policies; no deletion without an approved policy and evidence; no `UPDATE` or `TRUNCATE`; and documented closure-evidence queries. No retention period or legal basis is invented in this batch.
