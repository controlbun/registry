"""One claimant, shaped the way every view of it needs.

This is not a renderer. It was one: the project carried a Jinja frontend in
`web/templates/` alongside the Astro site, and the two drifted, most visibly when
the pairwise "Between claimants" table was replaced with a reader-pointed
similarity column in Astro and left standing in Jinja. Astro is the frontend. The
Jinja templates and the HTML-emitting half of this module are gone.

What survives is the part both callers actually shared: the shape of a claimant.
`export.py` builds the site payload from it and `client.py` builds a `Submission`
from it, so the Python client and the website cannot disagree about what a
submission is.

Every measurement is passed through as None when it was not taken. Nothing here
substitutes a zero, and the absence is carried out to whoever renders it.
"""

from __future__ import annotations

import json
import sqlite3

# The name, not the module: the package exposes a public `compare()` function,
# which shadows the `compare` submodule for anything reaching for it by attribute.
from .comparison import attacks_against, score_state


def claimant_view(conn: sqlite3.Connection, row: sqlite3.Row) -> dict:
    """One claimant as the page needs it.

    Every measurement is passed through as None when it was not taken. Nothing here
    substitutes a zero, and every view renders absence as its own state.
    """
    iv = conn.execute(
        "SELECT * FROM intervention WHERE author=? AND label=? AND version=?",
        (row["author"], row["label"], row["version"]),
    ).fetchone()
    # An eval whose suite belongs to someone other than the submission's author is
    # the thing this registry is actually for. Pointing your evaluation at someone
    # else's submission is how comparability accumulates without anyone mandating a
    # canonical eval per label, so the two are kept apart rather than averaged.
    reports = list(conn.execute(
        "SELECT r.*, s.author AS evaluator, s.name AS suite_name,"
        " s.version AS suite_version, s.judge_model, s.judge_revision"
        " FROM eval_report r JOIN eval_suite s ON s.id = r.eval_suite_id"
        " WHERE r.intervention_id = ?",
        (iv["id"],),
    )) if iv else []

    report = next((r for r in reports if r["evaluator"] == row["author"]), None)
    verifications = [
        {
            "evaluator": r["evaluator"],
            "suite": f"{r['suite_name']}@{r['suite_version']}",
            "judge_model": r["judge_model"],
            "judge_revision": r["judge_revision"],
            "reported_at": r["reported_at"],
            "trait_score": r["trait_score"],
            "coherence_score": r["coherence_score"],
            "transfer_score": r["transfer_score"],
            "score_state": score_state(r),
        }
        for r in reports
        if r["evaluator"] != row["author"]
    ]
    axes: list[str] = []
    for r in conn.execute(
        "SELECT confound_axes_json FROM eval_suite WHERE author=?", (row["author"],)
    ):
        if r["confound_axes_json"]:
            axes.extend(json.loads(r["confound_axes_json"]))

    # Optional by design. A published vector whose procedure was never written down
    # is still a submission, and its absence renders as absence rather than as a
    # gap to apologize for.
    rec = conn.execute(
        "SELECT * FROM recipe WHERE author=? AND label=? AND version=?",
        (row["author"], row["label"], row["version"]),
    ).fetchone()
    recipe = None
    if rec is not None:
        recipe = {
            "profile": rec["profile"],
            "payload": json.loads(rec["payload_json"]) if rec["payload_json"] else {},
            "entrypoint_library": rec["entrypoint_library"],
            "entrypoint_version": rec["entrypoint_version"],
            "container_digest": rec["container_digest"],
            "theory": rec["theory"],
        }

    # Applied use, not evaluation. The only evidence here that tests the
    # application contract rather than the artifact.
    support = [
        {
            "reporter": r["reporter"],
            "reported_at": r["reported_at"],
            "repo": r["repo"],
            "repo_commit": r["repo_commit"],
            "purpose": r["purpose"],
            "expected": r["expected"],
            "observed": r["observed"],
            "predictability": r["predictability"],
            "deviations": r["deviations"],
            "author_response": r["author_response"],
        }
        for r in conn.execute(
            "SELECT * FROM support_card WHERE author=? AND label=? AND version=?",
            (row["author"], row["label"], row["version"]),
        )
    ]

    return {
        "support": support,
        "verifications": verifications,
        "recipe": recipe,
        "shape": iv["shape"] if iv else None,
        "dtype": iv["dtype"] if iv else None,
        "l2_norm": iv["l2_norm"] if iv else None,
        "activation_norm": iv["activation_norm"] if iv else None,
        "coeff_low": iv["coeff_low"] if iv else None,
        "coeff_high": iv["coeff_high"] if iv else None,
        "steering_position": iv["steering_position"] if iv else None,
        "license_status": iv["license_status"] if iv else None,
        "chat_template_hash": iv["chat_template_hash"] if iv else None,
        "artifact_path": iv["artifact_path"] if iv else None,
        "author": row["author"],
        "label": row["label"],
        "version": row["version"],
        "definition": row["definition"],
        "created_at": row["created_at"],
        "score_state": score_state(report),
        "trait_score": report["trait_score"] if report else None,
        "coherence_score": report["coherence_score"] if report else None,
        "transfer_score": report["transfer_score"] if report else None,
        # Absent for most artifacts, which is the normal case: a single score at
        # one coefficient is what most people report. The page has to say so
        # rather than draw an empty axis.
        "coeff_curve": (
            json.loads(report["coeff_curve_json"])
            if report and report["coeff_curve_json"] else None
        ),
        "confounds": (
            json.loads(report["confound_json"])
            if report and report["confound_json"] else None
        ),
        # What the author wants said about their own numbers. Carried because a
        # battery can report a real measurement of the wrong thing, and the only
        # place that can be said is beside it.
        "notes": report["notes"] if report else None,
        "kind": iv["kind"] if iv else None,
        "model_id": iv["model_id"] if iv else None,
        # Truncated for display, and None when nobody recorded which revision
        # the activations were read from. See schema/migrations/005.
        "model_revision": (iv["model_revision"] or "")[:12] or None if iv else None,
        "layer": iv["layer"] if iv else None,
        "layer_convention": iv["layer_convention"] if iv else None,
        "hook_point": iv["hook_point"] if iv else None,
        "axes": sorted(set(axes)),
        "attacks": attacks_against(conn, iv["id"]) if iv else [],
        "is_synthetic": bool(row["is_synthetic"]),
    }
