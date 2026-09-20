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

**Run against `tests/probe.py` rather than against the corpus.** Every one of
these needs two artifacts in one label that differ in exactly one respect, and
the real corpus holds five submissions by one author, none of them a LoRA and
none of them a probe weight vector. The probe carries the kinds and the shapes;
the rows it writes reach no page and no database the site reads.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tests"))

import probe  # noqa: E402
from controlbun.comparison import similarity_matrix  # noqa: E402

# The probe's two labels, named here so a rename in `probe.py` fails loudly
# rather than turning every lookup below into a silent miss.
TRAIT = probe.LABEL_A
OTHER = probe.LABEL_B


@pytest.fixture
def conn(tmp_path):
    return probe.build(tmp_path / "probe.db")


def _add(conn, author, label, kind, shape, *, layer=12, hook="resid_pre",
         model="placeholder/other-architecture-7b", revision="1" * 40,
         path="tests/_probe/probe_c.safetensors"):
    conn.execute(
        "INSERT INTO submission (author,model_id,label,version,definition,"
        "created_at,is_synthetic) VALUES (?,?,?,?,?,?,1)",
        (author, model, label, "v1", "d", "2026-09-12T00:00:00Z"),
    )
    conn.execute(
        "INSERT INTO intervention (id,author,model_id,label,version,kind,"
        "model_revision,layer,layer_convention,hook_point,shape,dtype,"
        "artifact_path,is_synthetic) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,1)",
        (f"iv_{author}", author, model, label, "v1", kind, revision, layer,
         "block-0indexed", hook, shape, "float32", path),
    )
    conn.commit()


def cell(conn, label, a, b):
    """One cell of the matrix, found by whose row and whose column it is.

    The key is a four-part reference since `schema/migrations/010` and this
    does not spell it out, because one of the cases below is deliberately two
    authors on two different models and a helper that assumed one model could
    not ask for it.
    """
    m = similarity_matrix(conn, label)
    def ref_of(author):
        found = [k for k in m if k.startswith(f"{author}/")]
        assert len(found) == 1, f"{author} has {len(found)} rows on {label}"
        return found[0]
    return m[ref_of(a)][ref_of(b)]


def test_a_matrix_shaped_artifact_gets_no_angle(conn):
    """The case that would have shipped a number from a LoRA."""
    _add(conn, "probe-lora", OTHER, "lora", "[8, 4]")
    result = cell(conn, OTHER, "probe-c", "probe-lora")
    assert result["v"] is None
    assert result["why"] == "not a vector"


def test_vectors_of_different_dimension_get_no_angle(conn):
    _add(conn, "probe-wide", OTHER, "direction", "[16]")
    result = cell(conn, OTHER, "probe-c", "probe-wide")
    assert result["v"] is None
    assert result["why"] == "different dimensions"


def test_different_layers_get_no_angle(conn):
    _add(conn, "probe-shallow", OTHER, "direction", "[8]", layer=3)
    result = cell(conn, OTHER, "probe-c", "probe-shallow")
    assert result["v"] is None
    assert result["why"] == "different layer or hook point"


def test_different_models_get_no_angle(conn):
    _add(conn, "probe-elsewhere", OTHER, "direction", "[8]",
         model="somewhere/else-3b")
    result = cell(conn, OTHER, "probe-c", "probe-elsewhere")
    assert result["v"] is None
    assert result["why"] == "different model or revision"


def test_two_vectors_in_the_same_space_do_get_an_angle(conn):
    """The refusals must not be so broad that nothing compares."""
    result = cell(conn, TRAIT, "probe-a", "probe-b")
    assert result["v"] is not None
    assert -1.0 <= result["v"] <= 1.0
    assert result["why"] is None


def test_comparing_across_kinds_says_what_it_is_comparing(conn):
    """An SAE decoder column and a probe weight vector share a space, so the
    arithmetic holds, but they are not the same kind of object. The number ships
    with a note saying what is actually being compared."""
    result = cell(conn, OTHER, "probe-c", "probe-d")
    assert result["v"] is not None
    assert result["note"] and "steer with" in result["note"]
    assert "sae-latent" in result["note"] and "probe" in result["note"]


def test_same_kind_carries_no_note(conn):
    assert cell(conn, TRAIT, "probe-a", "probe-b")["note"] is None
