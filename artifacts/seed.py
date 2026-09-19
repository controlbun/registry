"""Write the real submissions into the database `fixtures/build.py` created.

Separate file, separate run, on purpose. `fixtures/build.py` says at the top that
nothing it produces is a measurement, and that has to stay true of every line in
it. Real rows in that file would make its docstring a lie the first time somebody
skimmed it.

    .venv/bin/python fixtures/build.py       # synthetic corpus, drops the db
    .venv/bin/python artifacts/seed.py       # real rows, added to it

Every measurement below is cited to a file in steering-arena at the pinned commit.
None is computed here and none is rounded: where a value has three decimals in the
source, it has three here. `artifacts/REAL.md` says which file each came from.

Four values are checked against the bytes rather than trusted, and none of them
is a measurement: the shape, the dtype, the L2 norm and `artifact_sha256`. Three
are cited, one is computed, and every one of them is refused unless the vendored
file agrees. A fact about a tensor that was typed in is a fact that can be typed
in wrong, and the row is what every later check reads. See `confirmed_facts`.

Two more columns are written at the end and not in the `INSERT`: where the
author published each artifact, out of `artifacts/published.json`. That file is
the durable copy of a pin, because this script runs against a database that was
just dropped and rebuilt. See `artifacts/publish.py`.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import replace
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(HERE))

from registry import artifact, db, ref  # noqa: E402
from registry.artifact import local_path  # noqa: E402
from publish import PinError, apply_pins  # noqa: E402
from source import COMMIT, DIRECTIONS, REPO  # noqa: E402

AUTHOR = "soham"
LABEL = "pro-human"
MODEL = "allenai/Olmo-3-1125-32B"

# Three of these sit at layer 32 and one does not, so this stopped being a
# constant. Layer is a property of an artifact rather than of the author.
LAYER = {
    "meandiff": 32,
    "logistic": 32,
    "lda":      32,
    "L24":      24,
}

# Ordered so the layer-32 siblings stay together and the odd one is last, which
# is also the order they were extracted in.
VERSIONS = ("meandiff", "logistic", "lda", "L24")

# The extraction timestamps out of each file's own `meta`, to the second. Used as
# `created_at` so ordering by newest reflects when the work happened rather than
# when it was imported here.
EXTRACTED = {
    "meandiff": "2026-06-08T22:05:52Z",
    "logistic": "2026-06-08T22:52:10Z",
    "lda":      "2026-06-08T22:52:06Z",
    "L24":      "2026-06-08T23:20:02Z",
}

FILES = {
    "meandiff": "d_olmo3_v1.safetensors",
    "logistic": "d_olmo3_logistic.safetensors",
    "lda":      "d_olmo3_lda.safetensors",
    "L24":      "d_olmo3_L24_logistic.safetensors",
}

# What `ingest_arena.py` recorded for the file it wrote, keyed by that filename.
# `source.py` holds it so two files cannot disagree about a sha256, which is the
# same reason the commit lives there.
INGESTED = {
    npz.replace(".npz", ".safetensors"): safetensors_sha
    for npz, _npz_sha, safetensors_sha in DIRECTIONS
}


# Cited, not derived here, and checked against the bytes by `confirmed_facts`.
#
#   shape    5120 is the residual width of allenai/Olmo-3-1125-32B, which is what
#            Season 3 runs. `CONTEXT.md`.
#   dtype    `ingest_arena.py` refuses anything that is not a 1-D float32 array
#            before it converts, so this is the conversion's own contract.
#   l2_norm  the shipped directions are unit-norm; `artifacts/REAL.md` states it
#            and the `mean_train_gap` identity recorded in the recipe depends on
#            it. 1.0 is the cited value, not a rounding of a measurement made
#            here: read as float64 the file norms to 1.0000000000683045, and
#            which of those two the column should hold is exactly the question
#            `registry.artifact.L2_TOLERANCE` answers.
#
# Kept as a claim rather than replaced by a recomputation, because a citation
# that the bytes agree with is worth more than a number derived from the bytes
# it is being compared to. See `_keep_the_claim`.
CITED = artifact.Claim(shape="[5120]", dtype="float32", l2_norm=1.0)


def confirmed_facts(rel: str) -> artifact.Facts:
    """One vendored artifact's facts, every one of them checked against its bytes.

    **The cross-check against `source.py` is deliberate, and the reason is that
    computing a number is not the same as checking one.** Without it this
    function reads whatever happens to be in `artifacts/soham/` and writes it
    into the database as the digest that artifact is published with. Every later
    check then passes by construction: the client would refuse bytes that
    disagree with a record derived from bytes nobody checked. That is the
    transcription problem inverted rather than solved.

    `source.py` carries an independent record. Its value was recorded when
    `ingest_arena.py` converted a `.npz` it had already checked against a sha256
    at a pinned GitHub commit, so the two agreeing means the file here is the
    file that conversion produced from bytes the author published.

    `make site` runs `ingest_arena.py --check`, which compares the same pair. It
    runs after this script, and it is a separate step somebody can drop from the
    chain. Checking at the moment the claim is written is the point: a seeder
    that will write a provenance claim about bytes it has not identified is the
    defect, whatever runs afterwards.

    **The same argument reaches three fields further than it used to.** Shape,
    dtype and norm went into the same `INSERT` as typed literals while the
    digest beside them was cross-checked, so one field of four was derived from
    the artifact and three were transcriptions sitting next to it. They are all
    claims now and all four are compared.
    """
    path = local_path(rel, root=ROOT)
    # The three cited fields plus the one this repository recorded itself.
    # `replace` rather than a fresh `Claim`, so a fifth field on `Claim` is
    # carried here without anybody remembering to add it.
    claim = replace(CITED, sha256=INGESTED[path.name])
    try:
        return artifact.confirmed(path.read_bytes(), claim, subject=rel)
    except artifact.MismatchedArtifact as mismatch:
        raise SystemExit(
            f"{mismatch}\n\nRefusing to seed: writing this row would publish a "
            "claim about bytes that are not the ones this repository converted "
            "at ingest. Rerun artifacts/ingest_arena.py and find out which of "
            "the two moved."
        ) from mismatch


# The author's own version string inside each `.npz`, kept because it is what the
# arena's code will look for and because `v1` is a name this registry deliberately
# did not reuse: naming one version `v1` and the others by estimator would imply a
# revision chain and a baseline, and these are three parallel takes.
AUTHOR_D_VERSION = {
    "meandiff": "v1",
    "logistic": "olmo3_logistic",
    "lda":      "olmo3_lda",
    "L24":      "olmo3_L24_logistic",
}

METHOD_LINE = {
    "meandiff": "mean of (chosen - rejected) last-token residuals",
    "logistic": "logistic-regression probe on chosen vs rejected, coefficient vector",
    "lda":      "linear discriminant analysis on chosen vs rejected",
    "L24":      "logistic-regression probe on chosen vs rejected, coefficient vector",
}

# `<file>.confound_audit.json`, `confound_cosines`. Cosine of the shipped direction
# against a separately estimated confound direction. Low is good.
CONFOUNDS = {
    "meandiff": {"approach": 0.1223, "valence": 0.0001,
                 "length_independent": 0.0018, "approach_probe": 0.1222},
    "logistic": {"approach": 0.1697, "valence": 0.0001,
                 "length_independent": 0.0015, "approach_probe": 0.1668},
    "lda":      {"approach": 0.1246, "valence": 0.0001,
                 "length_independent": 0.0011, "approach_probe": 0.1307},
}

# `<file>.confound_audit.json`, `control_pairs.transfer_ratio`: the mean projection
# gap on six held-out control pairs over the mean gap on the training pairs.
TRANSFER = {"meandiff": 0.74, "logistic": 0.716, "lda": 0.685}

# Same file, `control_pairs.mean_train_gap_chosen_rejected`. Recorded in the recipe
# payload rather than as an eval result because it is an identity, not evidence:
# for a unit-norm d it equals the norm of the class-mean difference times the
# cosine between d and that difference, and reproduces from v1's to within 0.01%.
TRAIN_GAP = {"meandiff": 18.95, "logistic": 13.034, "lda": 7.928}

# `layer_sweep_olmo-3-1125-32b_logistic.json`, `layers[].resid_norm`. A property
# of the model at that layer rather than of any direction, which is why the
# layer-24 row has one even though its confound audit was never run.
RESID_NORM = {"meandiff": 50.97, "logistic": 50.97, "lda": 50.97, "L24": 30.56}

DEFINITION = (
    "Pro-human is whatever separates the chosen from the rejected member of 135 "
    "hand-written pairs across 15 value axes: accountability, boundaries, "
    "conflict resolution, empathy, fairness, feedback, inclusion, integrity, "
    "leadership, learning, ownership, privacy, respect, safety and trust. The "
    "direction is the last-token residual contrast at layer 32 of "
    "allenai/Olmo-3-1125-32B with length and sentiment orthogonalized out. That "
    "is the whole of what is claimed: a representation induced by this dataset "
    "and this model, not a detector for human values. The author has not written "
    "a statement of the construct beyond this, and nothing has been substituted "
    "from a neighboring artifact in its place."
)

# The one thing that is genuinely contested between the three, stated once and
# pointed at from each. Recorded because nobody had written it down.
ESTIMATOR_NOTE = (
    "All three come from the same 135 pairs at the same layer, and differ only "
    "in the estimator. Their pairwise cosines are 0.6965 (meandiff-logistic), "
    "0.4261 (meandiff-lda) and 0.8318 (logistic-lda), recomputed here from the "
    "shipped tensors. Cosine is a displayed fact and not evidence of "
    "disagreement: the informative comparison is what each buys on the evidence "
    "below, and on this battery the answer is nothing that separates them."
)


def seed(conn) -> None:
    ex = conn.execute

    for version in VERSIONS:
        rel = f"artifacts/soham/{FILES[version]}"
        facts = confirmed_facts(rel)

        ex(
            "INSERT INTO submission (author,model_id,label,version,definition,"
            "created_at,is_synthetic) VALUES (?,?,?,?,?,?,0)",
            (AUTHOR, MODEL, LABEL, version, DEFINITION, EXTRACTED[version]),
        )

        ex(
            "INSERT INTO intervention (id,author,model_id,label,version,kind,"
            "model_revision,layer,layer_convention,hook_point,shape,dtype,"
            "l2_norm,activation_norm,coeff_low,coeff_high,steering_position,"
            "license_status,chat_template_hash,artifact_path,artifact_sha256,"
            "is_synthetic)"
            " VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,0)",
            (
                f"iv_soham_{version}", AUTHOR, MODEL, LABEL, version, "direction",
                # Not recorded. The extraction ran against whatever NDIF was
                # serving and the script captured an empty model_build. See
                # schema/migrations/005.
                None,
                # Cited above, checked against the file, written as cited. See
                # CITED and `confirmed_facts`.
                LAYER[version], "block-0indexed", "resid_post", facts.shape, facts.dtype,
                facts.l2_norm,
                # Not recorded, and not the same as unknown: the residual norm at
                # layer 32 is measured (50.97, in the layer sweep) but the
                # bake-off did not scale by it. Recording it here would say the
                # coefficients below are fractions of activation magnitude, and
                # they are raw multipliers of a unit vector. The number is in the
                # recipe payload with the sentence that makes it readable.
                None,
                8.0, 32.0, "all-positions",
                "apache-2.0, redistribution permitted",
                # No chat template was applied. Activations were read from raw
                # concatenated text against a base checkpoint, which is a fact
                # about the extraction rather than a hash anyone forgot.
                None,
                rel,
                # Recorded, unlike the two above. These three are the only rows
                # in the corpus whose bytes this repository did not write, so
                # they are the case the column exists for.
                facts.sha256,
            ),
        )

        ex(
            "INSERT INTO recipe (id,author,model_id,label,version,profile,"
            "payload_json,entrypoint_library,entrypoint_version,"
            "container_digest,theory) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (
                f"rc_soham_{version}", AUTHOR, MODEL, LABEL, version,
                "soham/arena-contrast-v1",
                json.dumps({
                    "estimator": version,
                    "estimator_one_line": METHOD_LINE[version],
                    "contrast_source":
                        "data/seed_pairs.jsonl, 135 hand-written pairs, 15 axes",
                    "token_masking": "last token of prompt + completion, concatenated",
                    "chat_template": "none applied; base checkpoint, raw text",
                    "confounds_orthogonalized": "length, sentiment",
                    "coefficient_semantics":
                        "raw multiplier of the unit direction; the bake-off does "
                        "not scale by residual norm",
                    # The residual norm at this artifact's own layer, from the
                    # sweep. It was keyed to layer 32 while every direction sat
                    # there; a layer-24 row carrying layer 32's norm would be a
                    # measurement of a different place in the model.
                    f"residual_norm_at_layer_{LAYER[version]}": RESID_NORM[version],
                    **({"mean_train_gap": TRAIN_GAP[version]}
                       if version in TRAIN_GAP else {}),
                    "layer_sweep":
                        "layers 16, 24, 32, 40, 48; held-out separation 1.000 at "
                        "every one, so the sweep does not pick a layer",
                    # Provenance lives here because the schema's artifact_repo
                    # resolves against the Hub, and this was published on GitHub.
                    # See DECISIONS.md, 2026-09-14.
                    "source_repo": f"github.com/{REPO}",
                    "source_commit": COMMIT,
                    "source_path": f"data/directions/{FILES[version].replace('.safetensors', '.npz')}",
                    "author_version_string": AUTHOR_D_VERSION[version],
                }),
                # No container was recorded and no pinned library version: the
                # extraction ran from a script in the arena repo against a remote
                # NDIF host. The commit is the only pin there is.
                "steering-arena/scripts/extract_direction.py", None, None,
                ESTIMATOR_NOTE,
            ),
        )

    # One suite, pointed at all three, because it is one battery run three times.
    # No judge model: nothing here is judged text. These are projections and
    # cosines, which is why there is no trait score below and no coherence.
    ex(
        "INSERT INTO eval_suite (id,author,name,version,confound_axes_json)"
        " VALUES (?,?,?,?,?)",
        ("es_soham_audit", AUTHOR, "confound-audit", "v1",
         json.dumps(["approach", "valence", "length_independent",
                     "approach_probe"])),
    )

    # `.get`, not `[...]`. Three of these four carry a confound audit and a
    # transfer ratio; the layer-24 one does not, because the arena never ran that
    # battery against it. Absence is the state and the page renders it as one.
    # Writing a zero, or borrowing a sibling's number because they share a
    # method and a dataset, would be inventing a measurement.
    SEPARATION = (
        "Held-out separation is 1.000, measured on the held-out split of the "
        "same 135 pairs the direction was fitted on, so it is internal "
        "consistency rather than transfer. No trait score and no coherence "
        "score: no judged behavioral evaluation was run."
    )
    NO_AUDIT = (
        " No confound audit and no control-pair transfer for this one: the "
        "arena ran that battery on the three layer-32 directions and not on "
        "this. Its siblings' numbers are not transferable to it, sharing a "
        "method and a dataset notwithstanding."
    )

    for version in VERSIONS:
        audited = version in CONFOUNDS
        ex(
            "INSERT INTO eval_report (id,eval_suite_id,intervention_id,reported_at,"
            "transfer_score,confound_json,notes,is_synthetic)"
            " VALUES (?,?,?,?,?,?,?,0)",
            (
                f"er_soham_{version}", "es_soham_audit", f"iv_soham_{version}",
                EXTRACTED[version],
                TRANSFER.get(version),
                json.dumps(CONFOUNDS[version]) if audited else None,
                SEPARATION if audited else SEPARATION + NO_AUDIT,
            ),
        )

    # A real pin, replacing nothing: the fixtures carry a synthetic one and this
    # sits beside it. Season 2 of the arena froze this direction so player scores
    # within the season stayed commensurable, which is the textbook case for
    # pinning and the opposite of designation as long as it stays visible.
    ex(
        "INSERT INTO pin (id,pinned_by,pinned_at,purpose,author,model_id,label,"
        "version,alternatives_json,rationale) VALUES (?,?,?,?,?,?,?,?,?,?)",
        ("pin_arena_s2", "steering-arena", EXTRACTED["L24"],
         "Season 2 scoring target, frozen so player scores within the season are "
         "commensurable",
         AUTHOR, MODEL, LABEL, "L24",
         # Each alternative names its model, because the choice was made between
         # four takes on one model and a reference that omits the model does not
         # say that.
         json.dumps([
             ref.format(AUTHOR, MODEL, LABEL, v)
             for v in VERSIONS if v != "L24"
         ]),
         "Chosen at the time from a five-layer sweep whose held-out separation "
         "was 1.000 at every layer, so separation could not pick one. Not a "
         "claim that layer 24 is the right layer; a claim that the season needed "
         "one and this was it."),
    )
    conn.commit()

    # --------------------------------------------------------------------- #
    # The one real namespace claim, and every value in it was observed rather
    # than composed.
    #
    # The account is `sohampadia` and the namespace is `soham`. Those are
    # different strings on purpose: the namespace is what `author/label@version`
    # is made of and what a reader sees, and the claim binds the provider's
    # subject, which is opaque and stable. HF handles are renameable, so a claim
    # bound to the handle either breaks on a rename or follows the handle to
    # whoever takes it next.
    #
    # **Where these came from.** A real sign-in through the configured provider
    # on 2026-09-19, whose capture recorded the subject, the handle, the issuer,
    # the userinfo endpoint and the orgs. That capture lives in
    # `artifacts/memberships.jsonl`, which is gitignored: a capture is a dated
    # statement about a real person and this repository is about to be public,
    # so publishing one is a decision to take deliberately rather than a side
    # effect of signing in. What is tracked is this row, which carries the same
    # dated facts. Nothing here is re-derived at build time, because re-deriving
    # it would mean signing in again during `make site`.
    ex = lambda q, v: conn.execute(q, v)  # noqa: E731
    ex(
        "INSERT INTO namespace_claim (id,namespace,provider,subject,handle,"
        "claimed_at,is_synthetic) VALUES (?,?,?,?,?,?,0)",
        ("nc_soham", AUTHOR, "custom:huggingface",
         "62cf4580e7f6014c0ea2450f", "sohampadia", "2026-09-19T16:51:32Z"),
    )
    # The strongest evidence available and the one `V2.md` names first: the repo
    # the artifact was published from is owned by the account making the claim.
    # Checkable by anyone, which is the property that matters, and it is the
    # same commit `soham/trauma@d61-diffmeans-expository-L34` is pinned to.
    ex(
        "INSERT INTO namespace_claim_evidence (claim_id,kind,detail,recorded_at)"
        " VALUES (?,?,?,?)",
        ("nc_soham", "repo",
         "The artifact pinned by soham/trauma@d61-diffmeans-expository-L34 is "
         "published at huggingface.co/sohampadia/pro-human, commit "
         "2ff771e4bbdc21a74d37dee111e98be6d71600f5, path "
         "vectors/events/trauma_minus_neutral_expository.safetensors. That "
         "repository belongs to the account this claim binds, and anyone can "
         "check both halves without asking anybody.",
         "2026-09-19T16:51:32Z"),
    )
    # An observation and not a standing fact. People join and leave
    # organisations, so what is recorded is what the endpoint said and when it
    # said it. Looking again appends a row beside this one.
    ex(
        "INSERT INTO namespace_membership_observation (id,provider,subject,org,"
        "role,observed_at,source,is_synthetic) VALUES (?,?,?,?,?,?,?,0)",
        ("nm_soham_controlbun", "custom:huggingface",
         "62cf4580e7f6014c0ea2450f", "controlbun", "admin",
         "2026-09-19T16:51:32Z", "https://huggingface.co/oauth/userinfo"),
    )
    conn.commit()

    # Where the author published these, if he has. Applied here rather than
    # written into the INSERT above because `artifacts/publish.py record` has to
    # write the same two columns against a database that already exists, and one
    # function writing them means the rebuild and the recording step cannot come
    # apart. Empty until an upload has happened, and an empty record leaves both
    # columns NULL, which is how every row in this corpus starts: pointing at a
    # local file and at nothing remote. See `artifacts/published.json`.
    try:
        applied = apply_pins(conn)
    except PinError as stale:
        raise SystemExit(
            f"{stale}\n\nRefusing to seed: a pin that matches nothing is a "
            "published claim about an artifact this corpus does not hold."
        ) from stale
    for rel, repo, commit in applied:
        print(f"  published  {rel} -> {repo}@{commit[:12]}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=str(ROOT / "registry.db"))
    args = ap.parse_args()

    conn = db.connect(Path(args.db))
    db.migrate(conn)
    seed(conn)

    real = conn.execute(
        "SELECT count(*) FROM submission WHERE is_synthetic = 0"
    ).fetchone()[0]
    print(f"seeded {args.db}")
    print(f"  real submissions {real}")


if __name__ == "__main__":
    main()
