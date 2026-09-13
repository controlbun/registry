"""Comparison behavior, against the synthetic fixture corpus.

These assert the shape of what a reader is shown, not the values of anything.
Fixture numbers are fabricated on purpose and asserting on them would only test
that nobody edited the fixture file.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from registry import db
from registry import comparison  # noqa: E402


@pytest.fixture(scope="module")
def conn(tmp_path_factory):
    path = tmp_path_factory.mktemp("db") / "fixture.db"
    subprocess.run(
        [sys.executable, str(ROOT / "fixtures" / "build.py"), "--db", str(path)],
        check=True, capture_output=True,
    )
    return db.connect(path)


def test_bare_label_yields_every_claimant(conn):
    rows = db.claimants(conn, "kindness")
    assert len(rows) == 2, "a label with two claimants must return two"
    assert {r["author"] for r in rows} == {"alice", "bob"}


def test_comparison_reports_the_axis_asymmetry(conn):
    pair = comparison.pairwise(conn, "kindness")[0]
    # Neither author checked what the other did. That gap is the finding, and it is
    # visible only because the registry declines to fix the axes in advance.
    assert pair["axes_only_a_checked"], "alice checked axes bob did not"
    assert pair["axes_only_b_checked"], "bob checked axes alice did not"
    assert pair["axes_both_checked"] == [], "the fixtures overlap on nothing by design"


def test_absent_transfer_is_absent_not_zero(conn):
    pair = comparison.pairwise(conn, "kindness")[0]
    present = [pair["transfer_a"], pair["transfer_b"]]
    assert None in present, "bob measured no transfer and that must survive as None"
    assert 0 not in present and 0.0 not in present, (
        "a missing measurement coerced to zero is a fabricated measurement"
    )


def test_score_with_no_coherence_is_uninterpretable():
    assert comparison.score_state(None) == comparison.SCORE_ABSENT
    assert comparison.score_state({"trait_score": None, "coherence_score": None}) == \
        comparison.SCORE_ABSENT
    assert comparison.score_state({"trait_score": 0.5, "coherence_score": None}) == \
        comparison.SCORE_UNINTERPRETABLE
    assert comparison.score_state({"trait_score": 0.5, "coherence_score": 0.9}) == \
        comparison.SCORE_REPORTABLE


def test_angle_similarity_is_reported_with_its_comparability(conn):
    pair = comparison.pairwise(conn, "kindness")[0]
    # The number is allowed to exist. What is not allowed is presenting it without
    # the context that makes it meaningful, or reading disagreement into it.
    assert pair["angle_comparable"] is True
    assert -1.0 <= pair["angle_similarity"] <= 1.0
    assert "disagreement" not in pair, "geometry is not a verdict about intent"
    assert "rank" not in pair and "score" not in pair


def test_comparison_returns_no_ordering_key(conn):
    pairs = comparison.pairwise(conn, "kindness")
    for p in pairs:
        assert not any(k in p for k in ("rank", "position", "composite", "overall"))


def test_attacks_are_not_filtered_by_disposition(conn):
    iv = conn.execute("SELECT id FROM intervention WHERE author='alice'").fetchone()
    attacks = comparison.attacks_against(conn, iv["id"])
    assert len(attacks) == 1
    a = attacks[0]
    # Attacker and author disagree. Both are recorded and neither is resolved by
    # the registry, because adjudicating is the one thing it does not do.
    assert a["attacker_disposition"] != a["author_disposition"]
    assert a["author_response"]


def test_everything_in_the_corpus_is_flagged_synthetic(conn):
    for table in ("submission", "intervention", "eval_report", "attack"):
        rows = conn.execute(f"SELECT is_synthetic FROM {table}").fetchall()
        assert rows, f"{table} is empty"
        assert all(r["is_synthetic"] == 1 for r in rows), (
            f"{table} holds a row not marked synthetic; fixtures must never be "
            "mistakable for measurements"
        )
