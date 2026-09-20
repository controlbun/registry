"""Comparison behavior, against the real corpus and against a probe.

These assert the shape of what a reader is shown, not the values of anything.
Where a number does appear below it is one the real artifacts re-derive, never a
figure typed into a test.

**Two databases, because the real corpus no longer holds every state.** The
fabricated half of the corpus went on 2026-09-19 and what is left is five
submissions by one author who ran one battery. That corpus genuinely contains a
missing transfer ratio, a pair whose angle is undefined, and a label several
takes claim, so those are checked against it. It contains no attack, no second
author on a label, and no two authors with disjoint confound axes, so those are
checked against `tests/probe.py`, which builds them and throws them away.

The old version of this file ran entirely against the fixture corpus and said so
in its docstring. The reason to split rather than move everything to the probe is
that a check run against real rows can fail for a real reason.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import probe
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from controlbun import db  # noqa: E402
from controlbun import comparison, views  # noqa: E402

REAL_LABEL = "pro-human"


@pytest.fixture(scope="module")
def conn(tmp_path_factory):
    """The probe corpus: two authors on one label who checked nothing in common."""
    return probe.build(tmp_path_factory.mktemp("probe") / "probe.db")


@pytest.fixture(scope="module")
def real(tmp_path_factory):
    """The real corpus, seeded the way `make site` seeds it.

    `artifacts/seed.py` is the corpus builder since the fixtures were removed:
    it drops the database, migrates it and writes the author's own rows, every
    tensor fact confirmed against the vendored bytes before the row is written.
    Pointed at a temporary file so this never touches `registry.db`.
    """
    path = tmp_path_factory.mktemp("real") / "registry.db"
    subprocess.run(
        [sys.executable, str(ROOT / "artifacts" / "seed.py"), "--db", str(path)],
        check=True, capture_output=True,
    )
    return db.connect(path)


def test_bare_label_yields_every_claimant(conn):
    rows = db.claimants(conn, probe.LABEL_A)
    assert len(rows) == 2, "a label with two claimants must return two"
    assert {r["author"] for r in rows} == {"probe-a", "probe-b"}


def test_a_bare_label_does_not_collapse_one_authors_several_takes(real):
    """Four submissions, one author, one word, and all four come back.

    The real corpus is the only place this can be checked, and it is the state
    the corpus is actually in: `soham/pro-human` is four parallel takes that
    differ only in the estimator. Nothing orders them and nothing picks one, so
    a bare label here is a view of four rows by one person rather than of four
    people. A version of `claimants` that deduplicated by author would look like
    a tidy-up and would delete three submissions from the view.
    """
    rows = db.claimants(real, REAL_LABEL)
    assert len(rows) == 4
    assert {r["author"] for r in rows} == {"soham"}, (
        "if a second author has claimed this label, this test is now checking "
        "something weaker than it was written to check"
    )
    assert len({r["version"] for r in rows}) == 4


def test_comparison_reports_the_axis_asymmetry(conn):
    pair = comparison.pairwise(conn, probe.LABEL_A)[0]
    # Neither author checked what the other did. That gap is the finding, and it is
    # visible only because the registry declines to fix the axes in advance.
    assert pair["axes_only_a_checked"], "probe-a checked axes probe-b did not"
    assert pair["axes_only_b_checked"], "probe-b checked axes probe-a did not"
    assert pair["axes_both_checked"] == [], "the probe overlaps on nothing by design"


def test_absent_transfer_is_absent_not_zero(real):
    """A real absence, not a manufactured one.

    `soham/pro-human@L24` carries no control-pair transfer ratio: the arena ran
    that battery on the three layer-32 directions and not on this one, and its
    siblings' numbers are not transferable to it. So every pair this row is in
    reports `None` on one side, and a version of this that filled the gap with a
    zero would be publishing a measurement nobody took.
    """
    pairs = comparison.pairwise(real, REAL_LABEL)
    with_l24 = [p for p in pairs if p["a"].endswith("@L24") or p["b"].endswith("@L24")]
    assert with_l24, "no pair involves the row that has no transfer ratio"
    for pair in with_l24:
        present = [pair["transfer_a"], pair["transfer_b"]]
        assert None in present, "the unmeasured side must survive as None"
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


def test_the_three_score_states_all_occur_in_the_probe(conn):
    """The states above, reached through a database rather than a dict.

    `score_state` takes a row and the three cases are easy to prove against
    literals, which proves the function and not the corpus. These rows put all
    three on the table: one report with a coherence measure beside its trait
    score, one with a trait score and nothing beside it, and rows with no report
    at all.
    """
    states = set()
    for label in (probe.LABEL_A, probe.LABEL_B):
        for row in db.claimants(conn, label):
            states.add(views.claimant_view(conn, row)["score_state"])
    assert states == {
        comparison.SCORE_REPORTABLE,
        comparison.SCORE_UNINTERPRETABLE,
        comparison.SCORE_ABSENT,
    }, f"the probe no longer exercises every score state: {sorted(states)}"


def test_angle_similarity_is_reported_with_its_comparability(real):
    """Recomputed from two real tensors in one model's basis at one layer.

    The number is allowed to exist. What is not allowed is presenting it without
    the context that makes it meaningful, or reading disagreement into it.
    """
    comparable = [
        p for p in comparison.pairwise(real, REAL_LABEL) if p["angle_comparable"]
    ]
    assert comparable, "no pair in the corpus is comparable, so this checks nothing"
    for pair in comparable:
        assert -1.0 <= pair["angle_similarity"] <= 1.0
        assert "disagreement" not in pair, "geometry is not a verdict about intent"
        assert "rank" not in pair and "score" not in pair


def test_an_undefined_angle_says_which_kind_of_nothing_it_is(real):
    """`soham/pro-human@L24` sits at layer 24 and its siblings at layer 32.

    There is no angle between them, and that is a statement about what the two
    objects are rather than a gap in the data. "Not comparable" on its own reads
    as missing data, so the reason is carried out with the None.
    """
    pairs = comparison.pairwise(real, REAL_LABEL)
    undefined = [p for p in pairs if p["angle_similarity"] is None]
    assert undefined, "every pair is comparable, so this check is inert"
    for pair in undefined:
        assert pair["angle_comparable"] is False
        assert pair["angle_why"], (
            "an angle that does not exist has to say why, or a reader reads a "
            "statement about layers as a missing measurement"
        )


def test_comparison_returns_no_ordering_key(real):
    for p in comparison.pairwise(real, REAL_LABEL):
        assert not any(k in p for k in ("rank", "position", "composite", "overall"))


def test_attacks_are_not_filtered_by_disposition(conn):
    """The real corpus holds no attack, so this is the probe's to prove.

    Nobody has attacked anything here, which is a fact about a registry that
    took no uploads rather than about the mechanism. The mechanism still has to
    be the one it claims to be: an attack is evidence the author did not choose,
    so it is never filtered by what either party calls it.
    """
    iv = conn.execute("SELECT id FROM intervention WHERE author='probe-a'").fetchone()
    attacks = comparison.attacks_against(conn, iv["id"])
    assert len(attacks) == 1
    a = attacks[0]
    # Attacker and author disagree. Both are recorded and neither is resolved by
    # the registry, because adjudicating is the one thing it does not do.
    assert a["attacker_disposition"] != a["author_disposition"]
    assert a["author_response"]


def test_nothing_in_the_real_corpus_is_marked_synthetic(real):
    """The inverse of the check this file used to make, and the point of the change.

    This asserted that every row in the corpus was flagged synthetic, which was
    true while the corpus was a fixture set. `DECISIONS.md` 2026-09-19 removed
    that set because a public site whose corpus is half fabricated invites "is
    this real". So the property is now the opposite one, and it is worth holding:
    a fabricated row reaching the corpus that seeds the published site is the
    failure the flag exists to make visible, and nothing would notice it here
    unless something asked.
    """
    # Every table carrying the flag. `pin`, `recipe` and `eval_suite` do not
    # have the column and are not listed, rather than being listed and skipped:
    # a loop that skips half its own list is how a check goes quietly inert.
    for table in ("submission", "intervention", "eval_report", "namespace_claim"):
        rows = real.execute(f"SELECT is_synthetic FROM {table}").fetchall()
        assert rows, f"{table} is empty, so this check looked at nothing"
        assert all(r["is_synthetic"] == 0 for r in rows), (
            f"{table} holds a row marked synthetic. Every row that reaches the "
            "published corpus is somebody's real work, and a fabricated one "
            "among them is what the removed fixture set was removed for"
        )


def test_every_probe_row_is_marked_synthetic(conn):
    """And the probe is flagged the whole way down, so it cannot be mistaken.

    The probe exists to put states on the table that the real corpus does not
    contain. Nothing stops somebody copying one of its rows into a seeder except
    that every one of them says what it is, in the column the exporter and the
    falsifier both read.
    """
    for table in ("submission", "intervention", "eval_report", "attack",
                  "support_card", "namespace_claim"):
        rows = conn.execute(f"SELECT is_synthetic FROM {table}").fetchall()
        assert rows, f"{table} is empty"
        assert all(r["is_synthetic"] == 1 for r in rows), (
            f"{table} holds a probe row not marked synthetic; a probe must never "
            "be mistakable for a measurement"
        )


def test_confound_axes_belong_to_the_artifact_not_to_its_author(real):
    """A page may not claim a measurement that was taken on something else.

    Two real faults, one inside the other. `claimant_view` read confound axes
    with `SELECT ... FROM eval_suite WHERE author = ?`, so every submission by
    an author inherited the axes of every suite that author had ever written:
    `soham/trauma`, which has no confound data of any kind, rendered four axes
    borrowed from `soham/pro-human` on another label and another model.

    Joining through `eval_report` fixed the borrowing and left the subtler one.
    A suite declares a battery and a report says what was run, and
    `soham/pro-human@L24` has a report from a four-axis suite with a null
    `confound_json`, because that battery was only ever run at layer 32. So an
    axis counts as checked when this artifact's own report carries a number
    for it, and not before.

    Read off a freshly seeded corpus rather than off `registry.db`, which a
    clean checkout does not have: a version of this that connected to a missing
    file got an empty database and passed while checking nothing.
    """
    rows = real.execute("SELECT * FROM submission").fetchall()
    assert rows, "no submissions, so this check looked at nothing"
    for row in rows:
        view = views.claimant_view(real, row)
        measured: set[str] = set()
        iv = real.execute(
            "SELECT id FROM intervention WHERE author=? AND label=? AND version=?",
            (row["author"], row["label"], row["version"]),
        ).fetchone()
        if iv:
            for r in real.execute(
                "SELECT e.confound_json FROM eval_report e"
                " JOIN eval_suite s ON s.id = e.eval_suite_id"
                " WHERE e.intervention_id=? AND s.author=?",
                (iv["id"], row["author"]),
            ):
                if r["confound_json"]:
                    measured.update(json.loads(r["confound_json"]))
        assert set(view["axes"]) == measured, (
            f"{row['author']}/{row['label']}@{row['version']} lists axes "
            f"{sorted(view['axes'])} and its own reports measured "
            f"{sorted(measured)}"
        )
