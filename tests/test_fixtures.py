"""The fixture corpus is a pure function of its inputs.

A project about reproducibility cannot ship a build that produces different bytes
each run. This one did: `safetensors` is Rust-backed and serializes metadata out
of a HashMap whose iteration order is randomly seeded per process, so the tensor
payload was stable while the header byte order was not.

These tests hold the fix in place and keep the synthetic markers honest.
"""

from __future__ import annotations

import importlib.util
import json
import struct
import sys
from pathlib import Path

import numpy as np
import pytest
from safetensors import safe_open
from safetensors.numpy import save_file

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "fixtures"
sys.path.insert(0, str(ROOT / "src"))


@pytest.fixture(scope="module")
def build():
    spec = importlib.util.spec_from_file_location("fx_build", FIXTURES / "build.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write_scrambled(path: Path, meta: dict[str, str]) -> None:
    save_file(
        {"direction": np.arange(1, 9, dtype=np.float32)}, str(path), metadata=meta
    )


def test_canonicalizing_makes_the_bytes_stable(build, tmp_path):
    """Two writes of identical content must land on identical bytes.

    Without canonicalization these differ, which is the defect this guards.
    """
    meta = {
        "synthetic": "true", "note": "probe", "model_id": "placeholder/x",
        "model_revision": "0" * 40, "layer": "4", "hook_point": "resid_post",
        "layer_convention": "block-0indexed",
    }
    a, b = tmp_path / "a.safetensors", tmp_path / "b.safetensors"
    _write_scrambled(a, meta)
    _write_scrambled(b, meta)

    build.canonicalize(a)
    build.canonicalize(b)
    assert a.read_bytes() == b.read_bytes(), (
        "identical inputs produced different files; the header is not canonical"
    )


def test_canonicalizing_is_idempotent(build, tmp_path):
    path = tmp_path / "c.safetensors"
    _write_scrambled(path, {"synthetic": "true", "note": "probe"})
    build.canonicalize(path)
    once = path.read_bytes()
    build.canonicalize(path)
    assert path.read_bytes() == once


def test_canonicalizing_preserves_metadata_and_tensor(build, tmp_path):
    meta = {"synthetic": "true", "note": "probe", "model_id": "placeholder/x"}
    path = tmp_path / "d.safetensors"
    _write_scrambled(path, meta)
    build.canonicalize(path)

    with safe_open(str(path), framework="numpy") as f:
        assert f.metadata() == meta, "canonicalizing must not lose metadata"
        assert f.get_tensor("direction").shape == (8,)


def test_committed_fixtures_are_canonical():
    """Whatever is checked in must already be canonical, or the next rebuild
    produces a spurious diff."""
    offenders = []
    for path in sorted(FIXTURES.glob("*.safetensors")):
        raw = path.read_bytes()
        size = struct.unpack("<Q", raw[:8])[0]
        header = json.loads(raw[8:8 + size])
        expected = json.dumps(header, sort_keys=True, separators=(",", ":")).encode()
        expected += b" " * (-len(expected) % 8)
        if raw[8:8 + size] != expected:
            offenders.append(path.name)
    assert not offenders, (
        "checked-in fixtures are not canonical, so a rebuild will churn them:\n  "
        + "\n  ".join(offenders)
    )


def test_every_fixture_carries_its_synthetic_marker():
    """The marker has to survive the file being copied out of this directory and
    separated from SYNTHETIC.md, which is the only reason it lives in metadata."""
    files = sorted(FIXTURES.glob("*.safetensors"))
    assert files, "no fixture vectors found"
    for path in files:
        with safe_open(str(path), framework="numpy") as f:
            meta = f.metadata() or {}
        assert meta.get("synthetic") == "true", f"{path.name} is not marked synthetic"
        assert "not a real direction" in meta.get("note", "").lower(), (
            f"{path.name} carries no note saying what it is"
        )
