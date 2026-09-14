"""Convert three real directions from steering-arena into safetensors.

These are the first real artifacts in this repository. Everything in `fixtures/`
is fabricated and says so; nothing here is. Read `artifacts/REAL.md`.

**Why a conversion step exists at all.** The author published `.npz`. Loading one
means `numpy.load`, whose `allow_pickle` argument turns a data file into arbitrary
code execution, and a registry that hands out other people's array files cannot be
in the business of asking readers to trust a flag default. safetensors was chosen
on ingest for exactly this: the format cannot express an object array, so the
question does not arise. All three of these load with `allow_pickle=False`, which
is checked below rather than assumed, so the conversion loses nothing.

**What is pinned and what is checked.** The source is a GitHub commit, not a
branch, for the same reason the schema resolves artifacts by commit SHA: a branch
moves and a pin that moves is not a pin. Every `.npz` is verified against the
sha256 recorded in the ingest table before it is read, and every `.safetensors`
this writes is verified against a recorded sha256 after. So a clean checkout can
rerun this with network and get byte-identical files, and can rerun `--check`
without network to confirm the committed copies are the ones this produced.

    .venv/bin/python artifacts/ingest_arena.py           # fetch, convert, write
    .venv/bin/python artifacts/ingest_arena.py --check   # offline, verify only

The steering contract, the evidence and the author's prose do not live here. They
are database rows, written by `artifacts/seed.py`.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import sys
import urllib.request
from pathlib import Path

import numpy as np
from safetensors.numpy import save_file

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from registry.artifact import sort_header  # noqa: E402

HERE = Path(__file__).resolve().parent
OUT = HERE / "soham"
sys.path.insert(0, str(HERE))

from source import COMMIT, DIRECTIONS, LICENSE, MEDIA, REPO  # noqa: E402


def sha256(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()


def fetch(name: str, expected: str) -> bytes:
    url = f"{MEDIA}/{REPO}/{COMMIT}/data/directions/{name}"
    with urllib.request.urlopen(url, timeout=60) as response:
        blob = response.read()
    got = sha256(blob)
    if got != expected:
        raise SystemExit(
            f"{name}: sha256 {got} does not match the recorded {expected}. "
            "Refusing to convert: the bytes at that commit are not the bytes "
            "this ingest was written against."
        )
    return blob


def convert(name: str, blob: bytes, npz_sha: str) -> tuple[Path, dict]:
    """One `.npz` to one `.safetensors`, carrying its provenance in the header."""
    # allow_pickle=False is the check, not a precaution: if any of these needed
    # pickle the conversion would be handing a reader an executable file, and the
    # right response is to fail rather than to set the flag.
    archive = np.load(io.BytesIO(blob), allow_pickle=False)
    if sorted(archive.files) != ["d", "meta"]:
        raise SystemExit(f"{name}: expected arrays ['d', 'meta'], got {archive.files}")

    vector = np.ascontiguousarray(archive["d"])
    meta = json.loads(str(archive["meta"]))

    if vector.dtype != np.float32 or vector.ndim != 1:
        raise SystemExit(f"{name}: expected a 1-D float32 array, got "
                         f"{vector.ndim}-D {vector.dtype}")

    # Everything below is read off the file, never typed in. A provenance header
    # somebody retyped is a claim about the file rather than a fact from it.
    header = {
        "synthetic": "false",
        "source_repo": f"github.com/{REPO}",
        "source_commit": COMMIT,
        "source_path": f"data/directions/{name}",
        "source_sha256": npz_sha,
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
    }

    path = OUT / name.replace(".npz", ".safetensors")
    save_file({"d": vector}, str(path), metadata=header)
    sort_header(path)
    return path, meta


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="verify the committed files offline and write nothing")
    args = ap.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)
    failures = 0

    for name, npz_sha, out_sha in DIRECTIONS:
        path = OUT / name.replace(".npz", ".safetensors")

        if args.check:
            if not path.exists():
                print(f"  MISSING  {path.relative_to(ROOT)}")
                failures += 1
                continue
            got = sha256(path.read_bytes())
            mark = "ok" if got == out_sha else "DRIFTED"
            failures += got != out_sha
            print(f"  {mark:8} {path.relative_to(ROOT)}  {got[:16]}")
            continue

        path, meta = convert(name, fetch(name, npz_sha), npz_sha)
        got = sha256(path.read_bytes())
        note = "" if got == out_sha else f"  (recorded {out_sha[:16]})"
        failures += got != out_sha
        print(f"  wrote    {path.relative_to(ROOT)}  {got[:16]}{note}"
              f"  {meta['extraction_method']}")

    if failures:
        print(f"\n{failures} file(s) do not match the recorded sha256", file=sys.stderr)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
