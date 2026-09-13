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
from pathlib import Path

import numpy as np
from safetensors.numpy import load_file

ROOT = Path(__file__).resolve().parents[2]

# A trait score with no coherence measure beside it is not a small effect, it is a
# broken instrument. Judge-human agreement ran 81% where text held together and 42%
# where it degenerated, and one arm inverted sign outright.
SCORE_ABSENT = "absent"
SCORE_UNINTERPRETABLE = "uninterpretable"
SCORE_REPORTABLE = "reportable"


def load_vector(artifact_path: str) -> np.ndarray:
    tensors = load_file(str(ROOT / artifact_path))
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
            "SELECT author, label, version FROM submission WHERE label = ?", (label,)
        )
    )


def _intervention(conn: sqlite3.Connection, author: str, label: str, version: str):
    return conn.execute(
        "SELECT * FROM intervention WHERE author=? AND label=? AND version=?",
        (author, label, version),
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
            iv_a = _intervention(conn, a["author"], a["label"], a["version"])
            iv_b = _intervention(conn, b["author"], b["label"], b["version"])

            similarity = None
            comparable = (
                iv_a is not None
                and iv_b is not None
                and iv_a["model_id"] == iv_b["model_id"]
                and iv_a["model_revision"] == iv_b["model_revision"]
                and iv_a["layer"] == iv_b["layer"]
                and iv_a["hook_point"] == iv_b["hook_point"]
            )
            if comparable and iv_a["artifact_path"] and iv_b["artifact_path"]:
                similarity = angle_similarity(
                    load_vector(iv_a["artifact_path"]),
                    load_vector(iv_b["artifact_path"]),
                )

            axes_a, axes_b = _axes(conn, a["author"]), _axes(conn, b["author"])
            rep_a = _report(conn, iv_a["id"]) if iv_a else None
            rep_b = _report(conn, iv_b["id"]) if iv_b else None

            pairs.append({
                "a": f"{a['author']}/{a['label']}@{a['version']}",
                "b": f"{b['author']}/{b['label']}@{b['version']}",
                # Geometry only, and meaningless unless both sit on the same model,
                # revision, layer and hook point.
                "angle_similarity": similarity,
                "angle_comparable": comparable,
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
