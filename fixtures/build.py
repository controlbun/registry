"""Build the synthetic fixture corpus and seed a database from it.

Read fixtures/SYNTHETIC.md first. Nothing produced here is a measurement. Scores
are repeated-digit decimals and vectors are integer ramps, both chosen so that a
fixture leaking into anything real is obvious on sight rather than plausible.

    .venv/bin/python fixtures/build.py [--db registry.db]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from safetensors.numpy import save_file

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from registry import db  # noqa: E402

HERE = Path(__file__).resolve().parent
DIM = 8
NOTE = "SYNTHETIC FIXTURE. Not a real direction. Not derived from any model."


def write_vector(name: str, values: np.ndarray, meta: dict[str, str]) -> Path:
    """Write a safetensors file whose metadata says what it is, so the marker
    survives the file being copied away from this directory."""
    vec = values / np.linalg.norm(values)
    path = HERE / f"{name}.safetensors"
    save_file(
        {"direction": vec.astype(np.float32)},
        str(path),
        metadata={"synthetic": "true", "note": NOTE, **meta},
    )
    return path


MODEL_A = ("placeholder/does-not-resolve-1b", "0" * 40, 4, "resid_post")
MODEL_B = ("placeholder/other-architecture-7b", "1" * 40, 12, "resid_pre")


def build_vectors() -> dict[str, Path]:
    ramp = np.arange(1, DIM + 1, dtype=np.float32)

    def meta(m):
        mid, rev, layer, hook = m
        return {"model_id": mid, "model_revision": rev, "layer": str(layer),
                "layer_convention": "block-0indexed", "hook_point": hook}

    return {
        "alice": write_vector("alice_kindness_v1", ramp, meta(MODEL_A)),
        "bob": write_vector("bob_kindness_v1", ramp[::-1].copy(), meta(MODEL_A)),
        "dana": write_vector("dana_refusal_v1", (ramp % 3) + 1, meta(MODEL_B)),
        "erik": write_vector("erik_refusal_v1", (ramp % 5) + 1, meta(MODEL_B)),
    }


def seed(conn, vectors: dict[str, Path]) -> None:
    ex = conn.execute

    # Two people claim `kindness` and mean different things by it. This is the
    # content, not a duplication problem.
    ex(
        "INSERT INTO submission (author,label,version,definition,created_at,is_synthetic)"
        " VALUES (?,?,?,?,?,1)",
        ("alice", "kindness", "v1",
         "Kindness is warmth in affect: the model sounds like it cares. I take "
         "affective tone to be the trait itself rather than a proxy for it.",
         "2026-09-12T00:00:00Z"),
    )
    ex(
        "INSERT INTO submission (author,label,version,definition,created_at,is_synthetic)"
        " VALUES (?,?,?,?,?,1)",
        ("bob", "kindness", "v1",
         "Kindness is costly help: the model gives up something to benefit the "
         "user. Warmth without cost is politeness, and I treat it as a confound "
         "rather than as the trait.",
         "2026-09-12T00:00:00Z"),
    )

    # Taxonomy from claims rather than from a committee.
    ex(
        "INSERT INTO label_relation"
        " (from_author,from_label,relation,to_author,to_label,note) VALUES (?,?,?,?,?,?)",
        ("bob", "kindness", "distinguishes-from", "alice", "kindness",
         "Alice's direction reads to me as affect, not as help at a cost."),
    )

    # A second label on a different model, claimed by two more people, with the
    # artifacts being an SAE latent and a probe rather than directions. The registry
    # is not about one trait, one method, or one architecture.
    ex(
        "INSERT INTO submission (author,label,version,definition,created_at,is_synthetic)"
        " VALUES (?,?,?,?,?,1)",
        ("dana", "refusal", "v1",
         "Refusal is the model declining a request it parsed and understood. I read "
         "it off an SAE latent that fires on declination rather than on topic.",
         "2026-09-12T00:00:00Z"),
    )
    ex(
        "INSERT INTO submission (author,label,version,definition,created_at,is_synthetic)"
        " VALUES (?,?,?,?,?,1)",
        ("erik", "refusal", "v1",
         "Refusal is a decision boundary, not a feature, so I train a linear probe on "
         "labelled transcripts instead of selecting a latent. Dana's latent looks to "
         "me like topic sensitivity.",
         "2026-09-12T00:00:00Z"),
    )
    ex(
        "INSERT INTO label_relation"
        " (from_author,from_label,relation,to_author,to_label,note) VALUES (?,?,?,?,?,?)",
        ("erik", "refusal", "distinguishes-from", "dana", "refusal",
         "A latent that fires on declination may be firing on the topics that "
         "provoke it."),
    )

    # kind is an open string and the corpus says so: four artifacts, three kinds,
    # two models, two labels. Nothing about the schema is direction-only.
    spec = {
        "alice": ("kindness", "direction", MODEL_A),
        "bob":   ("kindness", "direction", MODEL_A),
        "dana":  ("refusal",  "sae-latent", MODEL_B),
        "erik":  ("refusal",  "probe", MODEL_B),
    }
    for author, path in vectors.items():
        label, kind, (mid, rev, layer, hook) = spec[author]
        ex(
            "INSERT INTO intervention (id,author,label,version,kind,model_id,"
            "model_revision,layer,layer_convention,hook_point,shape,dtype,"
            "artifact_path,is_synthetic) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,1)",
            (f"iv_{author}", author, label, "v1", kind, mid, rev, layer,
             "block-0indexed", hook, f"[{DIM}]", "float32", f"fixtures/{path.name}"),
        )

    # Different authors checked different axes. The asymmetry is the informative cell.
    ex("INSERT INTO eval_suite (id,author,name,version,confound_axes_json) VALUES (?,?,?,?,?)",
       ("es_alice", "alice", "warmth-holdout", "v1",
        json.dumps(["sentiment", "verbosity"])))
    ex("INSERT INTO eval_suite (id,author,name,version,confound_axes_json) VALUES (?,?,?,?,?)",
       ("es_bob", "bob", "costly-help-holdout", "v1",
        json.dumps(["refusal_rate", "formality"])))

    # Alice measured transfer. Bob did not, and that absence is a state rather than
    # a gap to be filled with a zero.
    ex(
        "INSERT INTO eval_report (id,eval_suite_id,intervention_id,reported_at,"
        "trait_score,coherence_score,transfer_score,confound_json,is_synthetic)"
        " VALUES (?,?,?,?,?,?,?,?,1)",
        ("er_alice", "es_alice", "iv_alice", "2026-09-12T00:00:00Z",
         0.7777, 0.8888, 0.6666,
         json.dumps({"sentiment": 0.5555, "verbosity": 0.1111})),
    )
    ex(
        "INSERT INTO eval_report (id,eval_suite_id,intervention_id,reported_at,"
        "trait_score,coherence_score,confound_json,is_synthetic)"
        " VALUES (?,?,?,?,?,?,?,1)",
        ("er_bob", "es_bob", "iv_bob", "2026-09-12T00:00:00Z",
         0.4444, 0.9999,
         json.dumps({"refusal_rate": 0.2222, "formality": 0.3333})),
    )

    ex("INSERT INTO eval_suite (id,author,name,version,confound_axes_json) VALUES (?,?,?,?,?)",
       ("es_dana", "dana", "declination-holdout", "v1",
        json.dumps(["topic", "verbosity"])))
    ex("INSERT INTO eval_suite (id,author,name,version,confound_axes_json) VALUES (?,?,?,?,?)",
       ("es_erik", "erik", "boundary-probe", "v1", json.dumps(["topic"])))

    ex(
        "INSERT INTO eval_report (id,eval_suite_id,intervention_id,reported_at,"
        "trait_score,coherence_score,transfer_score,confound_json,is_synthetic)"
        " VALUES (?,?,?,?,?,?,?,?,1)",
        ("er_dana", "es_dana", "iv_dana", "2026-09-12T00:00:00Z",
         0.6666, 0.7777, 0.2222, json.dumps({"topic": 0.8888, "verbosity": 0.1111})),
    )
    # Erik reported a trait score with no coherence measure beside it. The page must
    # render that as uninterpretable rather than as a number, and this is the fixture
    # that puts that state on screen instead of only in a test.
    ex(
        "INSERT INTO eval_report (id,eval_suite_id,intervention_id,reported_at,"
        "trait_score,confound_json,is_synthetic) VALUES (?,?,?,?,?,?,1)",
        ("er_erik", "es_erik", "iv_erik", "2026-09-12T00:00:00Z",
         0.5555, json.dumps({"topic": 0.4444})),
    )

    # The strongest evidence is the kind the author did not choose. Attacker and
    # author disagree about what it means, and both dispositions are recorded.
    ex(
        "INSERT INTO attack (id,intervention_id,attacker,attacked_at,method,"
        "result_json,attacker_disposition,author_disposition,author_response,"
        "is_synthetic) VALUES (?,?,?,?,?,?,?,?,?,1)",
        ("at_carol", "iv_alice", "carol", "2026-09-12T00:00:00Z",
         "alternative-confound-axis",
         json.dumps({"sentiment_above_coeff_1_5": 0.9999}),
         "confirmed-limitation", "no-finding",
         "Sentiment moving with the trait is expected under my definition, since I "
         "take affect to be the trait rather than a confound on it."),
    )

    # A consumer freezing one claimant for one purpose, visibly and contestably.
    ex(
        "INSERT INTO pin (id,pinned_by,pinned_at,purpose,author,label,version,"
        "alternatives_json,rationale) VALUES (?,?,?,?,?,?,?,?,?)",
        ("pin_season", "steering-arena", "2026-09-12T00:00:00Z",
         "Season scoring target, frozen so player scores are commensurable",
         "bob", "kindness", "v1",
         json.dumps(["alice/kindness@v1"]),
         "Picked for the costly-help reading because the season's probe set is "
         "about action. Not a claim that it is the better direction."),
    )
    conn.commit()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=str(ROOT / "registry.db"))
    args = ap.parse_args()

    path = Path(args.db)
    if path.exists():
        path.unlink()

    vectors = build_vectors()
    conn = db.connect(path)
    db.migrate(conn)
    seed(conn, vectors)

    counts = {
        t: conn.execute(f"SELECT count(*) FROM {t}").fetchone()[0]
        for t in ("submission", "intervention", "eval_report", "attack", "pin",
                  "label_relation", "eval_suite")
    }
    print(f"seeded {path}")
    for t, n in counts.items():
        print(f"  {t:16} {n}")
    print(f"  vectors written  {len(vectors)}")


if __name__ == "__main__":
    main()
