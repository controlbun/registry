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

from . import compare, db

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
    report = (
        conn.execute(
            "SELECT * FROM eval_report WHERE intervention_id=?", (iv["id"],)
        ).fetchone()
        if iv
        else None
    )
    axes: list[str] = []
    for r in conn.execute(
        "SELECT confound_axes_json FROM eval_suite WHERE author=?", (row["author"],)
    ):
        if r["confound_axes_json"]:
            axes.extend(json.loads(r["confound_axes_json"]))

    return {
        "author": row["author"],
        "label": row["label"],
        "version": row["version"],
        "definition": row["definition"],
        "score_state": compare.score_state(report),
        "trait_score": report["trait_score"] if report else None,
        "coherence_score": report["coherence_score"] if report else None,
        "transfer_score": report["transfer_score"] if report else None,
        "kind": iv["kind"] if iv else None,
        "model_id": iv["model_id"] if iv else None,
        "model_revision": iv["model_revision"][:12] if iv else None,
        "layer": iv["layer"] if iv else None,
        "layer_convention": iv["layer_convention"] if iv else None,
        "hook_point": iv["hook_point"] if iv else None,
        "axes": sorted(set(axes)),
        "attacks": compare.attacks_against(conn, iv["id"]) if iv else [],
        "is_synthetic": bool(row["is_synthetic"]),
    }


def render_label(conn: sqlite3.Connection, label: str, out_dir: Path) -> Path:
    rows = db.claimants(conn, label)
    claimants = [claimant_view(conn, r) for r in rows]
    pairs = compare.pairwise(conn, label)

    html = _env().get_template("label.html").render(
        label=label,
        claimants=claimants,
        pairs=pairs,
        any_synthetic=any(c["is_synthetic"] for c in claimants),
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

    html = _env().get_template("index.html").render(
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
