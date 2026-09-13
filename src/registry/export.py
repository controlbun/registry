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
from pathlib import Path

from . import db, order, views
from .comparison import pairwise, similarity_matrix

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
            view = views.claimant_view(conn, row)
            view["attacks"] = [_attack(a) for a in view["attacks"]]
            claimants.append(view)
        labels.append({
            "label": label,
            "claimants": claimants,
            "pairs": pairwise(conn, label),
            "similarity": similarity_matrix(conn, label),
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
                # Ordering keys, the same two inputs order.py uses. Shipped per row
                # so the reader can switch ordering without a round trip.
                "latest": max(c["created_at"] for c in cs),
                "engagement": sum(
                    len(c["attacks"]) + len(c["verifications"]) for c in cs
                ),
                "pairs": [
                    p for p in source["pairs"]
                    if p["a"].split("/")[0] in here and p["b"].split("/")[0] in here
                ],
            })
        model_index.append({
            "model_id": m["model_id"],
            "latest": max(b["latest"] for b in blocks),
            "engagement": sum(b["engagement"] for b in blocks),
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

    # Pins. A consumer freezing one submission for one purpose so its own numbers
    # stay comparable. That is ordinary experimental control and the opposite of a
    # designation, but only while it stays visible: a pin whose alternatives nobody
    # can see has quietly become the answer rather than a choice.
    pins = [
        {
            "pinned_by": r["pinned_by"],
            "pinned_at": r["pinned_at"],
            "purpose": r["purpose"],
            "target": f"{r['author']}/{r['label']}@{r['version']}",
            "author": r["author"],
            "label": r["label"],
            "version": r["version"],
            "alternatives": json.loads(r["alternatives_json"]),
            "rationale": r["rationale"],
        }
        for r in conn.execute("SELECT * FROM pin")
    ]

    # Relations. Taxonomy from claims rather than from a committee: one author
    # saying what they think their label is or is not, which is a statement another
    # author can disagree with rather than a category anyone is filed under.
    relations = [
        {
            "from_author": r["from_author"],
            "from_label": r["from_label"],
            "relation": r["relation"],
            "to_author": r["to_author"],
            "to_label": r["to_label"],
            "note": r["note"],
        }
        for r in conn.execute("SELECT * FROM label_relation")
    ]

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
                # Same definition as everywhere else: what other people did to it,
                # never what it scored. Kept identical to the model_index sum so
                # the two pages do not order by quietly different quantities.
                "engagement": len(c["attacks"]) + len(c["verifications"]),
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
            # Ordering keys for the owners list, computed over all of someone's
            # submissions rather than read off the first one.
            "latest": max(s["created_at"] for s in o["submissions"]),
            "engagement": sum(s["engagement"] for s in o["submissions"]),
        }
        for o in owners.values()
    ]

    kinds = sorted({c["kind"] for l in labels for c in l["claimants"] if c["kind"]})
    models = sorted({
        c["model_id"] for l in labels for c in l["claimants"] if c["model_id"]
    })
    active = order.active_order(conn)

    return {
        "corpus": {
            "size": order.corpus_size(conn),
            "threshold": order.CORPUS_THRESHOLD,
            "active_order": active,
            "active_order_name": order.ORDER_LABELS.get(active, active),
            "order_choices": [
                {"key": k, "name": v} for k, v in order.ORDER_LABELS.items()
            ],
            # The trending constants travel with the data so the browser can run
            # order.trending_score rather than a second, drifting copy of it. The
            # page says trending is decayed by age; sorting on a raw engagement
            # count would have made that sentence false.
            "gravity": order.GRAVITY,
            "age_offset_hours": order.AGE_OFFSET_HOURS,
        },
        "any_synthetic": any(
            c["is_synthetic"] for l in labels for c in l["claimants"]
        ),
        "kinds": kinds,
        "models": models,
        "pins": pins,
        "relations": relations,
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
    print(f"  pins       {len(payload['pins'])}")
    print(f"  relations  {len(payload['relations'])}")
    print(f"  labels     {len(payload['labels'])}")
    print(f"  claimants  {payload['corpus']['size']}")
    print(f"  ordering   {payload['corpus']['active_order']}")


if __name__ == "__main__":
    main()
