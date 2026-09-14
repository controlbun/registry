"""A tensor that disagrees with its record is refused, not loaded.

The bytes can come off a CDN at a commit pinned months ago, from a repo somebody
else controls. If what arrives has a different shape than the submission says, it
is not a degraded version of the artifact, it is a different artifact, and every
number on the page describes something else.

The temptation is to warn and carry on, because refusing feels drastic for what is
usually a typo. It is the wrong call here specifically: the whole product is that
published numbers re-derive from raw artifacts, and quietly handing back the wrong
tensor breaks that in the one place nobody looks.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest
from safetensors.numpy import save

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from registry import client, db, fetch  # noqa: E402


@pytest.fixture
def conn(tmp_path):
    path = tmp_path / "fixture.db"
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


def test_the_recorded_artifact_loads(conn, monkeypatch):
    """The check must not be so strict that the real fixture fails it."""
    good = save({"direction": np.arange(8, dtype=np.float32)})
    assert _submission(conn, monkeypatch, good).vector().shape == (8,)


def test_a_different_shape_is_refused(conn, monkeypatch):
    wrong = save({"direction": np.arange(16, dtype=np.float32)})
    sub = _submission(conn, monkeypatch, wrong)
    with pytest.raises(client.MismatchedArtifact, match=r"\[8\].*\[16\]"):
        sub.vector()


def test_a_different_dtype_is_refused(conn, monkeypatch):
    wrong = save({"direction": np.arange(8, dtype=np.float64)})
    sub = _submission(conn, monkeypatch, wrong)
    with pytest.raises(client.MismatchedArtifact, match="float32.*float64"):
        sub.vector()


def test_a_file_holding_several_tensors_is_refused(conn, monkeypatch):
    """A submission is one artifact.

    Taking the first tensor would work, silently, and pick by whatever order the
    file happens to serialize in.
    """
    many = save({
        "direction": np.arange(8, dtype=np.float32),
        "other": np.arange(8, dtype=np.float32),
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
    renamed = save({"whatever_they_called_it": np.arange(8, dtype=np.float32)})
    assert _submission(conn, monkeypatch, renamed).vector().shape == (8,)


def test_a_submission_with_nothing_recorded_says_so(conn, monkeypatch):
    row = conn.execute(
        "SELECT * FROM submission WHERE author='alice' AND label='kindness'"
    ).fetchone()
    sub = client._build(conn, row)
    object.__setattr__(sub, "_artifact_path", None)
    object.__setattr__(sub, "_artifact_repo", None)
    object.__setattr__(sub, "_served_repo", None)
    with pytest.raises(client.NotFound, match="no artifact attached"):
        sub.vector()
