"""Write the real submissions into the database `fixtures/build.py` created.

Separate file, separate run, on purpose. `fixtures/build.py` says at the top that
nothing it produces is a measurement, and that has to stay true of every line in
it. Real rows in that file would make its docstring a lie the first time somebody
skimmed it.

    .venv/bin/python fixtures/build.py       # synthetic corpus, drops the db
    .venv/bin/python artifacts/seed.py       # real rows, added to it

Every number below is cited to a file in steering-arena at the pinned commit. None
is computed here and none is rounded: where a value has three decimals in the
source, it has three here. `artifacts/REAL.md` says which file each came from.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(HERE))

from registry import db  # noqa: E402
from source import COMMIT, REPO  # noqa: E402

AUTHOR = "soham"
LABEL = "pro-human"
MODEL = "allenai/Olmo-3-1125-32B"
LAYER = 32

# The extraction timestamps out of each file's own `meta`, to the second. Used as
# `created_at` so ordering by newest reflects when the work happened rather than
# when it was imported here.
EXTRACTED = {
    "meandiff": "2026-06-08T22:05:52Z",
    "logistic": "2026-06-08T22:52:10Z",
    "lda":      "2026-06-08T22:52:06Z",
}

FILES = {
    "meandiff": "d_olmo3_v1.safetensors",
    "logistic": "d_olmo3_logistic.safetensors",
    "lda":      "d_olmo3_lda.safetensors",
}

# The author's own version string inside each `.npz`, kept because it is what the
# arena's code will look for and because `v1` is a name this registry deliberately
# did not reuse: naming one version `v1` and the others by estimator would imply a
# revision chain and a baseline, and these are three parallel takes.
AUTHOR_D_VERSION = {
    "meandiff": "v1",
    "logistic": "olmo3_logistic",
    "lda":      "olmo3_lda",
}

METHOD_LINE = {
    "meandiff": "mean of (chosen - rejected) last-token residuals",
    "logistic": "logistic-regression probe on chosen vs rejected, coefficient vector",
    "lda":      "linear discriminant analysis on chosen vs rejected",
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

    for version in ("meandiff", "logistic", "lda"):
        ex(
            "INSERT INTO submission (author,label,version,definition,created_at,"
            "is_synthetic) VALUES (?,?,?,?,?,0)",
            (AUTHOR, LABEL, version, DEFINITION, EXTRACTED[version]),
        )

        ex(
            "INSERT INTO intervention (id,author,label,version,kind,model_id,"
            "model_revision,layer,layer_convention,hook_point,shape,dtype,"
            "l2_norm,activation_norm,coeff_low,coeff_high,steering_position,"
            "license_status,chat_template_hash,artifact_path,is_synthetic)"
            " VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,0)",
            (
                f"iv_soham_{version}", AUTHOR, LABEL, version, "direction", MODEL,
                # Not recorded. The extraction ran against whatever NDIF was
                # serving and the script captured an empty model_build. See
                # schema/migrations/005.
                None,
                LAYER, "block-0indexed", "resid_post", "[5120]", "float32",
                1.0,
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
                f"artifacts/soham/{FILES[version]}",
            ),
        )

        ex(
            "INSERT INTO recipe (id,author,label,version,profile,payload_json,"
            "entrypoint_library,entrypoint_version,container_digest,theory)"
            " VALUES (?,?,?,?,?,?,?,?,?,?)",
            (
                f"rc_soham_{version}", AUTHOR, LABEL, version,
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
                    "residual_norm_at_layer_32": 50.97,
                    "mean_train_gap": TRAIN_GAP[version],
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

    for version in ("meandiff", "logistic", "lda"):
        ex(
            "INSERT INTO eval_report (id,eval_suite_id,intervention_id,reported_at,"
            "transfer_score,confound_json,notes,is_synthetic)"
            " VALUES (?,?,?,?,?,?,?,0)",
            (
                f"er_soham_{version}", "es_soham_audit", f"iv_soham_{version}",
                EXTRACTED[version],
                TRANSFER[version],
                json.dumps(CONFOUNDS[version]),
                "Held-out separation is 1.000, measured on the held-out split of "
                "the same 135 pairs the direction was fitted on, so it is "
                "internal consistency rather than transfer. No trait score and no "
                "coherence score: no judged behavioral evaluation was run.",
            ),
        )
    conn.commit()


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
