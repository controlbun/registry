"""Default ordering for multi-submission views.

Below a corpus size where ranking means anything, the default is recency, because
recency is the only signal that exists and pretending otherwise would mean
inventing one. Above it, a decayed engagement score takes over.

**The trending function here is provisional and meant to be replaced.** It is a
placeholder chosen to be honest rather than clever: every input is a real count or
a real timestamp, nothing is fabricated, and with no engagement anywhere it
degrades exactly into recency rather than into noise. Someone who actually works
on ranking should replace it.

Two properties it deliberately keeps:

- **No eval result feeds the order.** Not trait score, not coherence, not transfer.
  A direction that also moves sentiment and verbosity feels more effective in use
  because more is happening, so ordering on measured effect would systematically
  favor the confounded submission and placement would compound it.
- **Engagement means scrutiny by other people**, not downloads. Evaluations and
  attacks by someone other than the author, which is the signal the audit queue
  wants anyway.

The loop worth knowing about: whatever sits at the top gets looked at, which raises
its engagement, which keeps it at the top. That is real and this function does not
solve it. It is one more reason the ordering is switchable and labeled on screen.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone

# Below this many submissions, engagement data is too thin to mean anything and
# recency is the whole signal.
CORPUS_THRESHOLD = 100

# How fast engagement decays with age. Hacker News uses 1.8 on votes; this is
# gentler because scrutiny accrues more slowly than votes do. Provisional.
GRAVITY = 1.5

# Keeps a brand-new item from dividing by something near zero.
AGE_OFFSET_HOURS = 2.0

ORDER_RECENT = "recently-added"
ORDER_TRENDING = "trending"


def _parse(ts: str) -> datetime:
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))


def age_hours(created_at: str, now: datetime) -> float:
    delta = now - _parse(created_at)
    return max(delta.total_seconds() / 3600.0, 0.0)


def engagement(conn: sqlite3.Connection, author: str, label: str, version: str) -> int:
    """How many people other than the author have engaged with this submission.

    Evaluations run by someone else plus attacks against it. A real count of real
    rows; when nobody has engaged it is zero, which is a fact rather than a gap.
    """
    iv = conn.execute(
        "SELECT id FROM intervention WHERE author=? AND label=? AND version=?",
        (author, label, version),
    ).fetchone()
    if iv is None:
        return 0

    others = conn.execute(
        "SELECT count(*) FROM eval_report r"
        " JOIN eval_suite s ON s.id = r.eval_suite_id"
        " WHERE r.intervention_id = ? AND s.author != ?",
        (iv["id"], author),
    ).fetchone()[0]
    attacks = conn.execute(
        "SELECT count(*) FROM attack WHERE intervention_id = ?", (iv["id"],)
    ).fetchone()[0]
    return int(others) + int(attacks)


def trending_score(engagement_count: int, hours: float) -> float:
    """Decayed scrutiny.

    The numerator is engagement plus one, so a submission nobody has touched still
    carries a positive value that decays purely with age. That is what makes this
    collapse into recency on an empty corpus instead of flattening into ties.
    """
    return (engagement_count + 1) / ((hours + AGE_OFFSET_HOURS) ** GRAVITY)


def corpus_size(conn: sqlite3.Connection) -> int:
    return conn.execute("SELECT count(*) FROM submission").fetchone()[0]


def active_order(conn: sqlite3.Connection) -> str:
    """Which default applies, given how much corpus there is to order."""
    return ORDER_RECENT if corpus_size(conn) < CORPUS_THRESHOLD else ORDER_TRENDING


def apply_order(
    conn: sqlite3.Connection,
    rows: list[sqlite3.Row],
    key: str | None = None,
    now: datetime | None = None,
) -> list[sqlite3.Row]:
    """Arrange rows under an explicitly named ordering.

    `key` is always available to the caller, so the default is a starting point a
    reader can change rather than a verdict. An unrecognized key leaves the rows
    in storage order rather than raising, because an unknown ordering is a request
    this build does not implement, not an error in the data.
    """
    now = now or datetime.now(timezone.utc)
    key = key or active_order(conn)

    if key == ORDER_RECENT:
        return sorted(rows, key=lambda r: _parse(r["created_at"]), reverse=True)

    if key == ORDER_TRENDING:
        def weight(r: sqlite3.Row) -> float:
            return trending_score(
                engagement(conn, r["author"], r["label"], r["version"]),
                age_hours(r["created_at"], now),
            )
        return sorted(rows, key=weight, reverse=True)

    return list(rows)
