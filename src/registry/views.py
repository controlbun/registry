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

from . import fetch

# The name, not the module: the package exposes a public `compare()` function,
# which shadows the `compare` submodule for anything reaching for it by attribute.
from .comparison import attacks_against, score_state


def published_at(iv: sqlite3.Row | None) -> dict | None:
    """Where the author published these bytes, as something a reader can click.

    **None is the ordinary answer and does not mean anything is wrong.** Nine of
    the ten rows in this corpus record no repo: five are synthetic fixtures and
    four are real directions whose author never published them anywhere with a
    URL. Both are true statements about a row rather than gaps, and neither is
    a lesser state than the tenth. Nothing here invents a URL for a row that
    has none, and nothing orders on whether this came back None.

    The URL is built by `registry.fetch.row_url` and not here, and not in a
    template. That function owns the rule that turns host, repo, commit, path
    and template into a URL, including the refusals: a template that drops the
    commit is not a pin, a scheme that is not a network fetch cannot be checked
    by anybody else, and a placeholder carrying a format spec is doing
    something other than building a URL. A second copy of any of that beside
    the page would be a second chance to get it wrong, quietly, in the half
    nobody runs the fetch tests against.

    `refusal` carries the sentence `row_url` refused with, for the row whose
    pin does not resolve. Written out rather than raised, because a single bad
    template in one row should render as that row saying so, not as a build
    that does not finish and a corpus nobody can see.
    """
    if iv is None or not (iv["artifact_repo"] and iv["artifact_commit"]):
        return None

    url: str | None = None
    refusal: str | None = None
    try:
        url = fetch.row_url(
            repo=iv["artifact_repo"],
            commit=iv["artifact_commit"],
            path=iv["artifact_path"] or "",
            host=iv["artifact_host"],
            url_template=iv["artifact_url_template"],
        )
    except fetch.FetchError as unresolvable:
        refusal = str(unresolvable)

    return {
        "repo": iv["artifact_repo"],
        "commit": iv["artifact_commit"],
        "path": iv["artifact_path"],
        # As recorded, never filled in. A row from before
        # `schema/migrations/007` records neither and resolves against the
        # client's own default; writing that default in here would read as a
        # fact somebody checked, which is the mistake 005 and 007 both name.
        "host": iv["artifact_host"],
        "url_template": iv["artifact_url_template"],
        "url": url,
        "refusal": refusal,
    }


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
    # Which axes were checked on this artifact.
    #
    # **A suite declares a battery; a report says what was actually run.** So
    # the axes read off the results, not off the suite: an axis is checked for
    # this artifact when this artifact's own report carries a number for it.
    #
    # Two ways the old query was wrong and the second survived the first fix.
    # It selected on `author` alone, so every submission by an author borrowed
    # the axes of every suite that author had ever written, and a real
    # submission with no confound data rendered four axes lifted from the same
    # author's unrelated work on another label and another model. Joining
    # through `eval_report` fixed that and left this: `soham/pro-human@L24` has
    # a report from a suite declaring four axes and a `confound_json` of null,
    # because the arena ran that battery on the layer-32 directions only. The
    # suite's declaration is a statement of intent and reading it as a result
    # is the same fabrication one step further in.
    #
    # An author's own name is the last join anybody thinks to distrust, and a
    # page claiming a measurement nobody took is the one failure this project
    # cannot absorb.
    #
    # **The author filter is the third correction and it is not the first one
    # in reverse.** `BRIEF.md` says the informative cell is the asymmetry in
    # which axes *each author checked*, so somebody else's independent report
    # on this artifact is not this author's diligence and does not belong in
    # this list. Carol measuring `length` on alice's vector is a real
    # measurement, it belongs on the page, and it belongs under carol's name in
    # `verifications` where it already is. Counting it here would say alice
    # checked an axis she did not, which is the same sentence as the bug above
    # with a friendlier cause.
    axes: list[str] = []
    if iv:
        for r in conn.execute(
            "SELECT e.confound_json FROM eval_report e"
            " JOIN eval_suite s ON s.id = e.eval_suite_id"
            " WHERE e.intervention_id = ? AND s.author = ?",
            (iv["id"], row["author"]),
        ):
            if r["confound_json"]:
                axes.extend(json.loads(r["confound_json"]))

    # Why a field has no value, in the words of whoever looked for it. Keyed by
    # the column it is about, an open string with nothing enumerating which
    # names it may take: see `schema/migrations/008`.
    #
    # Empty for almost every row and that is not a lesser state. No reason
    # recorded renders exactly as it rendered before 008 existed, which is the
    # field saying absent and saying nothing else. What this carries is the
    # other case: an absence somebody looked for and accounted for, which is
    # the difference between a cell a reader can act on and an empty one.
    absences = {
        r["field"]: r["reason"]
        for r in conn.execute(
            "SELECT field, reason FROM intervention_absence"
            " WHERE intervention_id = ? ORDER BY field",
            (iv["id"],),
        )
    } if iv else {}

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
        # Authored prose. It renders inside a `data-authored` region for the
        # reason the 2026-09-19 decision gives: a reason carries file names,
        # line numbers and sometimes figures, and the falsifier reads every
        # number outside a marked region as one this registry asserts.
        "absences": absences,
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
        # The digest of the file as published, which is a fact about the bytes
        # rather than about where they are, so it travels whether or not
        # anything is pinned. `registry.artifact.confirmed` checks bytes that
        # arrive against it; printing it is what lets a reader who fetched the
        # file by hand do the same check without a database.
        "artifact_sha256": iv["artifact_sha256"] if iv else None,
        # The other four columns of the pin, plus the URL they resolve to.
        # None where nobody published these bytes, which is most rows.
        "published": published_at(iv),
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
