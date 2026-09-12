"""Default ordering.

These check the properties that make the placeholder honest, not the particular
numbers it produces. The function is meant to be replaced; what must survive the
replacement is that it never reads an eval result and never invents a signal.
"""

from __future__ import annotations

import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from registry import db, order  # noqa: E402

NOW = datetime(2026, 9, 12, 12, 0, tzinfo=timezone.utc)


@pytest.fixture
def conn(tmp_path):
    path = tmp_path / "fixture.db"
    subprocess.run(
        [sys.executable, str(ROOT / "fixtures" / "build.py"), "--db", str(path)],
        check=True, capture_output=True,
    )
    return db.connect(path)


def test_small_corpus_defaults_to_recency(conn):
    assert order.corpus_size(conn) < order.CORPUS_THRESHOLD
    assert order.active_order(conn) == order.ORDER_RECENT


def test_threshold_switches_to_trending(conn):
    for i in range(order.CORPUS_THRESHOLD):
        conn.execute(
            "INSERT INTO submission (author,label,version,definition,created_at,"
            "is_synthetic) VALUES (?,?,?,?,?,1)",
            (f"filler{i}", "kindness", "v1", "filler", "2026-09-12T00:00:00Z"),
        )
    conn.commit()
    assert order.corpus_size(conn) >= order.CORPUS_THRESHOLD
    assert order.active_order(conn) == order.ORDER_TRENDING


def test_trending_collapses_to_recency_with_no_engagement():
    """The property that keeps the placeholder honest on an empty corpus.

    With engagement zero everywhere the numerator is constant, so the ordering is
    decided entirely by age. A newer item outranks an older one and nothing else
    is being claimed.
    """
    newer = order.trending_score(0, hours=1.0)
    older = order.trending_score(0, hours=100.0)
    assert newer > older


def test_engagement_outweighs_age_only_up_to_a_point():
    """Scrutiny lifts an item, and age eventually pulls it back down. Neither term
    is allowed to dominate outright, or the ordering stops being a trade-off."""
    scrutinised_but_old = order.trending_score(10, hours=500.0)
    untouched_but_new = order.trending_score(0, hours=1.0)
    assert untouched_but_new > scrutinised_but_old

    same_age_more_scrutiny = order.trending_score(10, hours=10.0)
    same_age_none = order.trending_score(0, hours=10.0)
    assert same_age_more_scrutiny > same_age_none


def test_engagement_counts_only_other_peoples_work(conn):
    """An author cannot lift their own submission by evaluating it again."""
    before = order.engagement(conn, "alice", "kindness", "v1")

    conn.execute(
        "INSERT INTO eval_suite (id,author,name,version) VALUES (?,?,?,?)",
        ("es_alice_2", "alice", "second-look", "v1"),
    )
    conn.execute(
        "INSERT INTO eval_report (id,eval_suite_id,intervention_id,reported_at,"
        "is_synthetic) VALUES (?,?,?,?,1)",
        ("er_alice_2", "es_alice_2", "iv_alice", "2026-09-12T00:00:00Z"),
    )
    conn.commit()

    assert order.engagement(conn, "alice", "kindness", "v1") == before, (
        "self-evaluation must not register as scrutiny"
    )


def test_attack_registers_as_engagement(conn):
    """Alice carries an attack in the fixtures; bob carries none."""
    assert order.engagement(conn, "alice", "kindness", "v1") > 0
    assert order.engagement(conn, "bob", "kindness", "v1") == 0


def test_caller_can_always_override_the_default(conn):
    rows = db.claimants(conn, "kindness")
    recent = order.apply_order(conn, rows, key=order.ORDER_RECENT, now=NOW)
    trending = order.apply_order(conn, rows, key=order.ORDER_TRENDING, now=NOW)
    assert {r["author"] for r in recent} == {r["author"] for r in trending}
    assert len(recent) == len(rows), "ordering must never drop a claimant"


def test_unknown_ordering_leaves_rows_alone_rather_than_raising(conn):
    rows = db.claimants(conn, "kindness")
    out = order.apply_order(conn, rows, key="by-vibes", now=NOW)
    assert [r["author"] for r in out] == [r["author"] for r in rows]


def test_ordering_reads_no_eval_result():
    """Invariant 4, at the level of this module rather than by grep."""
    source = (ROOT / "src" / "registry" / "order.py").read_text()
    code = "\n".join(
        line for line in source.splitlines()
        if not line.lstrip().startswith("#")
    )
    body = code.split('"""', 2)[-1]
    for column in ("trait_score", "coherence_score", "transfer_score",
                   "necessity_score", "cosine"):
        assert column not in body, (
            f"{column} reached the ordering; measured effect must never decide "
            "placement"
        )


def test_recency_uses_real_timestamps_not_invented_ones(conn):
    rows = db.claimants(conn, "kindness")
    ordered = order.apply_order(conn, rows, key=order.ORDER_RECENT, now=NOW)
    for r in ordered:
        assert r["created_at"], "every row orders on a timestamp that exists"
        datetime.fromisoformat(r["created_at"].replace("Z", "+00:00"))


def test_age_never_goes_negative():
    future = (NOW + timedelta(days=3)).isoformat()
    assert order.age_hours(future, NOW) == 0.0
