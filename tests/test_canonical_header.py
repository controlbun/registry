"""A safetensors file this repository writes is a pure function of its contents.

A project about reproducibility cannot ship a build that produces different bytes
each run. This one did: `safetensors` is Rust-backed and serializes metadata out
of a HashMap whose iteration order is randomly seeded per process, so the tensor
payload was stable while the header byte order was not. Every recorded sha256
would have been a number that means nothing.

`controlbun.artifact.sort_header` is the fix and it is live production code:
`controlbun.ingest` calls it on everything that arrives from anywhere, and
`tests/probe.py` calls it too so a probe cannot exercise a weaker rule than the
one that ships.

These tests were in `tests/test_fixtures.py`, which went with the synthetic
corpus on 2026-09-19. They are about the function rather than about the corpus,
which is why they moved instead of going with it. The two that were genuinely
about the committed fixture files are here as their successors: the artifacts
this repository actually vendors have to be canonical or a rebuild churns them,
and the vectors the probe writes have to carry their own marker or the marker
does not survive the file being copied away.

`tests/test_ingest_bite.py::test_processes_writing_one_input_produce_one_file`
covers the same property from the other side and more strongly, across six
processes, which is the only way to observe a per-process hash seed. What is
here and not there is everything about one process: that running the fix twice
is the same as running it once, and that it moves the header without losing the
metadata or the payload.
"""

from __future__ import annotations

import json
import struct
import sys
from pathlib import Path

import numpy as np
from safetensors import safe_open
from safetensors.numpy import save_file

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tests"))

import probe  # noqa: E402
from controlbun.artifact import sort_header  # noqa: E402

# Where this repository keeps bytes it did not generate at build time. These are
# committed, so a rebuild that reorders their headers is a diff nobody asked for
# and a digest that stops matching.
VENDORED = ROOT / "artifacts" / "soham"


def _write_scrambled(path: Path, meta: dict[str, str]) -> None:
    save_file(
        {"direction": np.arange(1, 9, dtype=np.float32)}, str(path), metadata=meta
    )


def _header_bytes(path: Path) -> tuple[bytes, dict]:
    raw = path.read_bytes()
    size = struct.unpack("<Q", raw[:8])[0]
    return raw[8:8 + size], json.loads(raw[8:8 + size])


def _canonical(header: dict) -> bytes:
    out = json.dumps(header, sort_keys=True, separators=(",", ":")).encode()
    return out + b" " * (-len(out) % 8)


def test_canonicalizing_makes_the_bytes_stable(tmp_path):
    """Two writes of identical content must land on identical bytes.

    Without canonicalization these differ, which is the defect this guards.
    Enough header keys that agreeing by chance is not the reason it passes: with
    two keys two writes come out in the same order about half the time.
    """
    meta = {
        "synthetic": "true", "note": "probe", "model_id": "placeholder/x",
        "model_revision": "0" * 40, "layer": "4", "hook_point": "resid_post",
        "layer_convention": "block-0indexed",
    }
    a, b = tmp_path / "a.safetensors", tmp_path / "b.safetensors"
    _write_scrambled(a, meta)
    _write_scrambled(b, meta)

    sort_header(a)
    sort_header(b)
    assert a.read_bytes() == b.read_bytes(), (
        "identical inputs produced different files; the header is not canonical"
    )


def test_canonicalizing_is_idempotent(tmp_path):
    """Running it twice is running it once.

    Not a nicety. `controlbun.ingest` calls it on output it may then hand to
    something else that calls it again, and a pass that padded or reordered a
    second time would make the digest depend on how many times the fix ran.
    """
    path = tmp_path / "c.safetensors"
    _write_scrambled(path, {"synthetic": "true", "note": "probe"})
    sort_header(path)
    once = path.read_bytes()
    sort_header(path)
    assert path.read_bytes() == once


def test_canonicalizing_preserves_metadata_and_tensor(tmp_path):
    """It moves the header. It does not edit what the header says.

    The failure this catches is silent in the worst way: a rewrite that dropped
    `__metadata__` would produce a file that loads, has the right tensor, hashes
    consistently, and has lost the model id, the layer and the synthetic marker
    the artifact was carrying.
    """
    meta = {"synthetic": "true", "note": "probe", "model_id": "placeholder/x"}
    path = tmp_path / "d.safetensors"
    _write_scrambled(path, meta)
    sort_header(path)

    with safe_open(str(path), framework="numpy") as f:
        assert f.metadata() == meta, "canonicalizing must not lose metadata"
        assert f.get_tensor("direction").shape == (8,)
        assert f.get_tensor("direction")[0] == 1.0, (
            "the payload moved, so the header rewrite is not the only thing "
            "that happened"
        )


def test_committed_artifacts_are_canonical():
    """Whatever is checked in must already be canonical.

    Otherwise the next rebuild produces a spurious diff on files nobody touched,
    and the digest `artifacts/source.py` records for each one stops matching the
    bytes in the tree.

    This read the fixture directory until 2026-09-19. The vendored artifacts are
    the stronger subject anyway: those files are committed rather than
    regenerated, so nothing rewrites them on the way to being checked.
    """
    files = sorted(VENDORED.glob("*.safetensors"))
    assert files, f"no vendored artifacts under {VENDORED}, so this is vacuous"
    offenders = [
        path.name for path in files
        if _header_bytes(path)[0] != _canonical(_header_bytes(path)[1])
    ]
    assert not offenders, (
        "checked-in artifacts are not canonical, so a rebuild will churn them "
        "and their recorded digests will stop matching:\n  "
        + "\n  ".join(offenders)
    )


def test_every_probe_vector_carries_its_synthetic_marker(tmp_path):
    """The marker has to survive the file being copied out of its directory.

    That is the only reason it lives in the file's own metadata rather than in
    a README beside it. The subject used to be `fixtures/`, whose whole point
    was that nothing in it was a measurement; the probe corpus inherited that
    convention along with the job, and a probe tensor that stopped saying what
    it is would be a fabricated artifact loose in a temporary directory with
    nothing on it.
    """
    paths = probe.build_vectors(tmp_path)
    assert paths, "the probe wrote no vectors"
    for rel in paths.values():
        path = tmp_path / rel
        with safe_open(str(path), framework="numpy") as f:
            meta = f.metadata() or {}
        assert meta.get("synthetic") == "true", (
            f"{path.name} is not marked synthetic"
        )
        assert "not a real direction" in meta.get("note", "").lower(), (
            f"{path.name} carries no note saying what it is"
        )
