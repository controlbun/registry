"""Proof that the content-hash checks added for S1 actually bite.

The defect was that nothing compared fetched bytes against a recorded digest.
`fetch.resolve` returns bytes from our copy, the author's repo or a local file;
`Submission._check` compared shape and dtype; the falsifier recomputed shape,
dtype and norm and only for files already in the repository. A substituted tensor
of the same shape and dtype passed all of it.

Two new checks, and one bite test each. Both are written the way
`tests/test_scan_gap_bite.py` is, because "the new check passes" proves nothing on
its own: what has to be shown is that the probe goes **unnoticed** under the old
behavior and is caught under the new one. Every mutation is asserted to have
landed before its result is believed.

The substituted tensor below is an obviously synthetic descending ramp. It stands
in for what a re-pointed LFS object returns; it is not a measurement and nothing
here reads it as one.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import shutil
import sqlite3
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest
from safetensors.numpy import load as load_bytes
from safetensors.numpy import load_file, save, save_file

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from controlbun import client, db, fetch  # noqa: E402
from controlbun.artifact import sort_header  # noqa: E402

# alice's fixture is `np.arange(1, 9)` normalized, eight float32 elements. This is
# eight float32 elements that are not those. Same shape, same dtype, different
# bytes, which is the whole of what the old check could not see.
SUBSTITUTE = save({"direction": np.arange(8, 0, -1, dtype=np.float32)})


@pytest.fixture
def conn(tmp_path):
    """A synthetic-only database, built the way every other test builds one."""
    path = tmp_path / "digest.db"
    subprocess.run(
        [sys.executable, str(ROOT / "fixtures" / "build.py"), "--db", str(path)],
        check=True, capture_output=True,
    )
    return db.connect(path)


def _submission(conn, monkeypatch, blob: bytes):
    """alice's submission, with whatever bytes we hand it standing in as the file."""
    monkeypatch.setattr(fetch, "resolve", lambda **k: blob)
    row = conn.execute(
        "SELECT * FROM submission WHERE author='alice' AND label='kindness'"
    ).fetchone()
    return client._build(conn, row)


def _recorded(conn, iv_id: str = "iv_alice") -> str | None:
    return conn.execute(
        "SELECT artifact_sha256 FROM intervention WHERE id=?", (iv_id,)
    ).fetchone()[0]


# --------------------------------------------------------------------------- #
# The column exists and stays optional.


def test_the_digest_column_ships_and_is_nullable(conn):
    """NOT NULL here would exclude every artifact this registry only points at.

    Checked against the schema that actually ships, after every migration has
    run, rather than against the text of 006. A later migration that rebuilt the
    table and tightened the column would pass a reading of the file.
    """
    cols = {r["name"]: r for r in conn.execute("PRAGMA table_info(intervention)")}
    assert "artifact_sha256" in cols, (
        "the column is gone, so every check in this file is vacuous"
    )
    assert cols["artifact_sha256"]["notnull"] == 0, (
        "artifact_sha256 became NOT NULL. That does not produce a digest, it "
        "produces a string, and a wrong one makes the client refuse the "
        "author's own bytes forever. See schema/migrations/006."
    )

    # And the pointer-only case is writable end to end, not merely permitted by
    # the column definition.
    conn.execute(
        "INSERT INTO submission (author,model_id,label,version,definition,"
        "created_at,is_synthetic) VALUES ('nadia','placeholder/does-not-resolve-1b',"
        "'kindness','v1','pointed at, not held','2026-09-16',1)"
    )
    conn.execute(
        "INSERT INTO intervention (id,author,label,version,kind,model_id,layer,"
        "layer_convention,hook_point,shape,dtype,artifact_repo,artifact_commit,"
        "artifact_path,is_synthetic) VALUES ('iv_nadia','nadia','kindness','v1',"
        "'direction','placeholder/does-not-resolve-1b',4,'block-0indexed',"
        "'resid_post','[8]','float32','someone/else',?,'d.safetensors',1)",
        ("c" * 40,),
    )
    conn.commit()
    assert _recorded(conn, "iv_nadia") is None

    sub = client.load("nadia/kindness@v1", database=_path(conn))
    assert sub.contract.artifact_sha256 is None


def _path(conn: sqlite3.Connection) -> str:
    return conn.execute("PRAGMA database_list").fetchone()[2]


# --------------------------------------------------------------------------- #
# S1a. The client refuses bytes whose digest disagrees with the record.


# The positive control, that the real committed fixture still loads with its
# digest intact, is `test_the_recorded_artifact_loads` in
# `tests/test_artifact_check.py`. Not repeated here.


def test_a_substituted_tensor_of_the_same_shape_and_dtype_is_refused(conn, monkeypatch):
    """The defect, reproduced against the fix."""
    recorded = _recorded(conn)
    assert recorded, "no digest was recorded, so this proves nothing"

    sub = _submission(conn, monkeypatch, SUBSTITUTE)
    arrived = next(iter(load_bytes(SUBSTITUTE).values()))

    # The old check in full: shape and dtype. Both agree, which is why a
    # substitution at this layer was invisible.
    assert str(list(arrived.shape)) == sub.contract.shape
    assert str(arrived.dtype) == sub.contract.dtype
    assert hashlib.sha256(SUBSTITUTE).hexdigest() != recorded, (
        "the substitute hashes to the recorded digest, so it is not a substitute"
    )

    with pytest.raises(client.MismatchedArtifact) as caught:
        sub.vector()
    # Both digests named, or the error tells the reader nothing actionable.
    assert recorded in str(caught.value)
    assert hashlib.sha256(SUBSTITUTE).hexdigest() in str(caught.value)


def test_the_same_substitution_went_unnoticed_before(conn, monkeypatch):
    """The old behavior, reproduced by removing the record it reads.

    This is the half that matters. It shows the bytes refused above are bytes
    that were previously handed back without a word, and at the same time it
    shows that absence of a digest is a state rather than a refusal: an artifact
    nobody hashed still loads, which is what keeps 006 from being a required
    field by the back door.
    """
    conn.execute("UPDATE intervention SET artifact_sha256 = NULL WHERE id='iv_alice'")
    conn.commit()
    assert _recorded(conn) is None, "the mutation did not land"

    got = _submission(conn, monkeypatch, SUBSTITUTE).vector()
    assert got.tolist() == [8.0, 7.0, 6.0, 5.0, 4.0, 3.0, 2.0, 1.0], (
        "with no digest recorded the client must still hand over the tensor; a "
        "refusal here would make the column mandatory in everything but name"
    )


def test_the_digest_is_checked_before_the_file_is_parsed(conn, monkeypatch):
    """Ordering, the way `artifacts/ingest_arena.py` does it.

    Bytes that are not a safetensors file at all raise `MismatchedArtifact` with
    the digest named, not whatever the parser raises. If the parser ran first, a
    hostile file would be handed to it before anything had established that the
    bytes are the ones the author published.
    """
    assert _recorded(conn), "no digest recorded, so ordering cannot be observed"
    sub = _submission(conn, monkeypatch, b"not a safetensors file")
    with pytest.raises(client.MismatchedArtifact, match="sha256"):
        sub.vector()


# --------------------------------------------------------------------------- #
# S1b. The falsifier notices a file that no longer hashes to its record.


def _load_falsifier(root: Path):
    spec = importlib.util.spec_from_file_location(
        "digest_probed_falsifier", root / "falsifier" / "verify.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.ROOT = root
    module.DB = root / "registry.db"
    module.EXPORT = root / "astro" / "src" / "data" / "controlbun.json"
    module.DIST = root / "astro" / "dist"
    # Reloaded per call rather than reused: `_vector` is lru_cached, so a module
    # kept across a mutation would recheck the tensor it read before it.
    module.failures = []
    return module


@pytest.fixture(scope="module")
def tree(tmp_path_factory):
    """A copy with a database, an export and one built page."""
    dest = tmp_path_factory.mktemp("digestfalsify") / "repo"
    dest.mkdir()
    for part in ("falsifier", "fixtures", "schema", "src"):
        shutil.copytree(ROOT / part, dest / part,
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    (dest / "astro" / "src" / "data").mkdir(parents=True)
    (dest / "astro" / "dist").mkdir(parents=True)

    subprocess.run(
        [sys.executable, str(dest / "fixtures" / "build.py"),
         "--db", str(dest / "registry.db")],
        check=True, capture_output=True,
    )
    subprocess.run(
        [sys.executable, "-m", "controlbun.export",
         "--db", str(dest / "registry.db"),
         "--out", str(dest / "astro" / "src" / "data" / "controlbun.json")],
        check=True, capture_output=True,
        env={"PYTHONPATH": str(dest / "src"), "PATH": "/usr/bin:/bin"},
        cwd=dest,
    )

    payload = json.loads(
        (dest / "astro" / "src" / "data" / "controlbun.json").read_text()
    )
    trait = payload["labels"][0]["claimants"][0]["trait_score"]
    page = dest / "astro" / "dist" / "probe"
    page.mkdir(parents=True)
    (page / "index.html").write_text(
        f"<html><body><p>Synthetic corpus. Trait {trait:.4f}</p></body></html>"
    )
    return dest


def _connect(tree: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(tree / "registry.db")
    conn.row_factory = sqlite3.Row
    return conn


def _negate_in_place(path: Path) -> None:
    """Rewrite the file with every element negated.

    Shape, dtype and L2 norm are all preserved exactly, because negating a float
    is exact. So this is a different artifact that satisfies every check the
    falsifier had before 006.
    """
    name, tensor = next(iter(load_file(path).items()))
    save_file({name: -tensor}, str(path))
    sort_header(path)


def test_the_clean_copy_passes(tree):
    assert _load_falsifier(tree).main() == 0, (
        "the copy is already failing, so nothing below proves anything"
    )


def test_a_tampered_artifact_is_caught_and_would_not_have_been(tree):
    held = tree / "fixtures" / "alice_kindness_v1.safetensors"
    original = held.read_bytes()
    recorded = _connect(tree).execute(
        "SELECT artifact_sha256 FROM intervention WHERE id='iv_alice'"
    ).fetchone()[0]
    assert recorded, "no digest was recorded in the copy, so this proves nothing"

    _negate_in_place(held)
    try:
        # The mutation landed, and it landed in the way that makes the point:
        # different bytes, identical shape, dtype and norm.
        before = next(iter(load_bytes(original).values()))
        after = next(iter(load_file(held).values()))
        assert hashlib.sha256(held.read_bytes()).hexdigest() != recorded
        assert after.shape == before.shape and after.dtype == before.dtype
        assert float(np.linalg.norm(after)) == float(np.linalg.norm(before))

        # The old check, run on its own against the tampered file: silent. This
        # is the gap, reproduced.
        old = _load_falsifier(tree)
        old.check_artifacts_match_their_metadata(_connect(tree))
        assert old.failures == [], (
            "shape, dtype and norm caught the substitution, so the new check is "
            f"not what closes this gap: {old.failures}"
        )

        # The new check, on the same file: named.
        new = _load_falsifier(tree)
        new.check_artifact_digests_match_the_record(_connect(tree))
        assert any("iv_alice" in line for line in new.failures), (
            f"the digest check did not name the tampered row: {new.failures}"
        )

        # And the whole run goes red with a digest failure in it, rather than
        # only with the angle failures the substitution also causes.
        whole = _load_falsifier(tree)
        assert whole.main() == 1
        assert any(line.startswith("[digests]") for line in whole.failures)
    finally:
        held.write_bytes(original)


def test_a_corpus_with_no_digests_reports_itself_inert(tree):
    """A check that examined nothing must not print a reassuring line.

    Six green-while-checking-nothing results in this repository, three of them
    bite tests. The inert branch is the one that would go unnoticed for longest,
    so it gets a test of its own.
    """
    conn = _connect(tree)
    before = dict(conn.execute(
        "SELECT id, artifact_sha256 FROM intervention"
    ).fetchall())
    assert any(before.values()), "nothing to clear; this test is inert itself"

    conn.execute("UPDATE intervention SET artifact_sha256 = NULL")
    conn.commit()
    try:
        cleared = _connect(tree).execute(
            "SELECT count(*) FROM intervention WHERE artifact_sha256 IS NOT NULL"
        ).fetchone()[0]
        assert cleared == 0, "the mutation did not land"

        module = _load_falsifier(tree)
        module.check_artifact_digests_match_the_record(_connect(tree))
        assert any("inert" in line for line in module.failures), (
            f"a run that rechecked no digest reported success: {module.failures}"
        )
    finally:
        restore = _connect(tree)
        for iv_id, value in before.items():
            restore.execute(
                "UPDATE intervention SET artifact_sha256=? WHERE id=?",
                (value, iv_id),
            )
        restore.commit()


def test_a_vendored_artifact_that_drifted_is_refused_at_seed_time(tmp_path):
    """`artifacts/seed.py` will not write a digest it has not identified.

    The three real rows are the only ones whose bytes this repository did not
    write, so they are the only place a recorded digest can be checked against a
    second record rather than against itself. `artifacts/source.py` holds that
    second record, put there by the ingest after it verified the `.npz` it
    converted. Without the cross-check the seeder would hash whatever is in
    `artifacts/soham/` and publish it as the artifact's digest, and every later
    check would then agree with a record derived from bytes nobody checked.
    """
    dest = tmp_path / "repo"
    dest.mkdir()
    for part in ("artifacts", "fixtures", "schema", "src"):
        shutil.copytree(ROOT / part, dest / part,
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))

    def seed() -> subprocess.CompletedProcess:
        subprocess.run(
            [sys.executable, str(dest / "fixtures" / "build.py"),
             "--db", str(dest / "registry.db")],
            check=True, capture_output=True,
        )
        return subprocess.run(
            [sys.executable, str(dest / "artifacts" / "seed.py"),
             "--db", str(dest / "registry.db")],
            capture_output=True, text=True,
        )

    assert seed().returncode == 0, "the untouched copy already fails to seed"

    held = dest / "artifacts" / "soham" / "d_olmo3_lda.safetensors"
    before = held.read_bytes()
    _negate_in_place(held)
    assert held.read_bytes() != before, "the mutation did not land"
    # Same shape, same dtype, same norm: nothing the schema records about this
    # artifact other than its digest has changed.
    assert (next(iter(load_bytes(before).values())).shape
            == next(iter(load_file(held).values())).shape)

    refused = seed()
    assert refused.returncode != 0, (
        "the seeder wrote a provenance claim about bytes it had not identified"
    )
    assert "d_olmo3_lda.safetensors" in refused.stderr
    assert "ingest" in refused.stderr


def test_a_recorded_digest_with_no_bytes_anywhere_is_named(tree):
    """A digest for a file that is not there is a record of nothing."""
    conn = _connect(tree)
    before = conn.execute(
        "SELECT artifact_path FROM intervention WHERE id='iv_bob'"
    ).fetchone()[0]
    conn.execute("UPDATE intervention SET artifact_path=NULL WHERE id='iv_bob'")
    conn.commit()
    try:
        assert _connect(tree).execute(
            "SELECT artifact_path FROM intervention WHERE id='iv_bob'"
        ).fetchone()[0] is None, "the mutation did not land"

        module = _load_falsifier(tree)
        module.check_artifact_digests_match_the_record(_connect(tree))
        assert any("iv_bob" in line for line in module.failures), (
            f"a digest with nothing behind it went unreported: {module.failures}"
        )
    finally:
        restore = _connect(tree)
        restore.execute("UPDATE intervention SET artifact_path=? WHERE id='iv_bob'",
                        (before,))
        restore.commit()
