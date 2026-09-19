"""Convert three real directions from steering-arena into safetensors.

These are the first real artifacts in this repository. Everything in `fixtures/`
is fabricated and says so; nothing here is. Read `artifacts/REAL.md`.

**Why a conversion step exists at all.** The author published `.npz`. Loading one
means `numpy.load`, whose `allow_pickle` argument turns a data file into arbitrary
code execution, and a registry that hands out other people's array files cannot be
in the business of asking readers to trust a flag default. safetensors was chosen
on ingest for exactly this: the format cannot express an object array, so the
question does not arise. All three of these load with `allow_pickle=False`, which
is checked rather than assumed, so the conversion loses nothing.

**What is pinned and what is checked.** The source is a GitHub commit, not a
branch, for the same reason the schema resolves artifacts by commit SHA: a branch
moves and a pin that moves is not a pin. Every `.npz` is verified against the
sha256 recorded in the ingest table before it is read, and every `.safetensors`
this writes is verified against a recorded sha256 after. So a clean checkout can
rerun this with network and get byte-identical files, and can rerun `--check`
without network to confirm the committed copies are the ones this produced.

    .venv/bin/python artifacts/ingest_arena.py           # fetch, convert, write
    .venv/bin/python artifacts/ingest_arena.py --check   # offline, verify only

**What is left in this file and what moved.** All of the machinery is now
`registry.ingest`, which takes bytes from anywhere and writes one checked
safetensors file. What stays here is the part that is only true of this corpus:
where these three came from, that the arena packs a direction as `d` beside a
`meta` blob, and that a direction is a 1-D float32 array. That last one is a
contract of this conversion rather than of the registry, which holds artifacts of
kinds nobody has named yet and does not decide what shape one has to be.

The steering contract, the evidence and the author's prose do not live here. They
are database rows, written by `artifacts/seed.py`.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from registry import ingest  # noqa: E402
from registry.artifact import Claim, MismatchedArtifact, local_path  # noqa: E402

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from source import COMMIT, DIRECTIONS, HOST, LICENSE, MEDIA, REPO  # noqa: E402

OUT = "artifacts/soham"


def arena_payload(parsed: ingest.Parsed) -> ingest.Payload:
    """One `.npz` as the arena writes them: the direction in `d`, JSON in `meta`.

    Everything this returns is read off the file. A provenance header somebody
    retyped is a claim about the file rather than a fact from it, and the four
    `source_*` fields beside these come from the pin `registry.ingest` fetched
    against, for the same reason.
    """
    if sorted(parsed.arrays) != ["d", "meta"]:
        raise SystemExit(
            f"expected arrays ['d', 'meta'], got {sorted(parsed.arrays)}"
        )

    vector = parsed.arrays["d"]
    meta = json.loads(str(parsed.arrays["meta"]))

    # The conversion's own contract, and cited as such by `artifacts/seed.py`,
    # which records `[5120]` and `float32` partly because this refuses anything
    # else. It constrains this corpus and nothing else: the registry's `kind` is
    # an open string and an SAE latent or a rank-one edit is not a 1-D vector.
    if vector.dtype != np.float32 or vector.ndim != 1:
        raise SystemExit(
            f"expected a 1-D float32 array, got {vector.ndim}-D {vector.dtype}"
        )

    return ingest.Payload(
        name="d",
        tensor=vector,
        metadata={
            "synthetic": "false",
            "license": LICENSE,
            "model_id": meta["model_id"],
            "layer": str(meta["layer"]),
            "layer_convention": "block-0indexed",
            "hook_point": "resid_post",
            "extraction_method": meta["extraction_method"],
            "confounds_removed": ",".join(meta["confounds_removed"]),
            "num_pairs": str(meta["num_pairs"]),
            "author_d_version": meta["d_version"],
            "extracted_at": meta["created_at"],
        },
    )


def source_of(name: str, npz_sha: str) -> ingest.PinnedRepoFile:
    """The pin, as one object, so the URL and the provenance share their fields."""
    return ingest.PinnedRepoFile(
        host=HOST,
        repo=REPO,
        commit=COMMIT,
        path=f"data/directions/{name}",
        sha256=npz_sha,
        url_template=MEDIA,
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="verify the committed files offline and write nothing")
    args = ap.parse_args()

    failures = 0

    for name, npz_sha, out_sha in DIRECTIONS:
        rel = f"{OUT}/{name.replace('.npz', '.safetensors')}"
        # Resolved the same way in both modes, and by the function that refuses
        # a path leaving the repository rather than by string joining.
        path = local_path(rel, root=ROOT)
        # The digest this ingest recorded for the file it wrote, offered back as
        # a claim. A conversion whose output has moved is refused rather than
        # re-recorded, in both modes.
        claim = Claim(sha256=out_sha)

        if args.check:
            if not path.exists():
                print(f"  MISSING  {rel}")
                failures += 1
                continue
            try:
                facts = ingest.confirmed_file(path, claim, subject=rel)
            except MismatchedArtifact as drift:
                print(f"  DRIFTED  {rel}\n           {drift}")
                failures += 1
                continue
            print(f"  ok       {rel}  {facts.sha256[:16]}")
            continue

        try:
            written = ingest.ingest(
                source_of(name, npz_sha),
                out=rel,
                subject=rel,
                claim=claim,
                payload=arena_payload,
                root=ROOT,
            )
        except MismatchedArtifact as drift:
            # Nothing was written. `registry.ingest` stages the output and moves
            # it into place only after the check, so a drifted conversion leaves
            # the committed artifact where it was instead of overwriting it with
            # the bytes that failed.
            print(f"  DRIFTED  {rel}\n           {drift}")
            failures += 1
            continue

        print(f"  wrote    {rel}  {written.facts.sha256[:16]}"
              f"  {written.header['extraction_method']}")

    if failures:
        print(f"\n{failures} file(s) do not match the recorded sha256", file=sys.stderr)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
