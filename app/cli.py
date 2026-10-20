"""Flask CLI commands."""
import click
from flask import Flask, current_app
from flask.cli import with_appcontext
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.extensions import db


@click.command("seed-dev")
@with_appcontext
def seed_dev_command() -> None:
    """Load fictional, deterministic development data. Refuses production."""
    from app import seeding
    from app.seeding.guard import check_seed_allowed

    allowed, reason = check_seed_allowed(current_app)
    if not allowed:
        click.echo(f"Refusing to seed: {reason}", err=True)
        raise click.exceptions.Exit(1)
    # Probe reachability before invoking any seeder; never print the DB URL or driver error.
    try:
        db.session.execute(text("SELECT 1"))
        db.session.rollback()
    except SQLAlchemyError as exc:
        db.session.rollback()
        click.echo("Seeding failed: the configured database is unreachable. No data was changed.", err=True)
        raise click.exceptions.Exit(1) from None

    try:
        ran = seeding.run_seeders(db.session)
    except seeding.SeedError as exc:
        click.echo(
            f"Seeding failed in '{exc.seeder_name}' ({exc.cause_type}). The transaction was rolled back.",
            err=True,
        )
        raise click.exceptions.Exit(1) from exc
    if not ran:
        click.echo("No seeders are registered yet. Nothing was seeded.")
        click.echo("Created: 0; skipped: 0.")
    else:
        names = ", ".join(item.name for item in ran)
        created = sum(item.created for item in ran)
        skipped = sum(item.skipped for item in ran)
        click.echo(f"Seeders run: {names}")
        click.echo(f"Created: {created}; skipped: {skipped}.")


def register_cli(app: Flask) -> None:
    app.cli.add_command(seed_dev_command)
