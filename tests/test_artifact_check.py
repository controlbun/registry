"""A tensor that disagrees with its record is refused, not loaded.

The bytes can come off a CDN at a commit pinned months ago, from a repo somebody
else controls. If what arrives has a different shape than the submission says, it
is not a degraded version of the artifact, it is a different artifact, and every
number on the page describes something else.

The temptation is to warn and carry on, because refusing feels drastic for what is
usually a typo. It is the wrong call here specifically: the whole product is that
published numbers re-derive from raw artifacts, and quietly handing back the wrong
tensor breaks that in the one place nobody looks.

Shape, dtype and the one-artifact rule live here. The content hash lives in
`tests/test_artifact_digest_bite.py`, because it is the check that fires first and
would otherwise stand in front of every case below.

**Run against the real corpus.** These used to be built on a fabricated fixture
that was written and hashed in the same run, so the positive control could only
ever tell you a script agreed with itself. `artifacts/soham/` is committed rather
than regenerated and its digest reaches the database only by matching what the
ingest recorded, which is the version of this check that can fail.
"""

from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest
from safetensors.numpy import save

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from controlbun import artifact, client, db, fetch  # noqa: E402

# One real row, named once. The first of the author's four takes, whose bytes
# are vendored here and whose digest the seeder confirmed against them.
ROW = "iv_soham_meandiff"
VENDORED = ROOT / "artifacts" / "soham" / "d_olmo3_v1.safetensors"
# The residual width of allenai/Olmo-3-1125-32B, which is what the row claims
# and what the bytes have to agree with. Not a measurement: a property of the
# model, cited in `CONTEXT.md` and checked at seed time.
WIDTH = 5120


@pytest.fixture
def conn(tmp_path):
    """The real corpus, seeded into a temporary file.

    `artifacts/seed.py` is the corpus builder since the fixtures were removed.
    It refuses to write a row whose cited shape, dtype, norm or digest the
    vendored bytes contradict, so reaching this fixture at all is already the
    first half of what this file is about.
    """
    path = tmp_path / "registry.db"
    subprocess.run(
        [sys.executable, str(ROOT / "artifacts" / "seed.py"), "--db", str(path)],
        check=True, capture_output=True,
    )
    return db.connect(path)


def _row(conn):
    return conn.execute(
        "SELECT * FROM submission"
        " WHERE author='soham' AND label='pro-human' AND version='meandiff'"
    ).fetchone()


def _submission(conn, monkeypatch, blob: bytes):
    """The author's submission, with whatever bytes we hand it standing in.

    **The recorded digest is cleared first, deliberately.** Every blob below is
    crafted here rather than read off disk, so none of them is the file the
    author published and all of them would be refused on the digest alone, which
    would shadow the checks these cases are about. Clearing it puts each test in
    the state it is actually describing: an artifact this registry points at and
    nobody hashed, where shape and dtype are the whole of the record and have to
    bite on their own. The digest itself is proven in
    `tests/test_artifact_digest_bite.py`.
    """
    conn.execute(
        "UPDATE intervention SET artifact_sha256 = NULL WHERE id=?", (ROW,)
    )
    conn.commit()
    monkeypatch.setattr(fetch, "resolve", lambda **k: blob)
    return client._build(conn, _row(conn))


def test_the_recorded_artifact_loads(conn, monkeypatch):
    """The check must not be so strict that the real artifact fails it.

    The vendored file, with everything the record holds against it, including
    the digest. A positive control built from something other than the artifact
    cannot tell you the artifact loads, which is what an earlier version of this
    did: it handed over a reconstructed `np.arange`, and it passed because shape
    and dtype were the only things compared.
    """
    good = VENDORED.read_bytes()
    recorded = conn.execute(
        "SELECT artifact_sha256 FROM intervention WHERE id=?", (ROW,)
    ).fetchone()[0]
    assert hashlib.sha256(good).hexdigest() == recorded, (
        "the committed artifact is not the file the database was seeded from"
    )

    monkeypatch.setattr(fetch, "resolve", lambda **k: good)
    assert client._build(conn, _row(conn)).vector().shape == (WIDTH,)


def test_a_different_shape_is_refused(conn, monkeypatch):
    wrong = save({"direction": np.arange(16, dtype=np.float32)})
    sub = _submission(conn, monkeypatch, wrong)
    with pytest.raises(client.MismatchedArtifact, match=rf"\[{WIDTH}\].*\[16\]"):
        sub.vector()


def test_a_different_dtype_is_refused(conn, monkeypatch):
    """Right shape, wrong dtype, so the dtype line is the one that has to fire.

    Handing over a tensor that is wrong in two ways would let this pass on the
    shape mismatch while the dtype check did nothing.
    """
    wrong = save({"direction": np.arange(WIDTH, dtype=np.float64)})
    sub = _submission(conn, monkeypatch, wrong)
    with pytest.raises(client.MismatchedArtifact, match="float32.*float64"):
        sub.vector()


def test_a_file_holding_several_tensors_is_refused(conn, monkeypatch):
    """A submission is one artifact.

    Taking the first tensor would work, silently, and pick by whatever order the
    file happens to serialize in.
    """
    many = save({
        "direction": np.arange(WIDTH, dtype=np.float32),
        "other": np.arange(WIDTH, dtype=np.float32),
    })
    sub = _submission(conn, monkeypatch, many)
    with pytest.raises(client.MismatchedArtifact, match="2 tensors"):
        sub.vector()


def test_the_tensor_name_does_not_have_to_match(conn, monkeypatch):
    """Deliberate.

    What the author called the tensor inside their own file is their business. The
    shape and dtype are the contract, because those are what break an application
    silently; a name cannot.
    """
    renamed = save({"whatever_they_called_it": np.arange(WIDTH, dtype=np.float32)})
    assert _submission(conn, monkeypatch, renamed).vector().shape == (WIDTH,)


def test_a_submission_with_nothing_recorded_says_so(conn):
    sub = client._build(conn, _row(conn))
    object.__setattr__(sub, "_artifact_path", None)
    object.__setattr__(sub, "_artifact_repo", None)
    object.__setattr__(sub, "_served_repo", None)
    with pytest.raises(client.NotFound, match="no artifact attached"):
        sub.vector()


def test_shape_notation_is_not_a_disagreement():
    """`[8192]` and `(8192,)` are one shape written two ways.

    `Facts` spells it the way safetensors does and a person reading their own
    record spells it the way numpy does. Comparing the strings made bracket
    style produce the sentence "the artifact and the record have come apart",
    which is a serious claim to make about a comma.
    """
    facts = artifact.Facts(shape="[8192]", dtype="float32", l2_norm=1.0,
                           sha256="0" * 64, size=1)
    for same in ("[8192]", "(8192,)", "8192", " [ 8192 ] "):
        assert artifact.disagreements(artifact.Claim(shape=same), facts) == [], \
            f"{same!r} is the same shape as [8192]"


def test_a_real_shape_difference_still_disagrees():
    facts = artifact.Facts(shape="[8192]", dtype="float32", l2_norm=1.0,
                           sha256="0" * 64, size=1)
    for different in ("[4096]", "(8192, 2)", "[]", "not a shape"):
        assert artifact.disagreements(artifact.Claim(shape=different), facts), \
            f"{different!r} is not the same shape as [8192]"
