"""Proof that each fix from the 2026-09-15 review actually bites.

Five defects were found by reading, not by a failing test, which means five checks
did not exist. A fix with no test is a fix until someone refactors past it, and
this repository has produced a green-while-checking-nothing result six times: a
`\\bbest\\b` regex that never matched `best_submission`, a cosine scan looking for a
field that had been renamed, `artifacts/` added with no invariant reading it, and
three bite tests that mutated nothing.

So each case here reconstructs the broken behavior and asserts the new code
refuses it. Where the reconstruction is a mutation, the mutation is asserted to
have landed before the result is believed.
"""

from __future__ import annotations

import json
import sqlite3
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest
from safetensors.numpy import save_file

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from controlbun import client, comparison, db, export  # noqa: E402
from controlbun.artifact import UnsafeArtifactPath, local_path  # noqa: E402


@pytest.fixture
def conn(tmp_path):
    """A synthetic-only database, built the way every other test builds one."""
    path = tmp_path / "bite.db"
    subprocess.run(
        [sys.executable, str(ROOT / "fixtures" / "build.py"), "--db", str(path)],
        check=True, capture_output=True,
    )
    return db.connect(path)


# --------------------------------------------------------------------------- #
# C1. A model holding both a recorded and an unrecorded revision.


def test_a_model_with_mixed_revisions_exports(conn):
    """`sorted({None, "abc"})` raises. Migration 005 made that state reachable.

    Nothing caught it because every Olmo row is NULL and every placeholder row is
    not, on different models, so the set was never mixed. One row is enough.
    """
    conn.execute(
        "UPDATE intervention SET model_revision = NULL WHERE id = 'iv_alice'"
    )
    conn.commit()

    mixed = conn.execute(
        "SELECT DISTINCT model_revision FROM intervention"
        " WHERE model_id = (SELECT model_id FROM intervention WHERE id='iv_alice')"
    ).fetchall()
    assert len(mixed) > 1 and any(r[0] is None for r in mixed), (
        "the fixture no longer produces a mixed revision set, so this proves nothing"
    )

    payload = export.build(conn)
    entry = next(m for m in payload["model_index"] if any(
        s["author"] == "alice" for s in m["submissions"]
    ))
    # Recorded first, unrecorded last, and the None survives so the page can say
    # "not recorded" beside a sibling that did record one.
    assert None in entry["revisions"]
    assert entry["revisions"][-1] is None
    assert entry["revisions"] == sorted(
        entry["revisions"], key=lambda r: (r is None, r or "")
    )


def test_the_old_sort_would_have_raised(conn):
    """The reconstruction, so the test above is not passing for another reason."""
    conn.execute(
        "UPDATE intervention SET model_revision = NULL WHERE id = 'iv_alice'"
    )
    conn.commit()
    revisions = {
        r[0] for r in conn.execute(
            "SELECT model_revision FROM intervention"
            " WHERE model_id = (SELECT model_id FROM intervention WHERE id='iv_alice')"
        )
    }
    with pytest.raises(TypeError):
        sorted(revisions)


# --------------------------------------------------------------------------- #
# C2. A bare author/label with several current versions.


def test_several_current_versions_refuse_to_resolve(conn, tmp_path):
    """Three parallel takes have no order, so picking one is designating one."""
    for version in ("alpha", "beta"):
        conn.execute(
            "INSERT INTO submission (author,model_id,label,version,definition,"
            "created_at,is_synthetic)"
            " VALUES ('alice','placeholder/does-not-resolve-1b','kindness',?,'another take',"
            "'2026-09-14',1)",
            (version,),
        )
    conn.commit()

    heads = conn.execute(
        "SELECT count(*) FROM submission WHERE author='alice' AND label='kindness'"
        " AND superseded_by IS NULL"
    ).fetchone()[0]
    assert heads == 3, f"expected three heads to disambiguate between, got {heads}"

    with pytest.raises(client.Ambiguous) as caught:
        client.load("alice/kindness", database=conn_path(conn))
    # The alternatives are named in full, or the error is a dead end: a
    # reference the reader has to add the model back into is not one they can
    # paste.
    for version in ("v1", "alpha", "beta"):
        assert (f"alice/placeholder/does-not-resolve-1b/kindness@{version}"
                in str(caught.value))


def test_a_revision_chain_still_resolves_to_its_head(conn):
    """Superseding is the author's own history and must keep working."""
    conn.execute(
        "INSERT INTO submission (author,model_id,label,version,definition,"
        "created_at,is_synthetic)"
        " VALUES ('alice','placeholder/does-not-resolve-1b','kindness','v2','revised','2026-09-14',1)"
    )
    conn.execute(
        "UPDATE submission SET superseded_by='v2'"
        " WHERE author='alice' AND label='kindness' AND version='v1'"
    )
    conn.commit()

    got = client.load("alice/kindness", database=conn_path(conn))
    assert got.version == "v2"
    # And the superseded version stays fetchable forever, because pins target it.
    assert client.load("alice/kindness@v1", database=conn_path(conn)).version == "v1"


def test_lexicographic_max_would_have_picked_the_wrong_one():
    """The old rule, on the corpus as it actually stands."""
    assert max(["meandiff", "logistic", "lda"]) == "meandiff"   # the oldest
    assert max(["v1", "v9", "v10"]) == "v9"                     # not the newest


def conn_path(conn: sqlite3.Connection) -> str:
    return conn.execute("PRAGMA database_list").fetchone()[2]


# --------------------------------------------------------------------------- #
# C3. A non-vector artifact reaching the angle.


@pytest.fixture
def inside_repo():
    """A scratch directory under ROOT.

    tmp_path is outside the repository, and an artifact path that leaves the
    repository is the thing S3 now refuses, so a LoRA written there would be
    rejected by the containment check before it ever reached the angle. `.cache`
    is gitignored.
    """
    scratch = ROOT / ".cache" / "bite"
    scratch.mkdir(parents=True, exist_ok=True)
    yield scratch
    for f in scratch.glob("*"):
        f.unlink()


def _add_lora(conn, shape: str, path: Path, array: np.ndarray):
    """A LoRA beside dana, same model, revision, layer and hook point."""
    save_file({"w": array}, str(path))
    iv = conn.execute("SELECT * FROM intervention WHERE id='iv_dana'").fetchone()
    conn.execute(
        "INSERT INTO submission (author,model_id,label,version,definition,"
        "created_at,is_synthetic)"
        " VALUES ('mira',?,'refusal','v1','a low-rank edit','2026-09-14',1)",
        (iv["model_id"],)
    )
    conn.execute(
        "INSERT INTO intervention (id,author,model_id,label,version,kind,"
        "model_revision,layer,layer_convention,hook_point,shape,dtype,"
        "artifact_path,is_synthetic) VALUES ('iv_mira','mira',?,'refusal',"
        "'v1','lora',?,?,?,?,?,'float32',?,1)",
        (iv["model_id"], iv["model_revision"], iv["layer"], iv["layer_convention"],
         iv["hook_point"], shape, str(path.relative_to(ROOT))),
    )
    conn.commit()


@pytest.mark.parametrize("shape,array", [
    # Rank 2. The old code broadcast this and float() raised.
    ("[8, 4]", np.arange(32, dtype=np.float32).reshape(8, 4)),
    # Rank 2 with a leading 1. The dangerous one: np.dot yields a size-1 array,
    # float() succeeds, and a number ships for a LoRA.
    ("[1, 8]", np.arange(8, dtype=np.float32).reshape(1, 8)),
])
def test_pairwise_refuses_a_non_vector(conn, inside_repo, shape, array):
    _add_lora(conn, shape, inside_repo / "lora.safetensors", array)
    comparison.load_vector.cache_clear()

    pairs = comparison.pairwise(conn, "refusal")
    mira = [p for p in pairs if "mira/" in p["a"] or "mira/" in p["b"]]
    assert mira, "the LoRA did not reach pairwise, so nothing here is tested"
    for pair in mira:
        assert pair["angle_similarity"] is None, (
            f"a number shipped for a LoRA of shape {shape}"
        )
        assert pair["angle_comparable"] is False
        assert pair["angle_why"] == "not a vector"


def test_pairwise_and_the_matrix_now_agree(conn, inside_repo):
    """The two were separate implementations and disagreed. Same answer or bust."""
    _add_lora(conn, "[8, 4]", inside_repo / "lora.safetensors",
              np.arange(32, dtype=np.float32).reshape(8, 4))
    comparison.load_vector.cache_clear()

    matrix = comparison.similarity_matrix(conn, "refusal")
    for pair in comparison.pairwise(conn, "refusal"):
        cell = matrix[pair["a"]][pair["b"]]
        assert cell["v"] == pair["angle_similarity"], (
            f"{pair['a']} vs {pair['b']}: matrix says {cell['v']}, "
            f"pairwise says {pair['angle_similarity']}"
        )
        assert cell["why"] == pair["angle_why"]


# --------------------------------------------------------------------------- #
# S3. A database path that leaves the repository.


@pytest.mark.parametrize("hostile", [
    "/etc/passwd",
    "../../../../etc/passwd",
    "fixtures/../../outside.safetensors",
])
def test_an_escaping_artifact_path_is_refused(hostile):
    with pytest.raises(UnsafeArtifactPath):
        local_path(hostile)


def test_the_old_join_would_have_escaped():
    """Why the helper exists: pathlib drops the left operand on an absolute path."""
    assert str(ROOT / "/etc/passwd") == "/etc/passwd"
    assert ".." in str(ROOT / "../../../../etc/passwd")


def test_an_ordinary_path_still_resolves():
    got = local_path("fixtures/alice_kindness_v1.safetensors")
    assert got.is_relative_to(ROOT) and got.exists()


# --------------------------------------------------------------------------- #
# S7. The license audit.


def test_the_license_audit_is_in_the_verify_chain():
    """It was written, required by CLAUDE.md, and called by nothing."""
    makefile = (ROOT / "Makefile").read_text()
    verify = next(
        line for line in makefile.splitlines() if line.startswith("verify:")
    )
    assert "licenses" in verify.split(), (
        f"the copyleft check is not in the gate: {verify!r}"
    )
    # After `site`, which is what installs node_modules.
    targets = verify.split(":", 1)[1].split()
    assert targets.index("licenses") > targets.index("site")


def test_the_license_audit_refuses_an_empty_scan(tmp_path):
    """Scanning nothing used to report 'all permissive' and exit 0."""
    script = (ROOT / "astro" / "scripts" / "check-licenses.mjs").read_text()
    code = [ln for ln in script.splitlines() if not ln.lstrip().startswith("//")]
    assert "fileURLToPath" in script, "the URL is not converted to a path"
    offenders = [ln.strip() for ln in code if ".pathname" in ln]
    assert not offenders, (
        "a file URL percent-encodes, so .pathname breaks on a path with a "
        f"space: {offenders}"
    )

    empty = tmp_path / "astro"
    (empty / "scripts").mkdir(parents=True)
    (empty / "scripts" / "check-licenses.mjs").write_text(script)
    result = subprocess.run(
        ["node", str(empty / "scripts" / "check-licenses.mjs")],
        capture_output=True, text=True,
    )
    if result.returncode == 127 or "not found" in result.stderr.lower():
        pytest.skip("node is not available")
    assert result.returncode == 1, (
        f"an empty scan exited {result.returncode}, so a GPL dependency in an "
        f"unreadable tree would report clean:\n{result.stdout}"
    )
    assert "no packages found" in result.stderr


# --------------------------------------------------------------------------- #
# T1. The attestation inventory.


def test_the_inventory_guard_notices_an_unlisted_stamp():
    """The guard that would have caught the tree stamp on the day it was made."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "probed_attest", ROOT / "tests" / "test_attest.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    module.test_every_manifest_on_disk_is_in_the_inventory()

    dropped = "MANIFEST_TREE_2026-09-13_2145.sha256"
    assert dropped in module.REQUIRED_MANIFESTS, "nothing to drop; test is inert"
    module.REQUIRED_MANIFESTS = [n for n in module.REQUIRED_MANIFESTS if n != dropped]

    with pytest.raises(AssertionError, match=dropped):
        module.test_every_manifest_on_disk_is_in_the_inventory()
