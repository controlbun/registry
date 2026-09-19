"""Export the corpus as JSON for the frontend to render.

The frontend is a view and nothing more. Every decision the invariants bind to is
made here, in Python, where it is already tested: which ordering applies, whether
a score is reportable or uninterpretable or simply absent, and what each pair of
claimants does and does not share. A template that receives `score_state` cannot
accidentally print a bare number, because it never receives the number.

    .venv/bin/python -m controlbun.export --db registry.db
"""

from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path

from . import db, order, ref, views
from .comparison import pairwise, similarity_matrix

ROOT = Path(__file__).resolve().parents[2]


def marker(flags) -> str:
    """What a page showing these rows should say about fabricated figures.

    `all` when every row is a fixture, `mixed` when some are, `none` when none
    are and the page therefore carries no marker at all. Computed here rather
    than in a template because getting it wrong in one direction prints a real
    measurement under a banner calling it invented, and in the other prints a
    fabricated one with nothing saying so.

    An empty page is `none`: there is nothing on it to mislabel.
    """
    flags = list(flags)
    if not flags:
        return "none"
    if all(flags):
        return "all"
    return "mixed" if any(flags) else "none"


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
                "synthetic": marker(c["is_synthetic"] for c in cs),
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
                    "ref": c["ref"],
                    "created_at": c["created_at"],
                    "kind": c["kind"],
                    "model_id": c["model_id"],
                }
                for b in blocks for c in b["claimants"]
            ],
            # Recorded revisions first, then the unrecorded ones. Not filtered:
            # the page distinguishes "nobody recorded a revision for this model"
            # from "one claimant recorded one and another did not", and dropping
            # the None loses the second reading. Sorting the raw set raised
            # TypeError the moment a model held both, which is the state
            # migration 005 exists to allow.
            "revisions": sorted(m["revisions"], key=lambda r: (r is None, r or "")),
            "kinds": sorted(m["kinds"]),
            "hook_points": sorted(m["hook_points"]),
            "layers": sorted(m["layers"]),
            "label_count": len(blocks),
            "claimant_count": m["claimant_count"],
            "synthetic": marker(
                c["is_synthetic"] for b in blocks for c in b["claimants"]
            ),
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
            "target": ref.format(
                r["author"], r["model_id"], r["label"], r["version"]
            ),
            "author": r["author"],
            "model_id": r["model_id"],
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
    def owner(name: str) -> dict:
        return owners.setdefault(name, {
            "owner": name,
            "submissions": [],
            "suites": [],
            "evaluations": [],
            "attacks_made": [],
            "support_given": [],
            "models": set(),
            "kinds": set(),
            "labels": set(),
            "attacks_received": 0,
        })

    owners: dict[str, dict] = {}
    for entry in labels:
        for c in entry["claimants"]:
            o = owner(c["author"])
            o["submissions"].append({
                "label": c["label"],
                "version": c["version"],
                "ref": c["ref"],
                "created_at": c["created_at"],
                "kind": c["kind"],
                "model_id": c["model_id"],
                "score_state": c["score_state"],
                "has_recipe": c["recipe"] is not None,
                "attacks": len(c["attacks"]),
                "is_synthetic": c["is_synthetic"],
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

    # Everyone who took part, not only everyone who published. An eval-suite
    # author, an attacker and a support-card reporter are all linked by name from
    # the pages their work appears on, and until now none of them had a page to
    # link to: an owner existed because they shipped an artifact.
    #
    # That is backwards for this registry specifically. The evidence layer is the
    # differentiator, and it is written by people pointing their suites at other
    # people's submissions. A reader weighing an attack cannot weigh the attacker
    # if the attacker has no page, which quietly makes scrutiny second-class next
    # to publication.
    #
    # This is not an account system and does not pretend to be one. A person here
    # is still derived from what they did, and nobody has a page until they do
    # something. Real profiles arrive with the upload path.
    for r in conn.execute(
        "SELECT author, id, name, version, judge_model, judge_revision,"
        " confound_axes_json FROM eval_suite"
    ):
        owner(r["author"])["suites"].append({
            "id": r["id"],
            "suite": f"{r['name']}@{r['version']}",
            "judge_model": r["judge_model"],
            "judge_revision": (r["judge_revision"] or "")[:12],
            "axes": (
                json.loads(r["confound_axes_json"])
                if r["confound_axes_json"] else []
            ),
        })

    # An evaluation of somebody else's submission. An author's runs against their
    # own work are already on their submission rows, and repeating them here would
    # count self-measurement as scrutiny.
    for r in conn.execute(
        "SELECT s.author AS evaluator, r.reported_at, i.author AS subject_author,"
        " i.label, i.version, i.model_id, i.is_synthetic FROM eval_report r"
        " JOIN eval_suite s ON s.id = r.eval_suite_id"
        " JOIN intervention i ON i.id = r.intervention_id"
        " WHERE s.author != i.author"
    ):
        owner(r["evaluator"])["evaluations"].append({
            "subject": ref.format(
                r["subject_author"], r["model_id"], r["label"], r["version"]
            ),
            "subject_author": r["subject_author"],
            "label": r["label"],
            "version": r["version"],
            "model_id": r["model_id"],
            "subject_synthetic": bool(r["is_synthetic"]),
            "reported_at": r["reported_at"],
        })

    for r in conn.execute(
        "SELECT a.attacker, a.attacked_at, a.method, a.attacker_disposition,"
        " i.author AS subject_author, i.label, i.version, i.model_id,"
        " i.is_synthetic FROM attack a"
        " JOIN intervention i ON i.id = a.intervention_id"
    ):
        owner(r["attacker"])["attacks_made"].append({
            "subject": ref.format(
                r["subject_author"], r["model_id"], r["label"], r["version"]
            ),
            "subject_author": r["subject_author"],
            "label": r["label"],
            "version": r["version"],
            "model_id": r["model_id"],
            "subject_synthetic": bool(r["is_synthetic"]),
            "attacked_at": r["attacked_at"],
            "method": r["method"],
            "disposition": r["attacker_disposition"],
        })

    # `model_id` off the card and not off the artifact since
    # `schema/migrations/010`: the card names which submission it is about, and
    # the join is a left join precisely because the artifact row may not be
    # there. Reading the model through the join would have rendered a card about
    # a submission with no artifact as a card about no model.
    for r in conn.execute(
        "SELECT c.*, i.is_synthetic AS subject_synthetic"
        " FROM support_card c"
        " LEFT JOIN intervention i"
        " ON i.author = c.author AND i.model_id = c.model_id"
        " AND i.label = c.label AND i.version = c.version"
    ):
        owner(r["reporter"])["support_given"].append({
            "subject": ref.format(
                r["author"], r["model_id"], r["label"], r["version"]
            ),
            "subject_author": r["author"],
            "label": r["label"],
            "version": r["version"],
            "model_id": r["model_id"],
            "subject_synthetic": bool(r["subject_synthetic"]),
            "reported_at": r["reported_at"],
            "purpose": r["purpose"],
            "predictability": r["predictability"],
        })

    # A namespace whose only record here is a claim still gets a page, for the
    # same reason an attacker who has published nothing does: the page is where
    # the claim and its evidence are readable, and a claim nobody can read is
    # not contestable. Called after every other producer, so a namespace that
    # already has one keeps its place and the ordering below is untouched.
    for r in conn.execute("SELECT DISTINCT namespace FROM namespace_claim"):
        owner(r["namespace"])

    def owner_entry(o: dict) -> dict:
        # Every date this person put on anything, so the ordering key covers
        # attacking and evaluating as well as publishing. Reading it off the
        # submissions alone would sort a prolific attacker as though they had
        # never done anything.
        #
        # **`claimed_at` is deliberately not in here.** It is a date and it
        # would fit, and including it would make the recency ordering derive
        # partly from whether a namespace is claimed: a claimed one would sort
        # above an unclaimed one that published on the same day, with nothing on
        # screen saying why. Every ordering key in this file is something
        # somebody did to the work. A claim is not.
        dates = (
            [s["created_at"] for s in o["submissions"]]
            + [e["reported_at"] for e in o["evaluations"]]
            + [a["attacked_at"] for a in o["attacks_made"]]
            + [c["reported_at"] for c in o["support_given"]]
        )
        # Who has bound an account to this namespace, and on what dated
        # evidence. Empty for every namespace in this corpus, which is the
        # ordinary state rather than a gap: see schema/migrations/009. A list
        # and not a flag, because a flag is what a table sorts on.
        claims = views.namespace_view(conn, o["owner"])["claims"]
        return {
            "owner": o["owner"],
            "claims": claims,
            "submissions": sorted(
                o["submissions"], key=lambda s: s["created_at"], reverse=True
            ),
            "suites": sorted(o["suites"], key=lambda x: x["suite"]),
            "evaluations": sorted(
                o["evaluations"], key=lambda x: x["reported_at"], reverse=True
            ),
            "attacks_made": sorted(
                o["attacks_made"], key=lambda x: x["attacked_at"], reverse=True
            ),
            "support_given": sorted(
                o["support_given"], key=lambda x: x["reported_at"], reverse=True
            ),
            "models": sorted(o["models"]),
            "kinds": sorted(o["kinds"]),
            "labels": sorted(o["labels"]),
            "attacks_received": o["attacks_received"],
            # An eval suite carries no date in the schema, so somebody who has
            # only authored one and never run it has nothing to sort on. None
            # rather than a stand-in date: the page says so instead of implying
            # they were here today.
            "latest": max(dates) if dates else None,
            # Scrutiny received, which is a property of having published
            # something. Nobody is ordered up the page for attacking a lot.
            "engagement": sum(s["engagement"] for s in o["submissions"]),
            # Their own rows plus the rows their work points at. Somebody who has
            # published nothing and only attacked fixtures still has a page full
            # of fabricated subjects, and it has to say so.
            #
            # Claims are in the tally because a fixture claim names a fixture
            # account, and a namespace whose only record here is one would
            # otherwise render an invented identity with no marker on the page.
            "synthetic": marker(
                [s["is_synthetic"] for s in o["submissions"]]
                + [x["subject_synthetic"] for x in o["evaluations"]]
                + [x["subject_synthetic"] for x in o["attacks_made"]]
                + [x["subject_synthetic"] for x in o["support_given"]]
                + [x["is_synthetic"] for x in claims]
            ),
        }

    owner_index = [owner_entry(o) for o in owners.values()]

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
        # Who published something that is not a fixture. The synthetic marker used
        # to be one flag for the whole corpus, which was true while the corpus was
        # entirely fabricated and became a lie the moment it was not: a real
        # measurement rendered under a banner saying every figure on the page is
        # invented. The flag is per row in the schema and always was. This is what
        # the page needs to name the exception rather than flatten it.
        "real_authors": sorted({
            c["author"] for l in labels for c in l["claimants"]
            if not c["is_synthetic"]
        }),
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
        "--out", default=str(ROOT / "astro" / "src" / "data" / "controlbun.json")
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
    print(f"  claims     {sum(len(o['claims']) for o in payload['owner_index'])}")
    print(f"  relations  {len(payload['relations'])}")
    print(f"  labels     {len(payload['labels'])}")
    print(f"  claimants  {payload['corpus']['size']}")
    print(f"  ordering   {payload['corpus']['active_order']}")


if __name__ == "__main__":
    main()
