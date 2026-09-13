"""Render label views to static HTML.

Static on purpose. v0 serves nothing publicly, and a renderer that writes files
cannot accidentally become a public surface the way a running server can. It also
keeps the output diffable, which makes a regression in what a reader is shown
visible in review rather than only at runtime.

    .venv/bin/python -m registry.render --db registry.db --out site/
"""

from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

# Names, not the module: the package exposes a public `compare()` function, which
# shadows the `compare` submodule for anything that reaches for it by attribute.
from . import db, order
from .comparison import attacks_against, pairwise, score_state

ROOT = Path(__file__).resolve().parents[2]
TEMPLATES = ROOT / "web" / "templates"


def _env() -> Environment:
    return Environment(
        loader=FileSystemLoader(str(TEMPLATES)),
        autoescape=select_autoescape(["html"]),
        undefined=__import__("jinja2").StrictUndefined,
    )


def claimant_view(conn: sqlite3.Connection, row: sqlite3.Row) -> dict:
    """One claimant as the page needs it.

    Every measurement is passed through as None when it was not taken. Nothing here
    substitutes a zero, and the template renders absence as its own state.
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
    # gap to apologise for.
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
        "kind": iv["kind"] if iv else None,
        "model_id": iv["model_id"] if iv else None,
        "model_revision": iv["model_revision"][:12] if iv else None,
        "layer": iv["layer"] if iv else None,
        "layer_convention": iv["layer_convention"] if iv else None,
        "hook_point": iv["hook_point"] if iv else None,
        "axes": sorted(set(axes)),
        "attacks": attacks_against(conn, iv["id"]) if iv else [],
        "is_synthetic": bool(row["is_synthetic"]),
    }


ORDER_LABELS = {
    order.ORDER_RECENT: "Recently added",
    order.ORDER_TRENDING: "Trending",
}


def render_label(
    conn: sqlite3.Connection, label: str, out_dir: Path, order_key: str | None = None
) -> Path:
    rows = order.apply_order(conn, db.claimants(conn, label), key=order_key)
    claimants = [claimant_view(conn, r) for r in rows]
    pairs = pairwise(conn, label)

    active = order_key or order.active_order(conn)
    html = _env().get_template("label.html").render(
        label=label,
        claimants=claimants,
        pairs=pairs,
        any_synthetic=any(c["is_synthetic"] for c in claimants),
        active_order=active,
        active_order_name=ORDER_LABELS.get(active, active),
        order_choices=[(k, v) for k, v in ORDER_LABELS.items()],
        corpus_size=order.corpus_size(conn),
        corpus_threshold=order.CORPUS_THRESHOLD,
    )
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{label}.html"
    path.write_text(html)
    return path


def render_index(conn: sqlite3.Connection, out_dir: Path) -> Path:
    """The registry as a whole.

    Labels in storage order with no ranking. What a reader needs here is the shape
    of the corpus, which is how many people claim each label and across which models
    and artifact kinds, not which label matters most.
    """
    labels = []
    for (label,) in conn.execute("SELECT DISTINCT label FROM submission"):
        rows = list(conn.execute(
            "SELECT i.kind, i.model_id, s.author FROM submission s"
            " LEFT JOIN intervention i"
            " ON i.author=s.author AND i.label=s.label AND i.version=s.version"
            " WHERE s.label = ?", (label,)))
        labels.append({
            "label": label,
            "claimants": len({r["author"] for r in rows}),
            "kinds": sorted({r["kind"] for r in rows if r["kind"]}),
            "models": sorted({r["model_id"] for r in rows if r["model_id"]}),
        })

    active = order.active_order(conn)
    html = _env().get_template("index.html").render(
        active_order=active,
        active_order_name=ORDER_LABELS.get(active, active),
        order_choices=[(k, v) for k, v in ORDER_LABELS.items()],
        corpus_size=order.corpus_size(conn),
        corpus_threshold=order.CORPUS_THRESHOLD,
        labels=labels,
        total_claimants=sum(l["claimants"] for l in labels),
        all_kinds=sorted({k for l in labels for k in l["kinds"]}),
        all_models=sorted({m for l in labels for m in l["models"]}),
    )
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "index.html"
    path.write_text(html)
    return path


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=str(ROOT / "registry.db"))
    ap.add_argument("--out", default=str(ROOT / "site"))
    args = ap.parse_args()

    conn = db.connect(args.db)
    labels = [r[0] for r in conn.execute("SELECT DISTINCT label FROM submission")]
    for label in labels:
        print("wrote", render_label(conn, label, Path(args.out)))
    print("wrote", render_index(conn, Path(args.out)))


if __name__ == "__main__":
    main()
