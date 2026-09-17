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

from registry import artifact, db  # noqa: E402
from registry.artifact import sort_header  # noqa: E402

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
    sort_header(path)
    return path


def confirmed_facts(path: Path) -> artifact.Facts:
    """Everything the row records about the tensor, checked against the tensor.

    This used to be `digest()`, returning one sha256 while the three tensor
    facts beside it in the same `INSERT` were typed out as `f"[{DIM}]"`,
    `"float32"` and `1.0`. They were right. The mechanism was that they were
    typed by somebody who knew, and that mechanism has no failure mode short of
    being wrong and staying wrong, because every later check reads the row.

    **What the claim is here, since nobody cited it from anywhere.** It is what
    `write_vector` twelve lines up promises: a float32 array of length `DIM`,
    divided by its own norm. Claiming it and checking it turns that promise into
    something that can fail, so a `write_vector` that stopped normalizing, or a
    `DIM` that stopped matching the ramp, is a build that refuses rather than a
    corpus that quietly describes itself wrong.

    **The digest half stays as honest as it was.** For a file this same script
    wrote four lines earlier the digest cannot disagree with the bytes, so
    nothing is established by recording it. Its value is downstream: the client
    compares bytes that arrived from somewhere else against it and the falsifier
    recomputes it from the committed file every run. `artifacts/seed.py` records
    the same column against a second, independent record of the same bytes,
    which is the version that can fail.

    None of these is a fabricated number. Each is derived from, or checked
    against, the fixture bytes, so all of them change when those do.
    """
    return artifact.confirmed(
        path.read_bytes(),
        artifact.Claim(shape=f"[{DIM}]", dtype="float32", l2_norm=1.0),
        subject=str(path.relative_to(ROOT)),
    )


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
        "fern": write_vector("fern_refusal_v1", (ramp % 4) + 1, meta(MODEL_B)),
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
         "labeled transcripts instead of selecting a latent. Dana's latent looks to "
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

    ex(
        "INSERT INTO submission (author,label,version,definition,created_at,is_synthetic)"
        " VALUES (?,?,?,?,?,1)",
        ("fern", "refusal", "v1",
         "Refusal is a dictionary feature, not a direction I constructed. I am not "
         "claiming to have found it; I am claiming this particular latent in this "
         "particular SAE fires on declination, and here is which one so you can "
         "check me.",
         "2026-09-12T00:00:00Z"),
    )

    # kind is an open string and the corpus says so: four artifacts, three kinds,
    # two models, two labels. Nothing about the schema is direction-only.
    spec = {
        "alice": ("kindness", "direction", MODEL_A),
        "bob":   ("kindness", "direction", MODEL_A),
        "dana":  ("refusal",  "sae-latent", MODEL_B),
        "erik":  ("refusal",  "probe", MODEL_B),
        "fern":  ("refusal",  "sae-latent", MODEL_B),
    }
    for author, path in vectors.items():
        label, kind, (mid, rev, layer, hook) = spec[author]
        # Four tensor facts out of one call, all four checked against the bytes
        # the row points at. `activation_norm` and the coefficient range are not
        # in there and cannot be: they are synthetic repeated-digit stand-ins for
        # something a model would have to be run to measure, and there is nothing
        # in the file to check them against. The line between the two is whether
        # the artifact itself can answer.
        facts = confirmed_facts(path)
        ex(
            "INSERT INTO intervention (id,author,label,version,kind,model_id,"
            "model_revision,layer,layer_convention,hook_point,shape,dtype,"
            "l2_norm,activation_norm,coeff_low,coeff_high,steering_position,"
            "license_status,chat_template_hash,artifact_path,artifact_sha256,"
            "is_synthetic)"
            " VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,1)",
            (f"iv_{author}", author, label, "v1", kind, mid, rev, layer,
             "block-0indexed", hook, facts.shape, facts.dtype,
             facts.l2_norm, 11.1111, 0.5, 1.5, "all-positions",
             "unresolved", "sha256:" + "e" * 8, f"fixtures/{path.name}",
             facts.sha256),
        )

    # The same kind as dana's, with the provenance dana's lacks. A latent is only
    # identified by its dictionary and its index, so this is the difference between
    # a checkable claim and a bare vector asserting where it came from.
    ex(
        "INSERT INTO recipe (id,author,label,version,profile,payload_json,"
        "entrypoint_library,entrypoint_version,container_digest,theory)"
        " VALUES (?,?,?,?,?,?,?,?,?,?)",
        ("rc_fern", "fern", "refusal", "v1", "neuronpedia/sae-latent-v1",
         json.dumps({
             "sae_repo": "placeholder/other-architecture-7b-saes",
             "sae_revision": "2" * 40,
             "latent_index": 41827,
             "hook": "blocks.12.hook_resid_pre",
             "selection_criterion": "max activation on held-out declinations",
         }),
         "sae-lens", "0.0.0-SYNTHETIC", "sha256:" + "3" * 64,
         "Selecting a latent is a weaker claim than building a direction: I did not "
         "decide what refusal is, I found something in someone else's dictionary "
         "that fires on it. If the latent turns out to be polysemantic, that is a "
         "fact about the SAE and not about my reading of the word."),
    )

    # Recipes. Optional by design, and dana deliberately has none: a published
    # artifact whose procedure was never written down is still a submission, and
    # the page has to render that absence rather than hide it.
    #
    # `profile` is namespaced and versioned, never chosen from a list, because
    # there is no list. Whoever invents the seventh way of making a direction
    # publishes their own profile without asking anyone.
    ex(
        "INSERT INTO recipe (id,author,label,version,profile,payload_json,"
        "entrypoint_library,entrypoint_version,container_digest,theory)"
        " VALUES (?,?,?,?,?,?,?,?,?,?)",
        ("rc_alice", "alice", "kindness", "v1", "soham/contrastive-v1",
         json.dumps({
             "contrast_source": "uploaded dataset, 135 length-matched pairs",
             "method": "diffmean",
             "token_masking": "last-token",
             "layer_sweep": "all blocks",
             "selection_criterion": "probe margin against a label-shuffled null",
         }),
         "steering-vectors", "0.0.0-SYNTHETIC", "sha256:" + "0" * 64,
         "I take affective tone to be the trait itself rather than a proxy for it, "
         "so I did not orthogonalize against sentiment. A reader who thinks warmth "
         "is a confound on kindness should expect this direction to move both, and "
         "should prefer bob's."),
    )
    ex(
        "INSERT INTO recipe (id,author,label,version,profile,payload_json,"
        "entrypoint_library,entrypoint_version,container_digest,theory)"
        " VALUES (?,?,?,?,?,?,?,?,?,?)",
        ("rc_bob", "bob", "kindness", "v1", "soham/contrastive-v1",
         json.dumps({
             "contrast_source": "generator prompt + generator model + seed",
             "method": "caa",
             "token_masking": "response-only",
             "layer_sweep": "blocks 0-15",
             "selection_criterion": "held-out separation",
         }),
         "steering-vectors", "0.0.0-SYNTHETIC", "sha256:" + "1" * 64,
         "Warmth without cost is politeness. I orthogonalized against sentiment "
         "and formality so that what is left is the willingness to give something "
         "up, which is what I mean by the word."),
    )
    ex(
        "INSERT INTO recipe (id,author,label,version,profile,payload_json,"
        "entrypoint_library,entrypoint_version,container_digest,theory)"
        " VALUES (?,?,?,?,?,?,?,?,?,?)",
        ("rc_erik", "erik", "refusal", "v1", "erik/linear-probe-v2",
         json.dumps({
             "training_data": "labeled transcripts, declination vs compliance",
             "method": "logistic probe",
             "regularization": "L2",
             "layer_sweep": "blocks 8-16",
             "selection_criterion": "validation AUC",
         }),
         "scikit-learn", "0.0.0-SYNTHETIC", "sha256:" + "2" * 64,
         "A decision boundary is not a feature. I train on transcripts rather than "
         "selecting a latent, because a latent that fires on declination may be "
         "firing on the topics that provoke it."),
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
        "trait_score,coherence_score,transfer_score,confound_json,coeff_curve_json,"
        "is_synthetic) VALUES (?,?,?,?,?,?,?,?,?,1)",
        ("er_alice", "es_alice", "iv_alice", "2026-09-12T00:00:00Z",
         0.7777, 0.8888, 0.6666,
         json.dumps({"sentiment": 0.5555, "verbosity": 0.1111}),
         # The shape is the claim: the trait keeps climbing after coherence has
         # started to fall, so the headline score at coefficient 1.5 is measured
         # on text that is already coming apart.
         json.dumps([
             {"coefficient": 0.0, "trait": 0.1111, "coherence": 0.9999},
             {"coefficient": 0.5, "trait": 0.4444, "coherence": 0.9999},
             {"coefficient": 1.0, "trait": 0.6666, "coherence": 0.8888},
             {"coefficient": 1.5, "trait": 0.7777, "coherence": 0.5555},
             {"coefficient": 2.0, "trait": 0.8888, "coherence": 0.2222},
         ])),
    )
    ex(
        "INSERT INTO eval_report (id,eval_suite_id,intervention_id,reported_at,"
        "trait_score,coherence_score,confound_json,coeff_curve_json,is_synthetic)"
        " VALUES (?,?,?,?,?,?,?,?,1)",
        ("er_bob", "es_bob", "iv_bob", "2026-09-12T00:00:00Z",
         0.4444, 0.9999,
         json.dumps({"refusal_rate": 0.2222, "formality": 0.3333}),
         json.dumps([
             {"coefficient": 0.0, "trait": 0.1111, "coherence": 0.9999},
             {"coefficient": 0.5, "trait": 0.2222, "coherence": 0.9999},
             {"coefficient": 1.0, "trait": 0.3333, "coherence": 0.9999},
             {"coefficient": 1.5, "trait": 0.4444, "coherence": 0.8888},
             {"coefficient": 2.0, "trait": 0.4444, "coherence": 0.8888},
         ])),
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

    # Someone pointing their own eval at a submission that is not theirs. This is
    # the mechanism that makes scores comparable without anyone mandating a
    # canonical eval per label, and it is a first-class action rather than a
    # favor: carol did not ask alice, and alice cannot withdraw it.
    #
    # Carol gets a lower trait score than alice reported for the same artifact.
    # That disagreement is the content. Neither number is corrected against the
    # other and the registry does not pick.
    ex("INSERT INTO eval_suite (id,author,name,version,judge_model,judge_revision,"
       "confound_axes_json) VALUES (?,?,?,?,?,?,?)",
       ("es_carol", "carol", "warmth-adversarial", "v1",
        "placeholder/judge-8b", "0" * 40, json.dumps(["sentiment", "length"])))
    ex(
        "INSERT INTO eval_report (id,eval_suite_id,intervention_id,reported_at,"
        "trait_score,coherence_score,transfer_score,confound_json,is_synthetic)"
        " VALUES (?,?,?,?,?,?,?,?,1)",
        ("er_carol_on_alice", "es_carol", "iv_alice", "2026-09-12T00:00:00Z",
         0.3333, 0.8888, 0.1111,
         json.dumps({"sentiment": 0.8888, "length": 0.2222})),
    )
    # And a verification that reports a score with no coherence beside it, so the
    # verifications tab has to render the uninterpretable state too.
    ex("INSERT INTO eval_suite (id,author,name,version,judge_model,judge_revision)"
       " VALUES (?,?,?,?,?,?)",
       ("es_erik_x", "erik", "declination-crosscheck", "v1",
        "placeholder/judge-8b", "0" * 40))
    ex(
        "INSERT INTO eval_report (id,eval_suite_id,intervention_id,reported_at,"
        "trait_score,is_synthetic) VALUES (?,?,?,?,?,1)",
        ("er_erik_on_dana", "es_erik_x", "iv_dana", "2026-09-12T00:00:00Z", 0.7777),
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

    # Support cards: applied use, not evaluation. One reports the artifact
    # behaving as documented; one reports it working while the published contract
    # was wrong, which is a defect report about our metadata that no eval could
    # surface.
    ex(
        "INSERT INTO support_card (id,author,label,version,reporter,reported_at,"
        "repo,repo_commit,purpose,expected,observed,predictability,deviations,"
        "author_response,is_synthetic) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,1)",
        ("sc_gus_on_bob", "bob", "kindness", "v1", "gus",
         "2026-09-12T00:00:00Z", "placeholder/support-desk-eval", "a" * 40,
         "Steering a support-desk assistant toward offering concrete help rather "
         "than sympathy.",
         "Per the contract: coefficient 0.5 to 1.5 at layer 4 resid_post, "
         "all-positions, with coherence holding across that range.",
         "Held across the documented range. At 1.5 the assistant offered to do "
         "the task rather than describing it, which is the behavior the label "
         "claims. Coherence did not visibly degrade.",
         "as-documented", None,
         "Matches what I measured. The costly-help reading is exactly the case "
         "this was built for."),
    )
    ex(
        "INSERT INTO support_card (id,author,label,version,reporter,reported_at,"
        "repo,repo_commit,purpose,expected,observed,predictability,deviations,"
        "author_response,is_synthetic) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,1)",
        ("sc_hana_on_alice", "alice", "kindness", "v1", "hana",
         "2026-09-12T00:00:00Z", "placeholder/tone-experiments", "b" * 40,
         "Warming the tone of generated release notes.",
         "Per the contract: layer 4, resid_post, block-0indexed, coefficient 0.5 "
         "to 1.5.",
         "Worked, but only after correcting the hook. Applying at resid_post as "
         "documented moved nothing; the effect appears at resid_pre. Once moved, "
         "behavior matched the claim up to about 1.0.",
         "partial",
         "The published hook_point does not reproduce the author's result. Either "
         "the artifact was extracted at resid_pre and recorded as resid_post, or "
         "the convention differs from the one I assumed. Nothing on the page "
         "disambiguates it.",
         "Checking my extraction script. If the hook is wrong in the metadata "
         "that is my error and I will publish a v2 rather than edit v1."),
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
