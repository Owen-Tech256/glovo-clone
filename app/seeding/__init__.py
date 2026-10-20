"""Development seed registry for `flask seed-dev`.

Rules (decision D-08): never runs at startup, refuses production, only seeds models
that exist, safe to repeat, rolls back on failure. Foundation registers no seeders
because no business tables exist yet. Each later phase appends its own seeder here.
"""
from collections.abc import Callable
from dataclasses import dataclass

from sqlalchemy.orm import scoped_session


@dataclass(frozen=True)
class SeedStats:
    """Counts reported by a seeder; counts must reflect committed inserts/skips."""
    created: int = 0
    skipped: int = 0

    def __post_init__(self):
        if self.created < 0 or self.skipped < 0:
            raise ValueError("seed counts cannot be negative")


@dataclass(frozen=True)
class Seeder:
    name: str
    run: Callable[[scoped_session], SeedStats]


@dataclass(frozen=True)
class SeederRun:
    name: str
    created: int = 0
    skipped: int = 0


# Ordered by dependency. Empty until a phase adds models that need development data.
SEEDERS: list[Seeder] = []


class SeedError(Exception):
    """A seeder failed. Carries the seeder name and exception class only, never the message."""

    def __init__(self, seeder_name: str, cause_type: str):
        super().__init__(f"Seeder '{seeder_name}' failed ({cause_type}).")
        self.seeder_name = seeder_name
        self.cause_type = cause_type


def run_seeders(session, seeders: list[Seeder] | None = None) -> list[SeederRun]:
    """Run every seeder in one transaction. Roll back everything if any seeder raises."""
    registry = SEEDERS if seeders is None else seeders
    ran: list[SeederRun] = []
    for seeder in registry:
        try:
            result = seeder.run(session)
            if not isinstance(result, SeedStats):
                # Reporting zero for a seeder that inserted rows but forgot to
                # return counts would be misleading. Make the contract explicit.
                raise TypeError("seeders must return SeedStats with created/skipped counts")
        except Exception as exc:
            session.rollback()
            raise SeedError(seeder.name, type(exc).__name__) from exc
        ran.append(SeederRun(seeder.name, result.created, result.skipped))
    if ran:
        try:
            session.commit()
        except Exception as exc:
            session.rollback()
            # Commit errors may contain connection strings or server details.
            # Convert them to the same sanitized CLI contract as seeder failures.
            raise SeedError("commit", type(exc).__name__) from exc
    return ran

# Development data registry; never runs automatically.
from app.seeding.marketplace_seed import run as _marketplace_seed
SEEDERS.append(Seeder(name="marketplace_demo_data", run=_marketplace_seed))
