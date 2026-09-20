"""A probe corpus the tests build and the site never sees.

**Nothing here is a measurement, and nothing here reaches the registry.** No row
below is written into `registry.db`, exported to `astro/src/data/`, or rendered
on a page. `make site` does not call this file and cannot: it is in `tests/`, it
writes its tensors into a gitignored directory, and every row it writes carries
`is_synthetic = 1`.

**Why it exists.** Until 2026-09-19 half the corpus was a fabricated fixture set
and the tests were written against it: two people disagreeing about one word, an
author who reported a trait score with no coherence measure beside it, an attack
somebody else made, a support card reporting the published hook was wrong. Those
are states the checks have to be able to see, and the real corpus contains none
of them, because it is five submissions by one author who ran one battery. The
fixtures went because a public site whose corpus is half fabricated invites "is
this real". A test that fabricates its own input and throws it away invites
nothing, so the states moved here rather than disappearing.

What did not move is the narrative. The old fixtures were also demo content,
with theories of kindness and a season pin, because they were on the site. These
are probes and are named like probes.

Two conventions make a leak obvious on sight, kept from `fixtures/SYNTHETIC.md`
because they were the good part of it:

- **Scores are repeated-digit decimals.** `0.1111`, `0.7777`. Real measurements
  do not look like this.
- **Vectors are integer ramps**, normalized. They are not directions in any
  model's residual basis, and the models they name are placeholders that do not
  resolve.

Every `.safetensors` this writes also carries `synthetic: "true"` plus a note in
its embedded metadata, so the marker survives the file being copied away.

    python tests/probe.py --db /tmp/x.db [--root /tmp/tree]

`--root` is what `artifact_path` values resolve against: the tensors land in
`<root>/tests/_probe/` and the rows record `tests/_probe/<name>.safetensors`. It
defaults to the repository, which is what `controlbun.comparison` and the
falsifier resolve against when a test runs in place.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import numpy as np
from safetensors.numpy import save_file

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from controlbun import artifact, db  # noqa: E402
from controlbun.artifact import sort_header  # noqa: E402

DIM = 8
NOTE = "SYNTHETIC PROBE. Not a real direction. Not derived from any model."

# Placeholders, and neither resolves to anything. `does-not-resolve` is in the
# name so a row that escaped into something real would be caught by reading it.
MODEL_A = ("placeholder/does-not-resolve-1b", "0" * 40, 4, "resid_post")
MODEL_B = ("placeholder/other-architecture-7b", "1" * 40, 12, "resid_pre")

LABEL_A = "probe-trait"
LABEL_B = "probe-other"

# Where the tensors go, relative to `root`. Gitignored, written at test time,
# never committed: a checked-in fabricated artifact is the thing that went.
VECTORS = Path("tests") / "_probe"


def vector_dir(root: Path) -> Path:
    return root / VECTORS


def write_vector(root: Path, name: str, values: np.ndarray,
                 meta: dict[str, str]) -> str:
    """One probe tensor, and the `artifact_path` a row should record for it.

    The header is sorted through `controlbun.artifact.sort_header`, the same
    call the real ingest makes, so a probe cannot be exercising a weaker rule
    than the one that ships.
    """
    out = vector_dir(root)
    out.mkdir(parents=True, exist_ok=True)
    vec = values / np.linalg.norm(values)
    path = out / f"{name}.safetensors"
    # Written beside the target and moved into place, because two test
    # processes building the probe at once would otherwise let one of them read
    # a half-written file. The bytes are identical either way, so the move is
    # the only thing that has to be atomic.
    staged = out / f".{name}.{os.getpid()}.staging"
    save_file(
        {"direction": vec.astype(np.float32)},
        str(staged),
        metadata={"synthetic": "true", "note": NOTE, **meta},
    )
    sort_header(staged)
    os.replace(staged, path)
    return str(path.relative_to(root))


def confirmed_facts(root: Path, rel: str) -> artifact.Facts:
    """Everything a row records about the tensor, checked against the tensor.

    Claimed and then confirmed rather than recomputed, which is what the real
    writers do. The claim is what `write_vector` promises four lines up: a
    float32 array of length `DIM` divided by its own norm. None of these is a
    fabricated number; each is derived from, or checked against, the bytes.
    """
    path = root / rel
    return artifact.confirmed(
        path.read_bytes(),
        artifact.Claim(shape=f"[{DIM}]", dtype="float32", l2_norm=1.0),
        subject=rel,
    )


def build_vectors(root: Path) -> dict[str, str]:
    ramp = np.arange(1, DIM + 1, dtype=np.float32)

    def meta(m):
        mid, rev, layer, hook = m
        return {"model_id": mid, "model_revision": rev, "layer": str(layer),
                "layer_convention": "block-0indexed", "hook_point": hook}

    return {
        "probe-a": write_vector(root, "probe_a", ramp, meta(MODEL_A)),
        "probe-b": write_vector(root, "probe_b", ramp[::-1].copy(), meta(MODEL_A)),
        "probe-c": write_vector(root, "probe_c", (ramp % 3) + 1, meta(MODEL_B)),
        "probe-d": write_vector(root, "probe_d", (ramp % 5) + 1, meta(MODEL_B)),
        "probe-e": write_vector(root, "probe_e", (ramp % 4) + 1, meta(MODEL_B)),
    }


def seed(conn, root: Path, vectors: dict[str, str]) -> None:
    ex = conn.execute

    # Two people claim one label and mean different things by it, which is the
    # state the real corpus has never been in and every plurality check needs.
    ex(
        "INSERT INTO submission (author,model_id,label,version,definition,"
        "created_at,is_synthetic) VALUES (?,?,?,?,?,?,1)",
        ("probe-a", MODEL_A[0], LABEL_A, "v1",
         "A probe definition, written by the test suite. This author takes the "
         "trait to be the thing itself rather than a proxy for it, which is the "
         "disagreement the other claimant is here to have.",
         "2026-09-12T00:00:00Z"),
    )
    ex(
        "INSERT INTO submission (author,model_id,label,version,definition,"
        "created_at,is_synthetic) VALUES (?,?,?,?,?,?,1)",
        ("probe-b", MODEL_A[0], LABEL_A, "v1",
         "A probe definition, written by the test suite. This author treats what "
         "the other one calls the trait as a confound on it, and orthogonalized "
         "against it.",
         "2026-09-12T00:00:00Z"),
    )
    ex(
        "INSERT INTO label_relation"
        " (from_author,from_label,relation,to_author,to_label,note)"
        " VALUES (?,?,?,?,?,?)",
        ("probe-b", LABEL_A, "distinguishes-from", "probe-a", LABEL_A,
         "Written by the test suite. One claimant saying how their reading "
         "stands to another's, which is the object under test."),
    )

    # A second label on a second model, three claimants, three kinds. `kind` is
    # an open string and the probe says so where a closed-enum check can see it.
    for author, theory in (
        ("probe-c", "A probe definition, written by the test suite. Read off a "
                    "dictionary latent rather than constructed."),
        ("probe-d", "A probe definition, written by the test suite. Trained as a "
                    "boundary rather than selected as a feature."),
        ("probe-e", "A probe definition, written by the test suite. A latent in "
                    "somebody else's dictionary, identified by index."),
    ):
        ex(
            "INSERT INTO submission (author,model_id,label,version,definition,"
            "created_at,is_synthetic) VALUES (?,?,?,?,?,?,1)",
            (author, MODEL_B[0], LABEL_B, "v1", theory, "2026-09-12T00:00:00Z"),
        )
    ex(
        "INSERT INTO label_relation"
        " (from_author,from_label,relation,to_author,to_label,note)"
        " VALUES (?,?,?,?,?,?)",
        ("probe-d", LABEL_B, "distinguishes-from", "probe-c", LABEL_B,
         "Written by the test suite. A second relation, on a second label."),
    )

    spec = {
        "probe-a": (LABEL_A, "direction", MODEL_A),
        "probe-b": (LABEL_A, "direction", MODEL_A),
        "probe-c": (LABEL_B, "sae-latent", MODEL_B),
        "probe-d": (LABEL_B, "probe", MODEL_B),
        "probe-e": (LABEL_B, "sae-latent", MODEL_B),
    }
    for author, rel in vectors.items():
        label, kind, (mid, rev, layer, hook) = spec[author]
        facts = confirmed_facts(root, rel)
        ex(
            "INSERT INTO intervention (id,author,model_id,label,version,kind,"
            "model_revision,layer,layer_convention,hook_point,shape,dtype,"
            "l2_norm,activation_norm,coeff_low,coeff_high,steering_position,"
            "license_status,chat_template_hash,artifact_path,artifact_sha256,"
            "is_synthetic)"
            " VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,1)",
            (f"iv_{author}", author, mid, label, "v1", kind, rev, layer,
             "block-0indexed", hook, facts.shape, facts.dtype,
             # Four tensor facts checked against the bytes. `activation_norm`
             # and the coefficient range are not in there and cannot be: there
             # is nothing in the file to check them against, so they are
             # repeated-digit stand-ins for something a model would have to be
             # run to measure.
             facts.l2_norm, 11.1111, 0.5, 1.5, "all-positions",
             "unresolved", "sha256:" + "e" * 8, rel, facts.sha256),
        )

    # A recipe for three of the five. `probe-c` deliberately has none: a
    # published artifact whose procedure was never written down is still a
    # submission and the page has to render that absence.
    #
    # `profile` is namespaced and versioned, never chosen from a list, because
    # there is no list.
    for author, profile, payload, library, theory in (
        ("probe-a", "probe/contrastive-v1",
         {"contrast_source": "a probe, not a dataset", "method": "diffmean",
          "token_masking": "last-token", "layer_sweep": "all blocks",
          "selection_criterion": "written by the test suite"},
         "steering-vectors",
         "Written by the test suite. This author did not orthogonalize against "
         "the axis the other one calls a confound, and says so."),
        ("probe-b", "probe/contrastive-v1",
         {"contrast_source": "a probe, not a dataset", "method": "caa",
          "token_masking": "response-only", "layer_sweep": "blocks 0-15",
          "selection_criterion": "written by the test suite"},
         "steering-vectors",
         "Written by the test suite. This author orthogonalized against the "
         "axis the other one calls the trait."),
        ("probe-e", "probe/sae-latent-v1",
         {"sae_repo": "placeholder/other-architecture-7b-saes",
          "sae_revision": "2" * 40, "latent_index": 41827,
          "hook": "blocks.12.hook_resid_pre",
          "selection_criterion": "written by the test suite"},
         "sae-lens",
         "Written by the test suite. Selecting a latent is a weaker claim than "
         "building a direction, and this row exists so the page has to render "
         "the difference."),
    ):
        label, _kind, model = spec[author]
        ex(
            "INSERT INTO recipe (id,author,model_id,label,version,profile,"
            "payload_json,entrypoint_library,entrypoint_version,"
            "container_digest,theory) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (f"rc_{author}", author, model[0], label, "v1", profile,
             json.dumps(payload), library, "0.0.0-SYNTHETIC",
             "sha256:" + "0" * 64, theory),
        )

    # Different authors checked different axes, and the asymmetry is the
    # informative cell. These two overlap on nothing, on purpose.
    ex("INSERT INTO eval_suite (id,author,name,version,confound_axes_json)"
       " VALUES (?,?,?,?,?)",
       ("es_probe_a", "probe-a", "probe-holdout", "v1",
        json.dumps(["probe_axis_one", "probe_axis_two"])))
    ex("INSERT INTO eval_suite (id,author,name,version,confound_axes_json)"
       " VALUES (?,?,?,?,?)",
       ("es_probe_b", "probe-b", "probe-holdout-other", "v1",
        json.dumps(["probe_axis_three", "probe_axis_four"])))

    # probe-a measured transfer. probe-b did not, and that absence stays a
    # state rather than being filled with a zero.
    ex(
        "INSERT INTO eval_report (id,eval_suite_id,intervention_id,reported_at,"
        "trait_score,coherence_score,transfer_score,confound_json,"
        "coeff_curve_json,is_synthetic) VALUES (?,?,?,?,?,?,?,?,?,1)",
        ("er_probe_a", "es_probe_a", "iv_probe-a", "2026-09-12T00:00:00Z",
         0.7777, 0.8888, 0.6666,
         json.dumps({"probe_axis_one": 0.5555, "probe_axis_two": 0.1111}),
         # The shape is the claim: the trait keeps climbing after coherence has
         # started to fall, so a headline score at the top coefficient is
         # measured on text that is already coming apart.
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
        "trait_score,coherence_score,confound_json,coeff_curve_json,"
        "is_synthetic) VALUES (?,?,?,?,?,?,?,?,1)",
        ("er_probe_b", "es_probe_b", "iv_probe-b", "2026-09-12T00:00:00Z",
         0.4444, 0.9999,
         json.dumps({"probe_axis_three": 0.2222, "probe_axis_four": 0.3333}),
         json.dumps([
             {"coefficient": 0.0, "trait": 0.1111, "coherence": 0.9999},
             {"coefficient": 1.0, "trait": 0.3333, "coherence": 0.9999},
             {"coefficient": 2.0, "trait": 0.4444, "coherence": 0.8888},
         ])),
    )

    ex("INSERT INTO eval_suite (id,author,name,version,confound_axes_json)"
       " VALUES (?,?,?,?,?)",
       ("es_probe_c", "probe-c", "probe-holdout-third", "v1",
        json.dumps(["probe_axis_five", "probe_axis_two"])))
    ex("INSERT INTO eval_suite (id,author,name,version,confound_axes_json)"
       " VALUES (?,?,?,?,?)",
       ("es_probe_d", "probe-d", "probe-boundary", "v1",
        json.dumps(["probe_axis_five"])))

    ex(
        "INSERT INTO eval_report (id,eval_suite_id,intervention_id,reported_at,"
        "trait_score,coherence_score,transfer_score,confound_json,is_synthetic)"
        " VALUES (?,?,?,?,?,?,?,?,1)",
        ("er_probe_c", "es_probe_c", "iv_probe-c", "2026-09-12T00:00:00Z",
         0.6666, 0.7777, 0.2222,
         json.dumps({"probe_axis_five": 0.8888, "probe_axis_two": 0.1111})),
    )
    # A trait score with no coherence measure beside it. The page has to render
    # that as uninterpretable rather than as a number, and this is the row that
    # puts the state under test instead of only in prose.
    ex(
        "INSERT INTO eval_report (id,eval_suite_id,intervention_id,reported_at,"
        "trait_score,confound_json,is_synthetic) VALUES (?,?,?,?,?,?,1)",
        ("er_probe_d", "es_probe_d", "iv_probe-d", "2026-09-12T00:00:00Z",
         0.5555, json.dumps({"probe_axis_five": 0.4444})),
    )

    # Somebody pointing their own eval at a submission that is not theirs. This
    # is the mechanism that makes scores comparable without anyone mandating an
    # eval per label, and it is a first-class action rather than a favor: the
    # subject did not agree to it and cannot withdraw it.
    ex("INSERT INTO eval_suite (id,author,name,version,judge_model,"
       "judge_revision,confound_axes_json) VALUES (?,?,?,?,?,?,?)",
       ("es_probe_attacker", "probe-attacker", "probe-adversarial", "v1",
        "placeholder/judge-8b", "0" * 40,
        json.dumps(["probe_axis_one", "probe_axis_six"])))
    ex(
        "INSERT INTO eval_report (id,eval_suite_id,intervention_id,reported_at,"
        "trait_score,coherence_score,transfer_score,confound_json,is_synthetic)"
        " VALUES (?,?,?,?,?,?,?,?,1)",
        ("er_attacker_on_a", "es_probe_attacker", "iv_probe-a",
         "2026-09-12T00:00:00Z", 0.3333, 0.8888, 0.1111,
         json.dumps({"probe_axis_one": 0.8888, "probe_axis_six": 0.2222})),
    )
    # A verification reporting a score with no coherence beside it, so the
    # verifications view has to render the uninterpretable state too.
    ex("INSERT INTO eval_suite (id,author,name,version,judge_model,"
       "judge_revision) VALUES (?,?,?,?,?,?)",
       ("es_probe_d_x", "probe-d", "probe-crosscheck", "v1",
        "placeholder/judge-8b", "0" * 40))
    ex(
        "INSERT INTO eval_report (id,eval_suite_id,intervention_id,reported_at,"
        "trait_score,is_synthetic) VALUES (?,?,?,?,?,1)",
        ("er_d_on_c", "es_probe_d_x", "iv_probe-c", "2026-09-12T00:00:00Z",
         0.7777),
    )

    # The strongest evidence is the kind the author did not choose. Attacker and
    # author disagree about what it means and both dispositions are recorded.
    ex(
        "INSERT INTO attack (id,intervention_id,attacker,attacked_at,method,"
        "result_json,attacker_disposition,author_disposition,author_response,"
        "is_synthetic) VALUES (?,?,?,?,?,?,?,?,?,1)",
        ("at_probe", "iv_probe-a", "probe-attacker", "2026-09-12T00:00:00Z",
         "alternative-confound-axis",
         json.dumps({"probe_axis_one_above_coeff_1_5": 0.9999}),
         "confirmed-limitation", "no-finding",
         "Written by the test suite. The author answers the attack and neither "
         "disposition is resolved by the registry."),
    )

    # Support cards: applied use, not evaluation. One reports the artifact
    # behaving as documented; one reports it working while the published
    # contract was wrong, which is a defect report no eval could surface.
    ex(
        "INSERT INTO support_card (id,author,model_id,label,version,reporter,"
        "reported_at,repo,repo_commit,purpose,expected,observed,predictability,"
        "deviations,author_response,is_synthetic)"
        " VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,1)",
        ("sc_probe_user_one", "probe-b", MODEL_A[0], LABEL_A, "v1",
         "probe-user-one", "2026-09-12T00:00:00Z", "placeholder/probe-use",
         "a" * 40,
         "Written by the test suite. A purpose somebody used it for.",
         "Per the contract: the documented coefficient range at the documented "
         "layer and hook point.",
         "Held across the documented range.",
         "as-documented", None,
         "Written by the test suite. The author agrees with the report."),
    )
    ex(
        "INSERT INTO support_card (id,author,model_id,label,version,reporter,"
        "reported_at,repo,repo_commit,purpose,expected,observed,predictability,"
        "deviations,author_response,is_synthetic)"
        " VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,1)",
        ("sc_probe_user_two", "probe-a", MODEL_A[0], LABEL_A, "v1",
         "probe-user-two", "2026-09-12T00:00:00Z",
         "placeholder/probe-use-other", "b" * 40,
         "Written by the test suite. A second purpose, reported by somebody "
         "else.",
         "Per the contract: the documented hook point.",
         "Worked, but only after correcting the hook. Applying it as documented "
         "moved nothing.",
         "partial",
         "The published hook_point does not reproduce the author's result, and "
         "nothing on the page disambiguates which of the two is wrong.",
         "Written by the test suite. The author will publish a v2 rather than "
         "edit v1, because a submission is immutable."),
    )

    # A consumer freezing one claimant for one purpose, visibly and
    # contestably. The alternative names its model, because a reference that
    # leaves the model out does not say which artifact was passed over.
    ex(
        "INSERT INTO pin (id,pinned_by,pinned_at,purpose,author,model_id,label,"
        "version,alternatives_json,rationale) VALUES (?,?,?,?,?,?,?,?,?,?)",
        ("pin_probe", "probe-consumer", "2026-09-12T00:00:00Z",
         "Written by the test suite. Frozen so one consumer's own numbers stay "
         "commensurable.",
         "probe-b", MODEL_A[0], LABEL_A, "v1",
         json.dumps([f"probe-a/{MODEL_A[0]}/{LABEL_A}@v1"]),
         "Written by the test suite. Not a claim that it is the better "
         "direction; a claim that one had to be picked and this was it."),
    )

    # One claimed namespace out of several, because unclaimed is the state the
    # page has to render well and claimed is the exception.
    #
    # **The account is fabricated and says so.** The provider does not exist,
    # the subject is not an id any system issued, and the org does not resolve.
    # `.invalid` is reserved by RFC 2606 precisely so a hostname cannot
    # accidentally be real. The real identity in this project is recorded in
    # `V2.md` and is not here.
    #
    # The subject is what the claim binds to; the handle is only what the
    # provider called the account on the day, and the two are different strings
    # here so that a query reading the wrong one is visible rather than
    # coincidentally correct.
    ex(
        "INSERT INTO namespace_claim (id,namespace,provider,subject,handle,"
        "claimed_at,is_synthetic) VALUES (?,?,?,?,?,?,1)",
        ("nc_probe_a", "probe-a", "placeholder-oidc",
         "SYNTHETIC-SUBJECT-NOT-ISSUED-BY-ANY-PROVIDER-probe-a",
         "probe-a-the-first", "2026-09-12T00:00:00Z"),
    )
    # Two kinds, because the evidence `kind` is an open string and the probe
    # should say so where a closed-enum check can see it.
    ex(
        "INSERT INTO namespace_claim_evidence (claim_id,kind,detail,recorded_at)"
        " VALUES (?,?,?,?)",
        ("nc_probe_a", "repo",
         "Written by the test suite. A path inside a temporary directory rather "
         "than a repository anyone owns, resolving to nothing outside this run.",
         "2026-09-12T00:00:00Z"),
    )
    ex(
        "INSERT INTO namespace_claim_evidence (claim_id,kind,detail,recorded_at)"
        " VALUES (?,?,?,?)",
        ("nc_probe_a", "human-decision",
         "Written by the test suite about an account that does not exist. The "
         "reasoning is the evidence for this kind of claim, which is why it is "
         "stored as prose somebody can disagree with rather than as a flag "
         "nobody can.",
         "2026-09-12T00:00:00Z"),
    )
    # Dated, and it renders as dated. Looking again writes a second row beside
    # this one rather than replacing it, which is why `observed_at` is part of
    # what makes a row unique.
    ex(
        "INSERT INTO namespace_membership_observation (id,provider,subject,org,"
        "role,observed_at,source,is_synthetic) VALUES (?,?,?,?,?,?,?,1)",
        ("nm_probe_a", "placeholder-oidc",
         "SYNTHETIC-SUBJECT-NOT-ISSUED-BY-ANY-PROVIDER-probe-a",
         "placeholder-org-does-not-resolve", "member", "2026-09-12T00:00:00Z",
         "https://placeholder-oidc.invalid/oauth/userinfo"),
    )
    conn.commit()


def build(db_path: Path, root: Path | None = None):
    """Write the probe corpus into `db_path`. Returns an open connection.

    Drops the database first, so a caller can rebuild without collecting
    primary-key collisions.
    """
    root = Path(root) if root is not None else ROOT
    db_path = Path(db_path)
    if db_path.exists():
        db_path.unlink()

    vectors = build_vectors(root)
    conn = db.connect(db_path)
    db.migrate(conn)
    seed(conn, root, vectors)
    return conn


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True)
    ap.add_argument(
        "--root", default=None,
        help="what artifact_path values resolve against; defaults to the repo",
    )
    args = ap.parse_args()

    conn = build(Path(args.db), Path(args.root) if args.root else None)
    counts = {
        t: conn.execute(f"SELECT count(*) FROM {t}").fetchone()[0]
        for t in ("submission", "intervention", "eval_report", "attack", "pin",
                  "label_relation", "eval_suite", "support_card")
    }
    print(f"probe corpus in {args.db}")
    for t, n in counts.items():
        print(f"  {t:16} {n}")


if __name__ == "__main__":
    main()
