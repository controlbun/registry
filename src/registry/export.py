"""Export the corpus as JSON for the frontend to render.

The frontend is a view and nothing more. Every decision the invariants bind to is
made here, in Python, where it is already tested: which ordering applies, whether
a score is reportable or uninterpretable or simply absent, and what each pair of
claimants does and does not share. A template that receives `score_state` cannot
accidentally print a bare number, because it never receives the number.

    .venv/bin/python -m registry.export --db registry.db
"""

from __future__ import annotations

import argparse
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from . import compare, db, order, render

ROOT = Path(__file__).resolve().parents[2]


def _attack(row: sqlite3.Row) -> dict:
    return {
        "attacker": row["attacker"],
        "attacked_at": row["attacked_at"],
        "method": row["method"],
        "attacker_disposition": row["attacker_disposition"],
        "author_disposition": row["author_disposition"],
        "author_response": row["author_response"],
    }


def build(conn: sqlite3.Connection) -> dict:
    labels = []

    for (label,) in conn.execute("SELECT DISTINCT label FROM submission"):
        rows = order.apply_order(conn, db.claimants(conn, label))
        claimants = []
        for row in rows:
            view = render.claimant_view(conn, row)
            view["attacks"] = [_attack(a) for a in view["attacks"]]
            claimants.append(view)
        labels.append({
            "label": label,
            "claimants": claimants,
            "pairs": compare.pairwise(conn, label),
        })

    kinds = sorted({c["kind"] for l in labels for c in l["claimants"] if c["kind"]})
    models = sorted({
        c["model_id"] for l in labels for c in l["claimants"] if c["model_id"]
    })
    active = order.active_order(conn)

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "corpus": {
            "size": order.corpus_size(conn),
            "threshold": order.CORPUS_THRESHOLD,
            "active_order": active,
            "active_order_name": render.ORDER_LABELS.get(active, active),
            "order_choices": [
                {"key": k, "name": v} for k, v in render.ORDER_LABELS.items()
            ],
        },
        "any_synthetic": any(
            c["is_synthetic"] for l in labels for c in l["claimants"]
        ),
        "kinds": kinds,
        "models": models,
        "labels": labels,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=str(ROOT / "registry.db"))
    ap.add_argument(
        "--out", default=str(ROOT / "astro" / "src" / "data" / "registry.json")
    )
    args = ap.parse_args()

    payload = build(db.connect(args.db))
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")

    print(f"wrote {out}")
    print(f"  labels     {len(payload['labels'])}")
    print(f"  claimants  {payload['corpus']['size']}")
    print(f"  ordering   {payload['corpus']['active_order']}")


if __name__ == "__main__":
    main()
