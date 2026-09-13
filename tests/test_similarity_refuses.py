"""An angle is only computed where an angle exists.

`kind` is an open string, and not every kind is a vector in the residual stream:

    direction    a vector at layer L                    angle defined
    sae-latent   the decoder column for that latent     angle defined, same space
    probe        the weight vector                      angle defined, same space
    lora         a low-rank matrix                      angle undefined
    reft         a learned intervention                 angle undefined

The comparability gate originally tested model, revision, layer and hook point
and never the shape, so the first LoRA anyone published would have been handed a
cosine as if it meant something. These check that it refuses, and says why.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from registry import db  # noqa: E402
from registry.comparison import similarity_matrix  # noqa: E402


@pytest.fixture
def conn(tmp_path):
    path = tmp_path / "fixture.db"
    subprocess.run(
        [sys.executable, str(ROOT / "fixtures" / "build.py"), "--db", str(path)],
        check=True, capture_output=True,
    )
    return db.connect(path)


def _add(conn, author, label, kind, shape, *, layer=12, hook="resid_pre",
         model="placeholder/other-architecture-7b", revision="1" * 40,
         path="fixtures/dana_refusal_v1.safetensors"):
    conn.execute(
        "INSERT INTO submission (author,label,version,definition,created_at,"
        "is_synthetic) VALUES (?,?,?,?,?,1)",
        (author, label, "v1", "d", "2026-09-12T00:00:00Z"),
    )
    conn.execute(
        "INSERT INTO intervention (id,author,label,version,kind,model_id,"
        "model_revision,layer,layer_convention,hook_point,shape,dtype,"
        "artifact_path,is_synthetic) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,1)",
        (f"iv_{author}", author, label, "v1", kind, model, revision, layer,
         "block-0indexed", hook, shape, "float32", path),
    )
    conn.commit()


def cell(conn, label, a, b):
    m = similarity_matrix(conn, label)
    return m[f"{a}/{label}@v1"][f"{b}/{label}@v1"]


def test_a_matrix_shaped_artifact_gets_no_angle(conn):
    """The case that would have shipped a number from a LoRA."""
    _add(conn, "lyn", "refusal", "lora", "[8, 4]")
    result = cell(conn, "refusal", "dana", "lyn")
    assert result["v"] is None
    assert result["why"] == "not a vector"


def test_vectors_of_different_dimension_get_no_angle(conn):
    _add(conn, "mo", "refusal", "direction", "[16]")
    result = cell(conn, "refusal", "dana", "mo")
    assert result["v"] is None
    assert result["why"] == "different dimensions"


def test_different_layers_get_no_angle(conn):
    _add(conn, "nia", "refusal", "direction", "[8]", layer=3)
    result = cell(conn, "refusal", "dana", "nia")
    assert result["v"] is None
    assert result["why"] == "different layer or hook point"


def test_different_models_get_no_angle(conn):
    _add(conn, "ola", "refusal", "direction", "[8]", model="somewhere/else-3b")
    result = cell(conn, "refusal", "dana", "ola")
    assert result["v"] is None
    assert result["why"] == "different model or revision"


def test_two_vectors_in_the_same_space_do_get_an_angle(conn):
    """The refusals must not be so broad that nothing compares."""
    result = cell(conn, "kindness", "alice", "bob")
    assert result["v"] is not None
    assert -1.0 <= result["v"] <= 1.0
    assert result["why"] is None


def test_comparing_across_kinds_says_what_it_is_comparing(conn):
    """An SAE decoder column and a probe weight vector share a space, so the
    arithmetic holds, but they are not the same kind of object. The number ships
    with a note saying what is actually being compared."""
    result = cell(conn, "refusal", "dana", "erik")
    assert result["v"] is not None
    assert result["note"] and "steer with" in result["note"]
    assert "sae-latent" in result["note"] and "probe" in result["note"]


def test_same_kind_carries_no_note(conn):
    assert cell(conn, "kindness", "alice", "bob")["note"] is None
