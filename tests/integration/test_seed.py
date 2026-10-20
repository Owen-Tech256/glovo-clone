import pytest
from sqlalchemy import text

from app import create_app, seeding
from app.extensions import db
from app.seeding import SeedError, Seeder, SeedStats, run_seeders

PROD_FAKE_DB = "postgresql+psycopg://appuser:Zq7pLm29@127.0.0.1:5432/marketplace_test"


def invoke(app):
    return app.test_cli_runner().invoke(args=["seed-dev"])


@pytest.fixture
def probe_table(app, clean_db):
    with app.app_context():
        db.session.execute(text("CREATE TABLE seed_probe (key text PRIMARY KEY, note text)"))
        db.session.commit()
    yield
    with app.app_context():
        db.session.remove()


def probe_count(app):
    with app.app_context():
        count = db.session.execute(text("SELECT count(*) FROM seed_probe")).scalar_one()
        db.session.rollback()
        return count


# F-24
def test_seed_refuses_under_production_and_writes_nothing(production_app, monkeypatch):
    def must_not_run(*args, **kwargs):
        raise AssertionError("seeders must not run under production")

    monkeypatch.setattr(seeding, "run_seeders", must_not_run)
    result = invoke(production_app)
    assert result.exit_code == 1
    assert "Refusing to seed" in result.stderr and "development and testing" in result.stderr


def test_seed_has_no_production_override(production_app, monkeypatch):
    production_app.config["SEED_DEV_ENABLED"] = True  # even if someone forces the flag
    assert invoke(production_app).exit_code == 1


# F-30
def test_seed_refuses_a_database_not_named_dev_or_test(test_database_url):
    other = "postgresql+psycopg://u:p@127.0.0.1:5432/marketplace"
    app = create_app("testing", config_overrides={"SQLALCHEMY_DATABASE_URI": other})
    result = invoke(app)
    assert result.exit_code == 1 and "_dev or _test" in result.stderr


# F-25
def test_seed_with_marketplace_data_is_honest_and_repeatable(app, clean_db):
    from flask_migrate import upgrade
    with app.app_context():
        upgrade()
    def tables():
        with app.app_context():
            names = db.session.execute(
                text("SELECT table_name FROM information_schema.tables WHERE table_schema='public' ORDER BY 1")
            ).scalars().all()
            db.session.rollback()
            return names

    before = tables()
    for _ in range(2):
        result = invoke(app)
        assert result.exit_code == 0
        assert "Seeders run: marketplace_demo_data" in result.output
        assert "Created:" in result.output and "skipped:" in result.output
    assert tables() == before


def test_idempotent_seeder_runs_twice_without_duplicates(app, probe_table, monkeypatch):
    def seed(session):
        result = session.execute(text(
            "INSERT INTO seed_probe VALUES ('k1','fictional') ON CONFLICT (key) DO NOTHING"
        ))
        created = max(result.rowcount, 0)
        return SeedStats(created=created, skipped=1 - created)

    monkeypatch.setattr(seeding, "SEEDERS", [Seeder("probe", seed)])
    first = invoke(app)
    second = invoke(app)
    assert first.exit_code == 0 and "Created: 1; skipped: 0." in first.output
    assert second.exit_code == 0 and "Created: 0; skipped: 1." in second.output
    assert probe_count(app) == 1


def test_seed_rejects_missing_counts_instead_of_reporting_misleading_zeroes(app, probe_table, monkeypatch):
    def incomplete_seeder(session):
        session.execute(text("INSERT INTO seed_probe VALUES ('k1','counts missing')"))
        # Missing SeedStats is a contract violation: do not report a false zero count.

    monkeypatch.setattr(seeding, "SEEDERS", [Seeder("incomplete", incomplete_seeder)])
    result = invoke(app)
    assert result.exit_code == 1
    assert "incomplete" in result.stderr and "TypeError" in result.stderr
    assert probe_count(app) == 0


def test_seed_commit_failure_is_sanitized_and_rolled_back():
    class FailingCommitSession:
        rolled_back = False

        def commit(self):
            raise RuntimeError("postgresql://private-user:secret@private-host failed")

        def rollback(self):
            self.rolled_back = True

    session = FailingCommitSession()
    with pytest.raises(SeedError) as exc:
        run_seeders(session, [Seeder("safe", lambda _session: SeedStats(created=1))])
    assert exc.value.seeder_name == "commit"
    assert exc.value.cause_type == "RuntimeError"
    assert "secret" not in str(exc.value) and "private-host" not in str(exc.value)
    assert session.rolled_back


# F-26
def test_seeders_are_not_invoked_at_startup(test_database_url, monkeypatch):
    def must_not_run(*args, **kwargs):
        raise AssertionError("seeding ran during create_app")

    monkeypatch.setattr(seeding, "run_seeders", must_not_run)
    app = create_app("testing")
    assert app.test_client().get("/health").status_code == 200


# F-29
def test_failing_seeder_rolls_back_and_hides_details(app, probe_table, monkeypatch):
    def good(session):
        session.execute(text("INSERT INTO seed_probe VALUES ('k1','kept?')"))
        return SeedStats(created=1)

    def bad(session):
        session.execute(text("INSERT INTO seed_probe VALUES ('k2','also rolled back')"))
        raise RuntimeError("super-secret-detail")

    monkeypatch.setattr(seeding, "SEEDERS", [Seeder("good", good), Seeder("bad", bad)])
    result = invoke(app)
    assert result.exit_code == 1
    assert "'bad'" in result.stderr and "RuntimeError" in result.stderr and "rolled back" in result.stderr
    assert "super-secret-detail" not in result.output + result.stderr
    assert probe_count(app) == 0


def test_seed_refuses_unreachable_database_before_running_seeders(test_database_url, monkeypatch):
    unreachable = "postgresql+psycopg://u:p@127.0.0.1:9/marketplace_test?connect_timeout=1"
    app = create_app("testing", config_overrides={"SQLALCHEMY_DATABASE_URI": unreachable})
    def must_not_run(*args, **kwargs):
        raise AssertionError("seeder must not run if the database probe fails")
    monkeypatch.setattr(seeding, "run_seeders", must_not_run)
    result = invoke(app)
    assert result.exit_code == 1
    assert "database is unreachable" in result.stderr
    assert "127.0.0.1" not in result.output + result.stderr
    assert "postgresql" not in result.output + result.stderr


def test_seed_reports_created_and_skipped_counts(app, probe_table, monkeypatch):
    def seed(session):
        session.execute(text("INSERT INTO seed_probe VALUES ('k1','fictional') ON CONFLICT (key) DO NOTHING"))
        return SeedStats(created=1, skipped=2)
    monkeypatch.setattr(seeding, "SEEDERS", [Seeder("counted", seed)])
    result = invoke(app)
    assert result.exit_code == 0
    assert "Seeders run: counted" in result.output
    assert "Created: 1; skipped: 2." in result.output
