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

from . import db, order, render
from .comparison import pairwise

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
            "pairs": pairwise(conn, label),
        })

    # Models are the primary axis. An intervention is a tensor in one model's basis
    # at one layer, so "which model" is the first real question a reader has, and
    # angle similarity is only meaningful inside one. Labels stay browsable one
    # level in, because a label across its claimants is the plurality view itself.
    grouped: dict[str, dict] = {}
    for entry in labels:
        for c in entry["claimants"]:
            if not c["model_id"]:
                continue
            m = grouped.setdefault(c["model_id"], {
                "model_id": c["model_id"],
                "revisions": set(),
                "kinds": set(),
                "hook_points": set(),
                "layers": set(),
                "labels": {},
                "claimant_count": 0,
            })
            m["revisions"].add(c["model_revision"])
            m["kinds"].add(c["kind"])
            m["hook_points"].add(c["hook_point"])
            m["layers"].add(c["layer"])
            m["claimant_count"] += 1
            m["labels"].setdefault(entry["label"], []).append(c)

    model_index = []
    for m in grouped.values():
        blocks = []
        for lab, cs in m["labels"].items():
            here = {c["author"] for c in cs}
            source = next(e for e in labels if e["label"] == lab)
            blocks.append({
                "label": lab,
                "claimants": cs,
                "pairs": [
                    p for p in source["pairs"]
                    if p["a"].split("/")[0] in here and p["b"].split("/")[0] in here
                ],
            })
        model_index.append({
            "model_id": m["model_id"],
            "submissions": [
                {
                    "author": c["author"],
                    "label": c["label"],
                    "version": c["version"],
                    "created_at": c["created_at"],
                    "kind": c["kind"],
                    "model_id": c["model_id"],
                }
                for b in blocks for c in b["claimants"]
            ],
            "revisions": sorted(m["revisions"]),
            "kinds": sorted(m["kinds"]),
            "hook_points": sorted(m["hook_points"]),
            "layers": sorted(m["layers"]),
            "label_count": len(blocks),
            "claimant_count": m["claimant_count"],
            "labels": blocks,
        })

    # Owners. Everything published here is public: a submission nobody can see
    # cannot be attacked, cannot have someone else's eval pointed at it, and cannot
    # appear in a Comparison, so it has none of the properties that make a registry
    # entry evidence rather than a file. There is no visibility field and
    # deliberately so. Dual-use gating, if it ever exists, is registry policy and a
    # different mechanism with a different owner.
    owners: dict[str, dict] = {}
    for entry in labels:
        for c in entry["claimants"]:
            o = owners.setdefault(c["author"], {
                "owner": c["author"],
                "submissions": [],
                "models": set(),
                "kinds": set(),
                "labels": set(),
                "attacks_received": 0,
            })
            o["submissions"].append({
                "label": c["label"],
                "version": c["version"],
                "created_at": c["created_at"],
                "kind": c["kind"],
                "model_id": c["model_id"],
                "score_state": c["score_state"],
                "has_recipe": c["recipe"] is not None,
                "attacks": len(c["attacks"]),
            })
            if c["model_id"]:
                o["models"].add(c["model_id"])
            if c["kind"]:
                o["kinds"].add(c["kind"])
            o["labels"].add(c["label"])
            o["attacks_received"] += len(c["attacks"])

    owner_index = [
        {
            "owner": o["owner"],
            "submissions": sorted(
                o["submissions"], key=lambda s: s["created_at"], reverse=True
            ),
            "models": sorted(o["models"]),
            "kinds": sorted(o["kinds"]),
            "labels": sorted(o["labels"]),
            "attacks_received": o["attacks_received"],
        }
        for o in owners.values()
    ]

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
        "model_index": model_index,
        "owner_index": owner_index,
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
    print(f"  models     {len(payload['model_index'])}")
    print(f"  owners     {len(payload['owner_index'])}")
    print(f"  labels     {len(payload['labels'])}")
    print(f"  claimants  {payload['corpus']['size']}")
    print(f"  ordering   {payload['corpus']['active_order']}")


if __name__ == "__main__":
    main()
