"""Comparison: derived, never authored.

Named `comparison` and not `compare` because the package exposes a public
`compare()` function. When both existed, `from . import compare` bound the
function over the module and every attribute access on it failed at runtime
rather than at import.

Computed on demand between submissions that share a label. There is no table
behind this and there should not be one, because a stored comparison is an
opinion with a schema attached.

What this deliberately does not do: produce a composite score, order the pairs,
or say which submission is better. It reports what each author measured, what
each author did not, and where the two disagree on ground they both covered. The
judgment is the reader's and the registry's job is to make it informed.
"""

from __future__ import annotations

import json
import sqlite3
from functools import lru_cache
from pathlib import Path

import numpy as np
from safetensors.numpy import load_file

from . import ref as _refs
from .artifact import local_path

ROOT = Path(__file__).resolve().parents[2]


def _ref(row) -> str:
    """One row's reference, through the module that owns the format."""
    return _refs.format(
        row["author"], row["model_id"], row["label"], row["version"]
    )

# A trait score with no coherence measure beside it is not a small effect, it is a
# broken instrument. Judge-human agreement ran 81% where text held together and 42%
# where it degenerated, and one arm inverted sign outright.
SCORE_ABSENT = "absent"
SCORE_UNINTERPRETABLE = "uninterpretable"
SCORE_REPORTABLE = "reportable"


@lru_cache(maxsize=None)
def load_vector(artifact_path: str) -> np.ndarray:
    """Cached, because pairing is quadratic and loading is not free.

    Without this, n claimants on one label cost n(n-1) reads of n distinct files:
    9,900 loads at n=100 where 100 would do. The cache is keyed on path and the
    artifacts are immutable, so a stale entry is not reachable.
    """
    tensors = load_file(str(local_path(artifact_path, root=ROOT)))
    return next(iter(tensors.values()))


def angle_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Cosine between two interventions.

    A fact about geometry and nothing more. Vectors that are indistinguishable in
    behavior can sit far apart in angle (arXiv:2602.06801), so a low value here is
    not evidence that two authors disagree, and callers must not present it that
    way or rank on it.
    """
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


def score_state(report: sqlite3.Row | None) -> str:
    """Absence is its own state. It is never an error and never a zero."""
    if report is None or report["trait_score"] is None:
        return SCORE_ABSENT
    if report["coherence_score"] is None:
        return SCORE_UNINTERPRETABLE
    return SCORE_REPORTABLE


def _axes(conn: sqlite3.Connection, author: str) -> set[str]:
    rows = conn.execute(
        "SELECT confound_axes_json FROM eval_suite WHERE author = ?", (author,)
    )
    out: set[str] = set()
    for r in rows:
        if r["confound_axes_json"]:
            out.update(json.loads(r["confound_axes_json"]))
    return out


def _submissions(conn: sqlite3.Connection, label: str) -> list[sqlite3.Row]:
    return list(
        conn.execute(
            "SELECT author, model_id, label, version FROM submission"
            " WHERE label = ?",
            (label,),
        )
    )


def _intervention(conn: sqlite3.Connection, row: sqlite3.Row):
    """The artifact for one submission, keyed on all four identity columns.

    Three of the four used to be enough and stopped being enough in
    `schema/migrations/010`. An author holding one label on two models has two
    artifacts under the old key, and this returned whichever the database
    reached first, which is a pair of vectors from different residual bases
    handed to `np.dot` with nothing saying so.
    """
    return conn.execute(
        "SELECT * FROM intervention"
        " WHERE author=? AND model_id=? AND label=? AND version=?",
        (row["author"], row["model_id"], row["label"], row["version"]),
    ).fetchone()


def _report(conn: sqlite3.Connection, intervention_id: str):
    return conn.execute(
        "SELECT * FROM eval_report WHERE intervention_id = ?", (intervention_id,)
    ).fetchone()


def pairwise(conn: sqlite3.Connection, label: str) -> list[dict]:
    """Every unordered pair of claimants on a label.

    Pairs come back in the order the submissions were stored. No ranking is applied
    and none should be: composing these axes into one number is the judgment being
    handed to the reader deliberately.
    """
    subs = _submissions(conn, label)
    pairs = []
    for i, a in enumerate(subs):
        for b in subs[i + 1:]:
            iv_a = _intervention(conn, a)
            iv_b = _intervention(conn, b)

            # One comparability rule, shared with `similarity_matrix`. It used to
            # be two: this loop checked model, revision, layer and hook point,
            # `_angle_between` checked those plus rank and shape, and the site
            # rendered both. A LoRA beside a direction at the same layer was
            # correctly refused by the matrix and reached `np.dot` here, which is
            # the failure `tests/test_similarity_refuses.py` exists to prevent,
            # still live in the other code path.
            cell = (
                _angle_between(iv_a, iv_b)
                if iv_a is not None and iv_b is not None
                else {"v": None, "why": "no intervention attached", "note": None}
            )
            similarity = cell["v"]
            # Comparable means the geometry is defined, which is a narrower claim
            # than "both are on the same model". A missing artifact is not a
            # statement about the objects, so it stays out of this.
            comparable = cell["why"] in (None, "no artifact attached")

            axes_a, axes_b = _axes(conn, a["author"]), _axes(conn, b["author"])
            rep_a = _report(conn, iv_a["id"]) if iv_a else None
            rep_b = _report(conn, iv_b["id"]) if iv_b else None

            pairs.append({
                "a": _ref(a),
                "b": _ref(b),
                # Geometry only, and meaningless unless both sit on the same model,
                # revision, layer and hook point, and both are vectors of the same
                # length. `angle_why` names which of those failed, because "not
                # comparable" alone reads as missing data when it is usually a
                # statement about what the two objects are.
                "angle_similarity": similarity,
                "angle_comparable": comparable,
                "angle_why": cell["why"],
                # The asymmetry is the informative cell: what one of them thought to
                # check and the other did not.
                "axes_both_checked": sorted(axes_a & axes_b),
                "axes_only_a_checked": sorted(axes_a - axes_b),
                "axes_only_b_checked": sorted(axes_b - axes_a),
                # Absence rendered as itself, on both sides.
                "score_state_a": score_state(rep_a),
                "score_state_b": score_state(rep_b),
                "transfer_a": rep_a["transfer_score"] if rep_a else None,
                "transfer_b": rep_b["transfer_score"] if rep_b else None,
                "is_synthetic": bool(
                    (iv_a and iv_a["is_synthetic"]) or (iv_b and iv_b["is_synthetic"])
                ),
            })
    return pairs


def attacks_against(conn: sqlite3.Connection, intervention_id: str) -> list[sqlite3.Row]:
    """Attacks are evidence the author did not choose, so they are never filtered
    by their disposition. Attacker and author each state theirs and both show."""
    return list(
        conn.execute(
            "SELECT * FROM attack WHERE intervention_id = ?", (intervention_id,)
        )
    )


def similarity_matrix(conn: sqlite3.Connection, label: str) -> dict:
    """Angle between every pair of claimants on a label, as a lookup.

    Shipped to the page so a reader can pick any reference and see the column
    recompute without a round trip. Storage is n^2 floats per label: fine at the
    scale one label reaches, not fine past a few hundred claimants. Revisit
    before that rather than after.

    Nothing is ordered here and nothing is implied. Which reference to measure
    against is the reader's choice, and rows do not reorder when they make it.
    """
    rows = list(conn.execute(
        "SELECT s.author, s.model_id, s.label, s.version, i.artifact_path,"
        " i.model_revision, i.layer, i.hook_point, i.kind, i.shape"
        " FROM submission s JOIN intervention i"
        " ON i.author=s.author AND i.model_id=s.model_id"
        " AND i.label=s.label AND i.version=s.version"
        " WHERE s.label = ?",
        (label,),
    ))
    refs = [_ref(r) for r in rows]
    matrix: dict[str, dict] = {ref: {} for ref in refs}

    for i, a in enumerate(rows):
        for j, b in enumerate(rows):
            matrix[refs[i]][refs[j]] = _angle_between(a, b)
    return matrix


def _rank(shape: str | None) -> int | None:
    """How many axes the stored artifact has.

    `kind` is an open string and not every kind is a vector. A direction, an SAE
    decoder column and a probe weight vector all live in the residual stream and
    can be compared. A LoRA adaptor is a low-rank matrix and a ReFT edit is a
    learned intervention; the angle between either of those and a direction is
    not a small number, it is undefined.
    """
    try:
        dims = json.loads(shape) if shape else None
    except (TypeError, ValueError):
        return None
    return len(dims) if isinstance(dims, list) else None


def _angle_between(a, b) -> dict:
    """The angle between two artifacts, or the reason there isn't one.

    Naming the reason matters: "not comparable" on its own reads as a gap in the
    data, when usually it is a statement about what the two objects are.
    """
    def out(value, why=None, note=None):
        return {"v": value, "why": why, "note": note}

    if not (a["artifact_path"] and b["artifact_path"]):
        return out(None, "no artifact attached")
    if a["model_id"] != b["model_id"] or a["model_revision"] != b["model_revision"]:
        return out(None, "different model or revision")
    if a["layer"] != b["layer"] or a["hook_point"] != b["hook_point"]:
        return out(None, "different layer or hook point")

    rank_a, rank_b = _rank(a["shape"]), _rank(b["shape"])
    if rank_a != 1 or rank_b != 1:
        return out(None, "not a vector")
    if a["shape"] != b["shape"]:
        return out(None, "different dimensions")

    value = angle_similarity(
        load_vector(a["artifact_path"]), load_vector(b["artifact_path"])
    )
    # Both are directions in the same space, so the arithmetic holds, but an SAE
    # decoder column and a probe weight vector are not the same kind of object.
    # What is being compared is what you would steer with, not the artifacts.
    note = (
        f"{a['kind']} against {b['kind']}: comparing what each would steer with"
        if a["kind"] != b["kind"] else None
    )
    return out(value, None, note)
