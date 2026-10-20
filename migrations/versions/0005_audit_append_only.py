"""Append-only audit safeguards and controlled retention maintenance.

Revision ID: 0005
Revises: 0004
"""
from flask import current_app

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "audit_retention_policy",
        sa.Column("id", sa.Integer(), sa.Identity(), nullable=False),
        sa.Column("public_id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("retention_days", sa.Integer(), nullable=False),
        sa.Column("approver", sa.String(length=120), nullable=False),
        sa.Column("legal_basis", sa.String(length=500), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("retention_days > 0", name="ck_audit_retention_policy_retention_days_positive"),
        sa.CheckConstraint("length(trim(approver)) > 0", name="ck_audit_retention_policy_approver_nonempty"),
        sa.CheckConstraint("length(trim(legal_basis)) > 0", name="ck_audit_retention_policy_legal_basis_nonempty"),
        sa.PrimaryKeyConstraint("id", name="pk_audit_retention_policy"),
        sa.UniqueConstraint("public_id", name="uq_audit_retention_policy_public_id"),
    )

    # SECURITY DEFINER functions use an empty search_path and fully qualified names.
    op.execute(r"""
    CREATE FUNCTION public.audit_guard_insert() RETURNS trigger
    LANGUAGE plpgsql SECURITY DEFINER SET search_path = '' AS $$
    BEGIN
      IF NEW.action IN ('audit.maintenance_run', 'audit.retention_policy_approved')
         AND pg_catalog.pg_trigger_depth() < 2 THEN
        RAISE EXCEPTION 'recorder-only audit action';
      END IF;
      RETURN NEW;
    END;
    $$;

    CREATE FUNCTION public.audit_guard_mutation() RETURNS trigger
    LANGUAGE plpgsql SECURITY DEFINER SET search_path = '' AS $$
    BEGIN
      RAISE EXCEPTION 'audit records are append-only';
    END;
    $$;

    CREATE FUNCTION public.audit_guard_policy_mutation() RETURNS trigger
    LANGUAGE plpgsql SECURITY DEFINER SET search_path = '' AS $$
    BEGIN
      RAISE EXCEPTION 'retention policies are append-only';
    END;
    $$;

    CREATE FUNCTION public.audit_record_policy_approval() RETURNS trigger
    LANGUAGE plpgsql SECURITY DEFINER SET search_path = '' AS $$
    BEGIN
      INSERT INTO public.audit_logs
        (actor_label, action, entity_type, entity_id, after_data, event_metadata)
      VALUES
        (NEW.approver, 'audit.retention_policy_approved', 'audit_retention_policy',
         NEW.public_id::text,
         pg_catalog.jsonb_build_object('retention_days', NEW.retention_days,
                                       'legal_basis', NEW.legal_basis),
         pg_catalog.jsonb_build_object('policy_id', NEW.public_id::text));
      RETURN NEW;
    END;
    $$;

    CREATE FUNCTION public.audit_guard_delete() RETURNS trigger
    LANGUAGE plpgsql SECURITY DEFINER SET search_path = '' AS $$
    DECLARE policy_row record;
    DECLARE maintenance_role_exists boolean;
    BEGIN
      SELECT EXISTS (SELECT 1 FROM pg_catalog.pg_roles WHERE rolname = 'audit_maintenance')
        INTO maintenance_role_exists;
      IF NOT maintenance_role_exists OR NOT pg_catalog.pg_has_role(session_user, 'audit_maintenance', 'member') THEN
        RAISE EXCEPTION 'audit deletion requires authorized maintenance role';
      END IF;
      SELECT id, public_id, retention_days INTO policy_row
        FROM public.audit_retention_policy ORDER BY created_at DESC, id DESC LIMIT 1;
      IF NOT FOUND THEN
        RAISE EXCEPTION 'audit deletion requires an approved retention policy';
      END IF;
      IF OLD.created_at >= pg_catalog.now() - pg_catalog.make_interval(days => policy_row.retention_days) THEN
        RAISE EXCEPTION 'audit row is within the retention period';
      END IF;
      RETURN OLD;
    END;
    $$;

    CREATE FUNCTION public.audit_record_maintenance_run() RETURNS trigger
    LANGUAGE plpgsql SECURITY DEFINER SET search_path = '' AS $$
    DECLARE policy_row record;
    DECLARE deleted_count bigint;
    DECLARE oldest_deleted timestamptz;
    DECLARE newest_deleted timestamptz;
    BEGIN
      SELECT id, public_id, retention_days INTO policy_row
        FROM public.audit_retention_policy ORDER BY created_at DESC, id DESC LIMIT 1;
      SELECT pg_catalog.count(*), pg_catalog.min(created_at), pg_catalog.max(created_at)
        INTO deleted_count, oldest_deleted, newest_deleted
        FROM deleted_audit_rows;
      IF deleted_count > 0 THEN
        INSERT INTO public.audit_logs
          (actor_label, action, entity_type, entity_id, after_data, event_metadata)
        VALUES
          (session_user::text, 'audit.maintenance_run', 'audit_logs', policy_row.public_id::text,
           pg_catalog.jsonb_build_object('deleted', deleted_count,
             'oldest_deleted_at', oldest_deleted, 'newest_deleted_at', newest_deleted),
           pg_catalog.jsonb_build_object('policy_id', policy_row.public_id::text,
             'retention_days', policy_row.retention_days, 'operator', session_user::text));
      END IF;
      RETURN NULL;
    END;
    $$;

    REVOKE ALL ON FUNCTION public.audit_guard_insert() FROM PUBLIC;
    REVOKE ALL ON FUNCTION public.audit_guard_mutation() FROM PUBLIC;
    REVOKE ALL ON FUNCTION public.audit_guard_policy_mutation() FROM PUBLIC;
    REVOKE ALL ON FUNCTION public.audit_record_policy_approval() FROM PUBLIC;
    REVOKE ALL ON FUNCTION public.audit_guard_delete() FROM PUBLIC;
    REVOKE ALL ON FUNCTION public.audit_record_maintenance_run() FROM PUBLIC;

    CREATE TRIGGER trg_audit_logs_guard_insert BEFORE INSERT ON public.audit_logs
      FOR EACH ROW EXECUTE FUNCTION public.audit_guard_insert();
    CREATE TRIGGER trg_audit_logs_no_update BEFORE UPDATE OR TRUNCATE ON public.audit_logs
      FOR EACH STATEMENT EXECUTE FUNCTION public.audit_guard_mutation();
    CREATE TRIGGER trg_audit_logs_guard_delete BEFORE DELETE ON public.audit_logs
      FOR EACH ROW EXECUTE FUNCTION public.audit_guard_delete();
    CREATE TRIGGER trg_audit_logs_record_maintenance AFTER DELETE ON public.audit_logs
      REFERENCING OLD TABLE AS deleted_audit_rows FOR EACH STATEMENT
      EXECUTE FUNCTION public.audit_record_maintenance_run();
    CREATE TRIGGER trg_audit_policy_no_update_delete BEFORE UPDATE OR DELETE OR TRUNCATE
      ON public.audit_retention_policy FOR EACH STATEMENT
      EXECUTE FUNCTION public.audit_guard_policy_mutation();
    CREATE TRIGGER trg_audit_policy_record_approval AFTER INSERT ON public.audit_retention_policy
      FOR EACH ROW EXECUTE FUNCTION public.audit_record_policy_approval();

    REVOKE CREATE ON SCHEMA public FROM PUBLIC;
    """)

    # Trigger functions must not be callable directly by any ordinary role.
    # Role grants/membership are deliberately provisioned by deployment, not migrations.
    for fn in (
        "audit_guard_insert", "audit_guard_mutation", "audit_guard_policy_mutation",
        "audit_record_policy_approval", "audit_guard_delete", "audit_record_maintenance_run",
    ):
        op.execute(f"REVOKE ALL ON FUNCTION public.{fn}() FROM PUBLIC")


def downgrade():
    app_env = str(current_app.config.get("APP_ENV", "production")).strip().lower()
    if app_env == "production":
        raise RuntimeError("Refusing to downgrade audit append-only protections in production.")

    op.execute("DROP TRIGGER IF EXISTS trg_audit_policy_record_approval ON public.audit_retention_policy")
    op.execute("DROP TRIGGER IF EXISTS trg_audit_policy_no_update_delete ON public.audit_retention_policy")
    op.execute("DROP TRIGGER IF EXISTS trg_audit_logs_record_maintenance ON public.audit_logs")
    op.execute("DROP TRIGGER IF EXISTS trg_audit_logs_guard_delete ON public.audit_logs")
    op.execute("DROP TRIGGER IF EXISTS trg_audit_logs_no_update ON public.audit_logs")
    op.execute("DROP TRIGGER IF EXISTS trg_audit_logs_guard_insert ON public.audit_logs")
    for fn in (
        "audit_record_maintenance_run", "audit_guard_delete", "audit_record_policy_approval",
        "audit_guard_policy_mutation", "audit_guard_mutation", "audit_guard_insert",
    ):
        op.execute(f"DROP FUNCTION IF EXISTS public.{fn}()")
    op.drop_table("audit_retention_policy")
