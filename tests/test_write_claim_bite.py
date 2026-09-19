"""Proof that write-time validation bites, and that it is one comparison.

The defect: two scripts put tensor facts into the `intervention` table by typing
them, `artifacts/seed.py:189-190` and `fixtures/build.py:175-176`. The values
were right. The mechanism was that somebody had been careful, sitting in the
same `INSERT` as one field that was derived from the bytes, and nothing compared
the other three against anything at all.

Every test below is written the way `tests/test_scan_gap_bite.py` and
`tests/test_artifact_digest_bite.py` are, because "the new check passes" proves
nothing on its own. What has to be shown is that the probe goes **unnoticed**
under the old behavior and is caught under the new one, and every mutation is
asserted to have landed before its result is believed. This repository has
produced a green-while-checking-nothing result seven times, three of them in
bite tests.

The two halves that matter, and they are different arguments:

  * A wrong shape on a row whose bytes are in this repository lands in the
    database and on a page, and the falsifier then catches it by disagreeing
    with a row that is already published. Late, not silent.
  * A wrong shape on a **pointer-only** row is caught by nothing, ever. The
    falsifier cannot fetch it, and the client compares arriving bytes *against*
    the record, so the record being wrong makes the client refuse the author's
    own artifact and name their bytes as the substitution. That one is in
    `test_a_pointer_only_row_...` and is the case this exists for.

Tensors here are obviously synthetic ramps and one negation of a committed
fixture. Nothing in this file is a measurement and nothing reads one.
"""

from __future__ import annotations

import hashlib
import importlib.util
import re
import shutil
import sqlite3
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest
from safetensors.numpy import load as load_bytes
from safetensors.numpy import save

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from registry import artifact, client, db, fetch  # noqa: E402

ALICE = ROOT / "fixtures" / "alice_kindness_v1.safetensors"

# Eight float32 elements that are not alice's eight, and sixteen that are not
# any of them. Both are integer ramps, the same shape of stand-in the rest of
# the fixture corpus uses so that one leaking anywhere real is obvious on sight.
SUBSTITUTE = save({"direction": np.arange(8, 0, -1, dtype=np.float32)})
WRONG_LENGTH = save({"direction": np.arange(16, dtype=np.float32)})


@pytest.fixture
def conn(tmp_path):
    path = tmp_path / "claims.db"
    subprocess.run(
        [sys.executable, str(ROOT / "fixtures" / "build.py"), "--db", str(path)],
        check=True, capture_output=True,
    )
    return db.connect(path)


def _blob() -> bytes:
    """alice's committed artifact, read rather than reconstructed.

    `DECISIONS.md` 2026-09-16 records the incidental finding that a positive
    control in `tests/test_artifact_check.py` was built from a reconstructed
    `np.arange(8)` and was therefore testing bytes that were never the artifact.
    Same trap, avoided the same way.
    """
    return ALICE.read_bytes()


def _tensor(blob: bytes):
    return next(iter(load_bytes(blob).values()))


# --------------------------------------------------------------------------- #
# 1. A wrong claim is refused, and both sides are named.


def test_a_wrong_shape_claim_is_refused():
    blob = _blob()
    assert str(list(_tensor(blob).shape)) == "[8]", "the fixture is not [8]"

    with pytest.raises(artifact.MismatchedArtifact) as caught:
        artifact.confirmed(blob, artifact.Claim(shape="[16]"), subject="probe")

    # Both sides, or the error tells whoever reads it nothing actionable.
    assert "[16]" in str(caught.value) and "[8]" in str(caught.value)
    assert "probe" in str(caught.value)


def test_a_wrong_dtype_claim_is_refused():
    with pytest.raises(artifact.MismatchedArtifact, match="float64.*float32"):
        artifact.confirmed(_blob(), artifact.Claim(dtype="float64"),
                           subject="probe")


def test_a_wrong_digest_claim_is_refused_before_the_parser_runs():
    """Ordering, the way `artifacts/ingest_arena.py` established it.

    Bytes that are not a safetensors file at all come back as a digest
    mismatch, not as whatever the parser raises. If the parse ran first, a
    hostile file would reach it before anything had established the bytes are
    the ones being claimed about.
    """
    claim = artifact.Claim(sha256=hashlib.sha256(_blob()).hexdigest())
    with pytest.raises(artifact.MismatchedArtifact, match="sha256"):
        artifact.confirmed(b"not a safetensors file at all", claim,
                           subject="probe")


def test_a_file_holding_several_tensors_is_refused():
    many = save({"direction": np.arange(8, dtype=np.float32),
                 "other": np.arange(8, dtype=np.float32)})
    with pytest.raises(artifact.MismatchedArtifact, match="2 tensors"):
        artifact.confirmed(many, subject="probe")


def test_every_wrong_field_is_named_at_once():
    """A record with two things wrong gets fixed twice if the error names one."""
    with pytest.raises(artifact.MismatchedArtifact) as caught:
        artifact.confirmed(
            WRONG_LENGTH,
            artifact.Claim(shape="[8]", dtype="float64", l2_norm=0.5),
            subject="probe",
        )
    message = str(caught.value)
    assert "[16]" in message, "the shape mismatch is missing"
    assert "float64" in message, "the dtype mismatch is missing"
    assert "L2 norm" in message, "the norm mismatch is missing"


# --------------------------------------------------------------------------- #
# 2. The norm has a tolerance and the digest does not, and both are load-bearing.


def test_a_norm_within_tolerance_is_accepted_and_one_outside_it_is_not():
    """Derived from the artifact rather than typed, so neither probe is invented.

    A digest has one right answer. A norm is derived at both ends and the two
    ends can derive it differently, which is the whole reason there is a number
    in `artifact.L2_TOLERANCE` and a comment above it saying where it came from.
    """
    blob = _blob()
    derived = float(np.linalg.norm(_tensor(blob)))

    inside = derived + artifact.L2_TOLERANCE / 2
    outside = derived + artifact.L2_TOLERANCE * 10
    assert inside != derived and outside != derived, "the probes are not probes"

    assert artifact.confirmed(
        blob, artifact.Claim(l2_norm=inside), subject="probe"
    ).l2_norm == inside

    with pytest.raises(artifact.MismatchedArtifact, match="L2 norm"):
        artifact.confirmed(blob, artifact.Claim(l2_norm=outside),
                           subject="probe")


def test_the_norm_tolerance_stays_inside_what_a_published_figure_can_hide():
    """A tolerance is a place to put a difference, so it gets bounds.

    Every test above states its probe as a multiple of `L2_TOLERANCE`, which is
    how they avoid hardcoding it and also how widening it by a thousand would
    slide past all of them together. So the constant itself is bounded here,
    and both bounds come from one fact: every measurement this project
    publishes renders through `.toFixed(4)`, which is what
    `falsifier/verify.py`'s `PUBLISHED_NUMBER` reads back off a page.

    Lower, half of the last rendered digit. A value transcribed from a page is
    only knowable to 5e-5, and a tolerance under that would refuse a citation
    that is as accurate as the thing it was cited from.

    Upper, one whole rendered digit. Anything larger lets a norm disagree in
    the fourth decimal, render as a visibly different number, and be recorded
    as agreeing anyway.
    """
    assert 5e-5 <= artifact.L2_TOLERANCE <= 1e-4, (
        f"L2_TOLERANCE is {artifact.L2_TOLERANCE}. Outside this band it is "
        "either refusing accurate citations or accepting a difference a reader "
        "can see on the page. Widen it only with a reason written down."
    )


def test_the_tolerance_is_the_one_the_falsifier_applies(conn):
    """One constant, because two would let a row pass one gate and fail the next.

    Asserted through the falsifier rather than by reading its source. A stored
    norm half a tolerance off the tensor has to go unreported and one ten
    tolerances off has to be named, which pins the falsifier to
    `artifact.L2_TOLERANCE` and not to a copy of the same digits.
    """
    derived = float(np.linalg.norm(_tensor(_blob())))

    for offset, expected in ((artifact.L2_TOLERANCE / 2, False),
                             (artifact.L2_TOLERANCE * 10, True)):
        stored = derived + offset
        conn.execute("UPDATE intervention SET l2_norm=? WHERE id='iv_alice'",
                     (stored,))
        conn.commit()
        assert conn.execute(
            "SELECT l2_norm FROM intervention WHERE id='iv_alice'"
        ).fetchone()[0] == stored, "the mutation did not land"

        module = _falsifier()
        module.check_artifacts_match_their_metadata(conn)
        named = any("iv_alice" in line for line in module.failures)
        assert named is expected, (
            f"a stored norm {offset} from the tensor was "
            f"{'ignored' if expected else 'reported'}: {module.failures}"
        )


# --------------------------------------------------------------------------- #
# 3. A caller with nothing to claim gets the derived value, and is not refused.


def test_claiming_nothing_derives_everything_and_refuses_nothing():
    """Absence is a state here as everywhere else.

    A write path that demanded a claim before it would hand back facts would be
    a required field wearing a function signature, which is the shape every
    quality gate in this project arrives in.
    """
    blob = _blob()
    facts = artifact.confirmed(blob, subject="probe")

    assert facts.shape == "[8]"
    assert facts.dtype == "float32"
    assert facts.sha256 == hashlib.sha256(blob).hexdigest()
    assert facts.l2_norm == float(np.linalg.norm(_tensor(blob)))
    assert facts.tensor is not None, "the parse was thrown away and redone later"


def test_a_partial_claim_checks_what_it_claims_and_derives_the_rest():
    blob = _blob()
    facts = artifact.confirmed(blob, artifact.Claim(dtype="float32"),
                               subject="probe")
    assert facts.dtype == "float32"
    assert facts.shape == "[8]", "an unclaimed field came back empty"
    assert facts.l2_norm is not None


# --------------------------------------------------------------------------- #
# 4. The claim is checked, not replaced. This is the half that is easy to invert.


def test_a_claim_that_survives_the_check_is_what_gets_recorded():
    """A recomputation over the top would throw the agreement away.

    `artifacts/seed.py` records 1.0 because that is the cited value. Read as
    float64 the vendored file norms to slightly more than that, and the row
    being worth anything depends on the citation and the bytes agreeing rather
    than on the column holding whatever the bytes happen to say.
    """
    blob = _blob()
    derived = float(np.linalg.norm(_tensor(blob)))
    cited = derived + artifact.L2_TOLERANCE / 2
    assert cited != derived, "the claim and the derived value are the same number"

    facts = artifact.confirmed(blob, artifact.Claim(l2_norm=cited),
                               subject="probe")
    assert facts.l2_norm == cited, (
        "the function recomputed over the claim instead of checking it, which "
        "destroys the provenance the claim carried"
    )
    assert facts.l2_norm != derived


def test_the_writers_record_the_cited_values_rather_than_recomputed_ones(conn):
    """Same property, end to end through `fixtures/build.py`.

    erik's and fern's fixtures norm to slightly under 1.0 in float32 because
    unit-normalizing in float64 and casting down does not land on exactly one.
    The rows say 1.0, which is what `write_vector` claims to produce.
    """
    stored = dict(conn.execute("SELECT id, l2_norm FROM intervention").fetchall())
    assert stored, "no rows, so this proves nothing"

    erik = float(np.linalg.norm(
        _tensor((ROOT / "fixtures" / "erik_refusal_v1.safetensors").read_bytes())
    ))
    assert erik != 1.0, "the fixture norms to exactly 1.0; the probe is vacuous"
    assert stored["iv_erik"] == 1.0, (
        "the build recorded the recomputed norm instead of the claim it checked"
    )


# --------------------------------------------------------------------------- #
# 5. One comparison. Break it once and every caller goes blind together.


def _falsifier(root: Path = ROOT):
    spec = importlib.util.spec_from_file_location(
        "write_claim_probed_falsifier", ROOT / "falsifier" / "verify.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.ROOT = root
    module.failures = []
    return module


def _submission(conn, monkeypatch, blob: bytes):
    monkeypatch.setattr(fetch, "resolve", lambda **k: blob)
    row = conn.execute(
        "SELECT * FROM submission WHERE author='alice' AND label='kindness'"
    ).fetchone()
    return client._build(conn, row)


def test_the_read_path_the_write_path_and_the_falsifier_share_one_comparison(
    conn, monkeypatch
):
    """Blind one function and all three stop noticing. That is the proof.

    This project has shipped the same question answered in two places twice:
    `pairwise` against the matrix built beside it, and the two `<head>` blocks.
    Both drifted. Asserting that three callers import the same name proves
    nothing, because an import can sit there unused. Removing the shared
    comparison and watching all three go quiet proves they were using it.
    """
    # Each of the three notices its own probe first, or the patch below is
    # unfalsifiable.
    with pytest.raises(artifact.MismatchedArtifact):
        artifact.confirmed(_blob(), artifact.Claim(shape="[16]"), subject="write")
    with pytest.raises(client.MismatchedArtifact):
        _submission(conn, monkeypatch, SUBSTITUTE).vector()
    before = artifact.disagreements(
        artifact.Claim(shape="[16]"), artifact.facts_of(_tensor(_blob()))
    )
    assert before, "the comparison reported nothing before it was patched"

    monkeypatch.setattr(artifact, "disagreements", lambda claim, facts: [])
    assert artifact.disagreements(
        artifact.Claim(shape="[16]"), artifact.facts_of(_tensor(_blob()))
    ) == [], "the patch did not land"

    # The write path, blind.
    assert artifact.confirmed(
        _blob(), artifact.Claim(shape="[16]"), subject="write"
    ).shape == "[16]", "the write path does not route through the comparison"

    # The read path, blind, on bytes it refused two lines ago.
    assert _submission(conn, monkeypatch, SUBSTITUTE).vector().shape == (8,), (
        "the read path does not route through the comparison"
    )

    # And the falsifier, blind, against a stored shape that contradicts the file.
    module = _falsifier()
    conn.execute("UPDATE intervention SET shape='[4096]' WHERE id='iv_alice'")
    conn.commit()
    assert conn.execute(
        "SELECT shape FROM intervention WHERE id='iv_alice'"
    ).fetchone()[0] == "[4096]", "the mutation did not land"
    module.check_artifacts_match_their_metadata(conn)
    assert module.failures == [], (
        f"the falsifier does not route through the comparison: {module.failures}"
    )


def test_the_falsifier_still_catches_that_shape_unpatched(conn):
    """The control for the test above: unpatched, the same mutation is named."""
    conn.execute("UPDATE intervention SET shape='[4096]' WHERE id='iv_alice'")
    conn.commit()
    assert conn.execute(
        "SELECT shape FROM intervention WHERE id='iv_alice'"
    ).fetchone()[0] == "[4096]", "the mutation did not land"

    module = _falsifier()
    module.check_artifacts_match_their_metadata(conn)
    assert any("iv_alice" in line for line in module.failures), (
        f"a stored shape contradicting the tensor went unreported: {module.failures}"
    )


# --------------------------------------------------------------------------- #
# 6. The probe that matters: the claim nothing downstream can catch.


def test_a_pointer_only_row_with_a_wrong_shape_is_caught_by_nothing_downstream(
    conn, monkeypatch
):
    """The case write-time validation exists for, reproduced in full.

    A row that points at somebody else's repository has no bytes here. The
    falsifier skips it, because it is offline by design and cannot fetch. The
    client does look at bytes, but it compares them **against the record**, so a
    record that is wrong does not get corrected by the comparison; it gets
    enforced. The author's own artifact arrives and is named as the wrong one.

    So the wrong value is written once, by hand, and from then on every check
    agrees with it. There is no later gate that reaches this. The only moment it
    can be caught is the moment it is written, which is what `artifact.confirmed`
    now occupies.
    """
    good = _blob()

    # Written the way both seeds used to write: the tensor facts typed straight
    # into the INSERT, with one digit wrong.
    conn.execute(
        "INSERT INTO submission (author,model_id,label,version,definition,"
        "created_at,is_synthetic) VALUES ('nadia','placeholder/does-not-resolve-1b',"
        "'kindness','v1','pointed at, not held','2026-09-17',1)"
    )
    conn.execute(
        "INSERT INTO intervention (id,author,label,version,kind,model_id,layer,"
        "layer_convention,hook_point,shape,dtype,l2_norm,artifact_repo,"
        "artifact_commit,is_synthetic) VALUES ('iv_nadia','nadia','kindness',"
        "'v1','direction','placeholder/does-not-resolve-1b',4,'block-0indexed',"
        "'resid_post','[16]','float32',1.0,'someone/else',?,1)",
        ("c" * 40,),
    )
    conn.commit()
    assert conn.execute(
        "SELECT shape FROM intervention WHERE id='iv_nadia'"
    ).fetchone()[0] == "[16]", "the wrong row did not land"

    # The falsifier: silent about it, and not silent in general. Both checks,
    # because between them they are everything this repository re-derives.
    module = _falsifier()
    module.check_artifacts_match_their_metadata(conn)
    module.check_artifact_digests_match_the_record(conn)
    assert not any("iv_nadia" in line for line in module.failures), (
        f"the falsifier reached a pointer-only row after all: {module.failures}"
    )
    assert module.failures == [], (
        f"the copy was already failing, so the silence above means nothing: "
        f"{module.failures}"
    )

    # The client: hands back the author's correct bytes? No. It refuses them,
    # and names them as the thing that is wrong.
    monkeypatch.setattr(fetch, "resolve", lambda **k: good)
    path = conn.execute("PRAGMA database_list").fetchone()[2]
    with pytest.raises(client.MismatchedArtifact) as caught:
        client.load("nadia/kindness@v1", database=path).vector()
    assert "[16]" in str(caught.value) and "[8]" in str(caught.value), (
        "the refusal does not name both sides"
    )

    # And the same claim, offered to the write path, never becomes a row.
    with pytest.raises(artifact.MismatchedArtifact):
        artifact.confirmed(good, artifact.Claim(shape="[16]", dtype="float32",
                                                l2_norm=1.0),
                           subject="nadia/kindness@v1")


# --------------------------------------------------------------------------- #
# 7. Both writers go through it, and the old mechanism is reproduced beside them.


WRITERS = {
    "fixtures/build.py": ROOT / "fixtures" / "build.py",
    "artifacts/seed.py": ROOT / "artifacts" / "seed.py",
}


def _intervention_insert(path: Path) -> str:
    """The `INSERT INTO intervention` statement, as source text.

    Sliced to the next `INSERT INTO recipe`, which both writers have and which
    is the statement immediately after. If either stops having one this raises
    rather than returning a slice that happens to be empty, because a
    source-reading check that finds nothing is the failure mode this repository
    keeps producing.
    """
    text = path.read_text()
    start = text.index("INSERT INTO intervention")
    end = text.index("INSERT INTO recipe", start)
    region = text[start:end]
    assert len(region) > 400, (
        f"{path.name}: the slice is too small to be the statement, so this "
        "check is reading nothing"
    )
    return region


def test_no_writer_types_a_tensor_fact_into_the_intervention_insert():
    """The defect as a rule, rather than as the two instances it was found in.

    Both halves are needed and neither is sufficient. Checking the bytes and
    then writing a separately typed literal next to the result gets the
    refusal and keeps the transcription, and two copies of one fact are two
    copies that come apart. Writing `facts.shape` while nothing confirmed it
    is the mirror of that.

    A behavioral test cannot see this, which is why it is a source read: with
    the claim correct, a writer that types the same value produces exactly the
    same row, and only diverges later when one of the two copies is edited.
    """
    for name, path in WRITERS.items():
        region = _intervention_insert(path)
        for attribute in ("facts.shape", "facts.dtype", "facts.l2_norm",
                          "facts.sha256"):
            assert attribute in region, (
                f"{name} no longer supplies {attribute} to the row it writes, "
                "so whatever goes into that column was not compared against "
                "the artifact"
            )
        typed = re.findall(r'"\[\d+\]"|"(?:float|bfloat|int|uint)\d+"', region)
        assert not typed, (
            f"{name} types a tensor fact straight into the row: {typed}. That "
            "is the defect: a value nothing compared against the bytes, "
            "sitting in the same statement as values that were."
        )


def _copy(tmp_path: Path) -> Path:
    dest = tmp_path / "repo"
    dest.mkdir()
    for part in ("artifacts", "falsifier", "fixtures", "schema", "src"):
        shutil.copytree(ROOT / part, dest / part,
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    return dest


def _run(script: Path, dest: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(script), "--db", str(dest / "registry.db")],
        capture_output=True, text=True,
    )


def _patch(path: Path, old: str, new: str) -> None:
    text = path.read_text()
    assert old in text, f"{path.name} no longer contains {old!r}; the probe is stale"
    path.write_text(text.replace(old, new, 1))
    assert new in path.read_text(), "the mutation did not land"


def test_the_fixture_build_refuses_a_claim_its_own_bytes_contradict(tmp_path):
    dest = _copy(tmp_path)
    assert _run(dest / "fixtures" / "build.py", dest).returncode == 0, (
        "the untouched copy already fails to build"
    )

    _patch(dest / "fixtures" / "build.py",
           'artifact.Claim(shape=f"[{DIM}]", dtype="float32", l2_norm=1.0)',
           'artifact.Claim(shape="[16]", dtype="float32", l2_norm=1.0)')

    refused = _run(dest / "fixtures" / "build.py", dest)
    assert refused.returncode != 0, (
        "the build wrote a shape its own vectors contradict"
    )
    assert "[16]" in refused.stderr and "[8]" in refused.stderr


def test_the_same_wrong_shape_entered_the_database_under_the_old_mechanism(
    tmp_path
):
    """The half that matters, and the only honest way to show it.

    The old code read `f"[{DIM}]", "float32", 1.0` in the `INSERT` tuple with
    nothing reading the file. Reproduced here literally, by putting a typed
    value back where the derived one now goes: the build succeeds, the row is
    in the database, and it is wrong.

    Not "silent forever": for a row whose bytes are in this repository the
    falsifier does catch this, on the next run, against a row that already
    exists. Silent forever is the pointer-only case above. What this shows is
    the mechanism the defect described, that a typed fact reaches the record
    without anything comparing it to the artifact.
    """
    dest = _copy(tmp_path)
    _patch(dest / "fixtures" / "build.py",
           '"block-0indexed", hook, facts.shape, facts.dtype,',
           '"block-0indexed", hook, "[16]", facts.dtype,')

    built = _run(dest / "fixtures" / "build.py", dest)
    assert built.returncode == 0, (
        f"the old mechanism failed, so it was never the silent one: {built.stderr}"
    )

    conn = sqlite3.connect(dest / "registry.db")
    shapes = {r[0] for r in conn.execute("SELECT shape FROM intervention")}
    conn.close()
    assert shapes == {"[16]"}, (
        f"the typed value did not reach the database, so this proves nothing: "
        f"{shapes}"
    )


def test_the_seed_refuses_a_cited_claim_the_vendored_bytes_contradict(tmp_path):
    """`artifacts/seed.py`, whose three claims are citations rather than guesses.

    `tests/test_artifact_digest_bite.py` already moves the bytes under a fixed
    claim. This moves the claim under fixed bytes, which is the other direction
    and the one that was unchecked for shape, dtype and norm.
    """
    dest = _copy(tmp_path)
    assert _run(dest / "fixtures" / "build.py", dest).returncode == 0
    assert _run(dest / "artifacts" / "seed.py", dest).returncode == 0, (
        "the untouched copy already fails to seed"
    )

    _patch(dest / "artifacts" / "seed.py",
           'CITED = artifact.Claim(shape="[5120]", dtype="float32", l2_norm=1.0)',
           'CITED = artifact.Claim(shape="[4096]", dtype="float32", l2_norm=1.0)')

    assert _run(dest / "fixtures" / "build.py", dest).returncode == 0
    refused = _run(dest / "artifacts" / "seed.py", dest)
    assert refused.returncode != 0, (
        "the seeder published a shape the vendored tensor contradicts"
    )
    assert "[4096]" in refused.stderr and "[5120]" in refused.stderr
    assert "d_olmo3" in refused.stderr, "the refusal does not name the file"
    assert "ingest" in refused.stderr, (
        "the refusal no longer points at the step that would explain it"
    )
