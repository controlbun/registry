"""The one seam between the registry and its database.

Everything that touches storage goes through here, so moving off SQLite later is a
change to this file rather than a change everywhere. Migrations are plain portable
SQL and are the source of truth for the schema; nothing here creates a table that
the migrations do not declare, except the ledger that records which migrations ran.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MIGRATIONS_DIR = ROOT / "schema" / "migrations"


def connect(path: str | Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def migrate(conn: sqlite3.Connection) -> list[str]:
    """Apply unapplied migrations in filename order. Returns what it applied."""
    conn.execute(
        "CREATE TABLE IF NOT EXISTS _migration ("
        " name TEXT PRIMARY KEY, applied_at TEXT NOT NULL)"
    )
    done = {r[0] for r in conn.execute("SELECT name FROM _migration")}
    applied = []
    for path in sorted(MIGRATIONS_DIR.glob("*.sql")):
        if path.name in done:
            continue
        conn.executescript(path.read_text())
        conn.execute(
            "INSERT INTO _migration (name, applied_at) VALUES (?, ?)",
            (path.name, datetime.now(timezone.utc).isoformat()),
        )
        applied.append(path.name)
    conn.commit()
    return applied


def claimants(conn: sqlite3.Connection, label: str) -> list[sqlite3.Row]:
    """Every submission claiming a label.

    Returns all of them, in insertion order, with no sort applied. A bare label is
    a view across everyone claiming it, not a lookup that yields one answer, so
    ordering is the caller's explicit choice and never this function's default.

    Across models, and `model_id` comes back on every row because it is part of
    what each submission is since `schema/migrations/010`. Not filtered by model
    here: a label narrowed to one model is a different view and the caller asks
    for it by name, on the model's own page.
    """
    return list(
        conn.execute(
            "SELECT author, model_id, label, version, definition, created_at,"
            " superseded_by, is_synthetic FROM submission WHERE label = ?",
            (label,),
        )
    )
