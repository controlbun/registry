"""Proof that the general ingest path bites, and where it bites harder than before.

`artifacts/ingest_arena.py` was three quarters of an ingest welded to one commit
in one repository. Generalizing it is only worth anything if the checks survived
the move, so every one of them is probed here the way `tests/test_scan_gap_bite.py`
and `tests/test_write_claim_bite.py` do it: the mutation is asserted to have
landed before its result is believed, and where the old behavior can be
reproduced the probe is shown to go **unnoticed** under it.

That discipline is not decoration. This repository has produced a
green-while-checking-nothing result nine times, including three bite tests that
mutated nothing, a positive control built from bytes that were never the
artifact, and two probes a thousandfold widening slid past.

The three that matter, in order:

  * **Bytes that do not match their claimed digest never reach a parser.** Not
    "are refused": never reach it. A converter that runs on unidentified bytes
    has already lost, whatever it does afterwards, so the probe watches the
    converter rather than the exception.
  * **A pickle-bearing input is refused rather than loaded.** Proved with a
    pickle that records having run. Under `allow_pickle=True` it runs. Under
    what ships it does not, and the caller gets a sentence explaining why.
  * **A conversion whose output drifts is caught rather than silently
    re-recorded**, and the artifact already on disk is not replaced by the
    bytes that failed. The old shape wrote first and compared second, so it
    reported the drift accurately and had already destroyed the good copy.

Every tensor here is an obviously synthetic integer ramp. Nothing in this file
is a measurement and nothing reads one.
"""

from __future__ import annotations

import hashlib
import http.server
import io
import pickle
import shutil
import socket
import subprocess
import sys
import threading
import zipfile
from json import dumps as json_dumps
from pathlib import Path

import numpy as np
import pytest
from safetensors.numpy import load as load_bytes
from safetensors.numpy import load_file, save, save_file

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from controlbun import artifact, fetch, ingest  # noqa: E402
from controlbun.artifact import Claim, sort_header  # noqa: E402

sys.path.insert(0, str(ROOT / "artifacts"))

from source import DIRECTIONS  # noqa: E402

# Eight float32 elements, ascending, and eight that are not those. The same
# stand-in shape the rest of the corpus uses, so one leaking anywhere real is
# obvious on sight rather than plausible.
RAMP = np.arange(1, 9, dtype=np.float32)
OTHER = np.arange(8, 0, -1, dtype=np.float32)

BLOB = save({"direction": RAMP})
SUBSTITUTE = save({"direction": OTHER})

BLOB_SHA = hashlib.sha256(BLOB).hexdigest()


def _npz(**arrays) -> bytes:
    buffer = io.BytesIO()
    np.savez(buffer, **arrays)
    return buffer.getvalue()


def _local(blob: bytes, sha: str | None = None) -> ingest.LocalBytes:
    return ingest.LocalBytes(blob=blob, origin="a probe", sha256=sha)


# --------------------------------------------------------------------------- #
# 0. Controls. Several tests below mean nothing if these are not true.


def test_the_vendored_artifacts_are_the_bytes_the_ingest_table_records():
    """The requirement the generalization had to not break, asserted directly.

    `artifacts/source.py` records a sha256 for each `.safetensors` the ingest
    wrote. If a refactor changes the conversion by so much as a header key,
    these move, and the right response is to find out why rather than to
    re-record them.
    """
    for npz_name, _npz_sha, out_sha in DIRECTIONS:
        path = ROOT / "artifacts" / "soham" / npz_name.replace(".npz",
                                                               ".safetensors")
        assert path.exists(), f"{path} is missing, so this control is vacuous"
        assert hashlib.sha256(path.read_bytes()).hexdigest() == out_sha, (
            f"{path.name} is not the file the ingest recorded. Something moved; "
            "do not re-record the digest until you know which of the two it was"
        )


def test_the_arena_check_runs_offline_and_passes():
    """`make site` calls this. A copy that already fails proves nothing below."""
    done = subprocess.run(
        [sys.executable, str(ROOT / "artifacts" / "ingest_arena.py"), "--check"],
        capture_output=True, text=True,
    )
    assert done.returncode == 0, done.stdout + done.stderr
    assert done.stdout.count("ok") == len(DIRECTIONS)


# The four `source_*` fields come from the pin rather than from the payload, so
# they are the ones this round-trip cannot supply and has to exclude.
FROM_THE_PIN = {"source_repo", "source_commit", "source_path", "source_sha256"}


def test_the_arena_payload_still_produces_the_header_it_produced(monkeypatch):
    """The gap the offline gate otherwise has, closed without the network.

    `--check` compares the committed files against their recorded digests, so
    it proves the bytes on disk are the bytes that were written and says
    nothing at all about whether rerunning the conversion would write them
    again. Change a header key in `arena_payload` and every offline check stays
    green until somebody runs the ingest with network months later.

    So the conversion is run against a reconstruction of its own input: the
    tensor out of the committed file, and a `meta` blob rebuilt from the fields
    that file records. What comes back has to be the header the file already
    carries. A dropped key, an added key, a renamed source field, a changed
    literal or a changed separator all move it.
    """
    from ingest_arena import arena_payload  # noqa: PLC0415

    for npz_name, _npz_sha, _out_sha in DIRECTIONS:
        path = ROOT / "artifacts" / "soham" / npz_name.replace(".npz",
                                                               ".safetensors")
        blob = path.read_bytes()
        committed = artifact.metadata_of(blob)
        assert committed, f"{path.name} carries no header, so this is vacuous"

        meta = {
            "model_id": committed["model_id"],
            "layer": int(committed["layer"]),
            "extraction_method": committed["extraction_method"],
            "confounds_removed": committed["confounds_removed"].split(","),
            "num_pairs": int(committed["num_pairs"]),
            "d_version": committed["author_d_version"],
            "created_at": committed["extracted_at"],
        }
        produced = arena_payload(ingest.Parsed(arrays={
            "d": next(iter(load_bytes(blob).values())),
            "meta": np.array(json_dumps(meta)),
        }))

        assert produced.name == "d", (
            "the tensor key changed, so a rerun writes a different file"
        )
        assert produced.metadata == {
            key: value for key, value in committed.items()
            if key not in FROM_THE_PIN
        }, (
            f"{path.name}: rerunning the conversion would write a different "
            "header from the one the committed file carries. The recorded "
            "sha256 is about to stop reproducing"
        )
        assert set(committed) - set(produced.metadata) == FROM_THE_PIN, (
            "the provenance fields the pin supplies are not the four expected"
        )


def test_the_arena_conversion_still_refuses_what_seed_py_cites_it_for():
    """`artifacts/seed.py` records `[5120]` and `float32` partly because of this.

    Its comment says the ingest refuses anything that is not a 1-D float32
    array, "so this is the conversion's own contract", and a cited claim whose
    citation stopped being true is worse than an uncited one. The contract
    belongs to this corpus and not to the registry, which holds kinds of
    artifact nobody has named yet.
    """
    from ingest_arena import arena_payload  # noqa: PLC0415

    meta = np.array(json_dumps({
        "model_id": "placeholder/does-not-resolve-1b", "layer": 4,
        "extraction_method": "a probe", "confounds_removed": [],
        "num_pairs": 0, "d_version": "v0", "created_at": "2026-09-17",
    }))
    for wrong in (RAMP.astype(np.float64), RAMP.reshape(2, 4)):
        with pytest.raises(SystemExit, match="1-D float32"):
            arena_payload(ingest.Parsed(arrays={"d": wrong, "meta": meta}))

    assert arena_payload(
        ingest.Parsed(arrays={"d": RAMP, "meta": meta})
    ).tensor.tolist() == RAMP.tolist(), "the control refuses too, so this is inert"


# --------------------------------------------------------------------------- #
# 1. The digest is compared before a parser touches the bytes.


class _Spy:
    """A converter that records having been reached, and reads nothing.

    Installed over `FORMATS`, which is also the only honest way to prove the
    dict is consulted at call time rather than captured at import.
    """

    def __init__(self):
        self.calls = 0

    def read(self, blob: bytes) -> ingest.Parsed:
        self.calls += 1
        return ingest.Parsed(arrays={"direction": RAMP})

    def install(self, monkeypatch):
        monkeypatch.setattr(ingest, "FORMATS", {
            "spy": ingest.Format(sniff=lambda blob: True, read=self.read,
                                 note="a probe, reads nothing"),
        })
        return self


def test_bytes_that_contradict_their_digest_never_reach_a_parser(monkeypatch,
                                                                 tmp_path):
    spy = _Spy().install(monkeypatch)
    assert hashlib.sha256(SUBSTITUTE).hexdigest() != BLOB_SHA, (
        "the substitute hashes to the claimed digest, so it is not a substitute"
    )

    with pytest.raises(artifact.MismatchedArtifact) as caught:
        ingest.ingest(_local(SUBSTITUTE, BLOB_SHA), out="probe.safetensors",
                      subject="probe", root=tmp_path)

    # Both sides named, or the error tells whoever reads it nothing actionable.
    assert BLOB_SHA in str(caught.value)
    assert hashlib.sha256(SUBSTITUTE).hexdigest() in str(caught.value)
    assert spy.calls == 0, (
        "the converter ran on bytes nothing had identified. Being refused "
        "afterwards is not the property: the parser is the first code to touch "
        "a file somebody else's server sent, and it does not get to go first"
    )
    assert not list(tmp_path.iterdir()), (
        f"a refused ingest left something behind: {list(tmp_path.iterdir())}"
    )


def test_the_same_bytes_reach_the_parser_once_the_digest_check_is_removed(
    monkeypatch, tmp_path
):
    """The half that matters: the ordering is what stops it, not luck.

    With the digest comparison neutered the substituted bytes go straight into
    the converter, which is the behavior every path here had before
    `artifacts/ingest_arena.py` put the check in front of the parse.
    """
    spy = _Spy().install(monkeypatch)
    monkeypatch.setattr(ingest, "confirm_digest",
                        lambda blob, claim=Claim(), *, subject: "")
    assert ingest.confirm_digest(b"", subject="x") == "", "the patch did not land"

    ingest.ingest(_local(SUBSTITUTE, BLOB_SHA), out="probe.safetensors",
                  subject="probe", root=tmp_path)
    assert spy.calls == 1, (
        "the converter did not run even with the check removed, so the test "
        "above was never observing the ordering"
    )


def test_the_source_refuses_through_the_one_comparison_rather_than_its_own(
    monkeypatch
):
    """Blind `disagreements` and the source goes quiet with everything else.

    Asserting that a caller imports a name proves nothing, because an import
    can sit unused beside a hand-rolled `if got != expected`. Removing the
    shared comparison and watching the source stop noticing proves it was
    using it. This repository has shipped one question answered in two places
    twice, `pairwise` against the matrix and the two `<head>` blocks, and both
    copies drifted.
    """
    with pytest.raises(artifact.MismatchedArtifact):
        _local(SUBSTITUTE, BLOB_SHA).read()
    assert artifact.disagreements(
        Claim(sha256=BLOB_SHA), artifact.Facts(sha256="0" * 64)
    ), "the comparison reported nothing before it was patched"

    monkeypatch.setattr(artifact, "disagreements", lambda claim, facts: [])
    assert artifact.disagreements(
        Claim(sha256=BLOB_SHA), artifact.Facts(sha256="0" * 64)
    ) == [], "the patch did not land"

    assert _local(SUBSTITUTE, BLOB_SHA).read() == SUBSTITUTE, (
        "the source keeps its own copy of the digest comparison, which is the "
        "thing consolidating these was supposed to end"
    )
    assert artifact.confirmed(SUBSTITUTE, Claim(sha256=BLOB_SHA),
                              subject="probe").shape == "[8]", (
        "the parsed-file check does not route through the same comparison"
    )


def test_a_source_claiming_no_digest_is_read_rather_than_refused(tmp_path):
    """Absence is a state here as everywhere else.

    A path that demanded a digest before it would read anything would be a
    required field wearing a function signature, which is the shape every
    quality gate in this project arrives in. `artifact_sha256` is nullable for
    the same reason: requiring a value does not produce one.
    """
    done = ingest.ingest(_local(BLOB), out="probe.safetensors", subject="probe",
                         root=tmp_path)
    # The facts are about the file that was written. The input's digest is
    # recorded beside it as provenance, and the two differ because the output
    # carries a header the input did not.
    assert done.header["source_sha256"] == BLOB_SHA
    assert done.facts.sha256 == hashlib.sha256(done.path.read_bytes()).hexdigest()
    assert done.facts.shape == "[8]" and done.facts.dtype == "float32"


# --------------------------------------------------------------------------- #
# 2. A pickle is refused rather than loaded, and the refusal is what stops it.


RAN: list[str] = []


def _mark() -> str:
    """The payload. Harmless, and the point is only that it ran at all."""
    RAN.append("the pickle ran")
    return "marked"


class _Detonator:
    """An object whose unpickling calls a function of our choosing.

    This is what `allow_pickle` means. Not a theoretical risk and not a
    malformed file: a perfectly well-formed `.npz` that executes code when a
    reader loads it with the flag numpy has always offered.
    """

    def __reduce__(self):
        return (_mark, ())


@pytest.fixture(autouse=True)
def quiet():
    RAN.clear()
    yield
    RAN.clear()


def test_an_npz_carrying_a_pickle_is_refused_and_the_pickle_does_not_run(tmp_path):
    blob = _npz(direction=np.array([_Detonator()], dtype=object))
    assert RAN == [], "the payload ran while the fixture was being built"

    with pytest.raises(ValueError) as caught:
        ingest.ingest(_local(blob), out="probe.safetensors", subject="probe",
                      root=tmp_path)

    assert RAN == [], (
        f"the pickle executed during a refused ingest: {RAN}"
    )
    assert "allow_pickle" in str(caught.value) or "Object arrays" in str(caught.value)


def test_the_same_npz_executes_under_allow_pickle_true():
    """The flag is load-bearing, shown rather than asserted.

    The member scan cannot see this one: numpy writes an object array to a
    member called `direction.npy` like every other array, so the archive looks
    exactly like a legitimate one from the outside. `allow_pickle=False` inside
    `_read_npz` is the only thing between these bytes and the code in them.
    """
    blob = _npz(direction=np.array([_Detonator()], dtype=object))
    assert zipfile.ZipFile(io.BytesIO(blob)).namelist() == ["direction.npy"], (
        "the archive no longer looks innocent from the outside, so the scan "
        "would have caught it and this proves nothing about the flag"
    )

    loaded = np.load(io.BytesIO(blob), allow_pickle=True)["direction"]
    assert RAN == ["the pickle ran"], (
        f"the payload did not execute even with the flag on: {RAN}"
    )
    assert loaded.tolist() == ["marked"]


def test_the_flag_is_written_down_rather_than_left_to_the_default():
    """A source read, because a behavioral test cannot tell these apart.

    `numpy.load` defaults to `allow_pickle=False` today. Relying on that puts
    the safety of every artifact this registry converts inside somebody else's
    default, and a default is a thing that changes in a minor release without
    anybody here reading the changelog. `artifacts/REAL.md` says the ingest
    asserts the flag rather than assuming it, and this is what makes that
    sentence checkable.
    """
    text = (ROOT / "src" / "controlbun" / "ingest.py").read_text()
    start = text.index("def _read_npz")
    body = text[start:text.index("\ndef ", start + 1)]
    assert "allow_pickle=False" in body, (
        "the npz converter no longer states the flag, so it now depends on "
        "numpy's default staying what it is"
    )


def test_a_raw_pickle_is_refused_before_anything_loads_it(monkeypatch, tmp_path):
    spy = _Spy().install(monkeypatch)
    blob = pickle.dumps(_Detonator())
    assert blob[:1] == b"\x80", "the probe is not a protocol-2-or-later pickle"

    with pytest.raises(ingest.RefusedBytes, match="pickle"):
        ingest.ingest(_local(blob), out="probe.safetensors", subject="probe",
                      root=tmp_path)

    assert RAN == [], f"the payload executed: {RAN}"
    assert spy.calls == 0, (
        "the refusal happened after a converter had already been handed the "
        "bytes, so it is a report rather than a refusal"
    )


def test_an_archive_carrying_a_pickle_member_is_refused_and_names_it(tmp_path):
    """The layout a `.pt` uses, reproduced rather than assumed.

    That torch writes a zip around a pickle is inference from the format's
    shape and is not checked here. What is checked is the rule that catches it
    either way: an archive whose members are not all `.npy` is not something
    this path knows how to read without running part of it.
    """
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("archive/data.pkl", pickle.dumps(_Detonator()))
        archive.writestr("archive/data/0", b"\x00" * 32)
    blob = buffer.getvalue()

    with pytest.raises(ingest.RefusedBytes) as caught:
        ingest.ingest(_local(blob), out="probe.safetensors", subject="probe",
                      root=tmp_path)

    assert "archive/data.pkl" in str(caught.value), (
        "the refusal does not say what is in the archive, so the reader has to "
        "go and find out"
    )
    assert RAN == [], f"the payload executed: {RAN}"


def test_a_plain_npz_of_arrays_still_converts(tmp_path):
    """The control. A refusal that refuses everything is not a check."""
    done = ingest.ingest(
        _local(_npz(direction=RAMP)),
        out="probe.safetensors", subject="probe", root=tmp_path,
    )
    assert load_file(done.path)["direction"].tolist() == RAMP.tolist()
    assert done.facts.shape == "[8]"


# --------------------------------------------------------------------------- #
# 3. Drift is caught, and the artifact already on disk survives being caught.


def _drifting_payload(parsed: ingest.Parsed) -> ingest.Payload:
    """A conversion that has moved: same file, different bytes out."""
    return ingest.Payload(name="direction", tensor=-parsed.arrays["direction"])


def test_a_conversion_whose_output_moved_is_refused(tmp_path):
    recorded = ingest.ingest(_local(BLOB), out="held.safetensors",
                             subject="held", root=tmp_path).facts.sha256

    with pytest.raises(artifact.MismatchedArtifact) as caught:
        ingest.ingest(_local(BLOB), out="held.safetensors", subject="held",
                      root=tmp_path, claim=Claim(sha256=recorded),
                      payload=_drifting_payload)
    assert recorded in str(caught.value)


def test_the_artifact_on_disk_is_not_replaced_by_the_bytes_that_failed(tmp_path):
    """The half the old shape got wrong, and it got it wrong accurately.

    `artifacts/ingest_arena.py` used to `save_file` over the destination and
    compare the result afterwards. So a drifted conversion reported the drift
    correctly, exited nonzero, and had already overwritten the committed
    artifact with the bytes that failed. The next `--check` then compared the
    bad file against the record and failed again, which is correct and far too
    late: the bytes the recorded digest identifies were gone from the tree.
    """
    held = tmp_path / "held.safetensors"
    recorded = ingest.ingest(_local(BLOB), out="held.safetensors",
                             subject="held", root=tmp_path).facts.sha256
    original = held.read_bytes()

    with pytest.raises(artifact.MismatchedArtifact):
        ingest.ingest(_local(BLOB), out="held.safetensors", subject="held",
                      root=tmp_path, claim=Claim(sha256=recorded),
                      payload=_drifting_payload)

    assert held.read_bytes() == original, (
        "a refused conversion replaced the artifact that was already there"
    )
    assert not list(tmp_path.glob("*.ingesting")), (
        f"the staged file was left behind: {list(tmp_path.iterdir())}"
    )


def test_the_old_shape_destroyed_it_while_reporting_the_drift_correctly(tmp_path):
    """The same drift under the previous ordering, reproduced literally.

    Write, then compare. Both steps work; the file is gone anyway. This is what
    staging the output and moving it into place afterwards is for, and without
    this test the staging would look like tidiness rather than a fix.
    """
    held = tmp_path / "held.safetensors"
    save_file({"direction": RAMP}, held)
    sort_header(held)
    recorded = hashlib.sha256(held.read_bytes()).hexdigest()
    original = held.read_bytes()

    # The old ordering, in the three lines it was.
    save_file({"direction": -RAMP}, held)
    sort_header(held)
    got = hashlib.sha256(held.read_bytes()).hexdigest()

    assert got != recorded, "the probe did not drift, so it is not a probe"
    assert held.read_bytes() != original, (
        "the old ordering did not overwrite the file, so there was nothing to fix"
    )


def test_the_arena_check_reports_a_drifted_vendored_file(tmp_path):
    """End to end through the script `make site` runs, offline.

    Negation preserves shape, dtype and L2 norm exactly, so this is a different
    artifact that satisfies everything the record holds about it other than the
    digest.
    """
    dest = tmp_path / "repo"
    dest.mkdir()
    for part in ("artifacts", "src"):
        shutil.copytree(ROOT / part, dest / part,
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))

    script = dest / "artifacts" / "ingest_arena.py"

    def check() -> subprocess.CompletedProcess:
        return subprocess.run([sys.executable, str(script), "--check"],
                              capture_output=True, text=True)

    assert check().returncode == 0, "the untouched copy already fails"

    held = dest / "artifacts" / "soham" / "d_olmo3_lda.safetensors"
    before = held.read_bytes()
    name, tensor = next(iter(load_file(held).items()))
    save_file({name: -tensor}, held)
    sort_header(held)
    assert held.read_bytes() != before, "the mutation did not land"

    drifted = check()
    assert drifted.returncode != 0, (
        "a vendored file that is no longer the one the ingest wrote passed the "
        "offline check"
    )
    assert "DRIFTED" in drifted.stdout
    assert "d_olmo3_lda.safetensors" in drifted.stdout


# --------------------------------------------------------------------------- #
# 4. The format set is open, and so is what a caller may say is in a file.


def test_a_converter_registered_from_outside_works(monkeypatch, tmp_path):
    """The extension point, exercised rather than documented.

    A format nobody here anticipated has to work as well as the two that
    shipped, or `FORMATS` is a permission list with a friendlier name. This
    registers a made-up container from outside the package and ingests it.
    """
    body = b"RAMP8" + RAMP.tobytes()

    def read(blob: bytes) -> ingest.Parsed:
        return ingest.Parsed(
            arrays={"direction": np.frombuffer(blob[5:], dtype=np.float32)},
            metadata={"invented_by": "this test"},
        )

    monkeypatch.setitem(ingest.FORMATS, "ramp8", ingest.Format(
        sniff=lambda blob: blob.startswith(b"RAMP8"),
        read=read,
        note="a container invented in a test",
    ))

    done = ingest.ingest(_local(body), out="probe.safetensors", subject="probe",
                         root=tmp_path)
    assert load_file(done.path)["direction"].tolist() == RAMP.tolist()
    assert done.header["invented_by"] == "this test"


def test_bytes_nothing_reads_are_refused_and_the_message_is_not_a_rule(tmp_path):
    """The refusal has to describe itself as incomplete, not as a boundary.

    A message saying which formats are allowed teaches every reader that the
    list is the rule. Naming what has a converter and where to add one says the
    true thing instead, which is that nobody here decides how an author packs
    a tensor.
    """
    with pytest.raises(ingest.RefusedBytes) as caught:
        ingest.ingest(_local(b"\x93NUMPY not really"), out="probe.safetensors",
                      subject="probe", root=tmp_path)

    message = str(caught.value)
    assert "FORMATS" in message, "the refusal does not say where a converter goes"
    for word in ("allowed", "permitted", "supported", "unsupported"):
        assert word not in message.lower(), (
            f"the refusal calls the converter set {word!r}, which turns a "
            "description of what is written into a rule about what may be"
        )


def test_a_file_of_several_arrays_refuses_rather_than_taking_the_first(tmp_path):
    """Taking one would take whichever the format happened to serialize first."""
    with pytest.raises(ingest.RefusedBytes, match="2 arrays"):
        ingest.ingest(_local(_npz(direction=RAMP, other=OTHER)),
                      out="probe.safetensors", subject="probe", root=tmp_path)


def test_a_caller_that_knows_the_layout_says_so_and_is_not_refused(tmp_path):
    """The same file, with the corpus-specific knowledge supplied by the corpus."""
    def payload(parsed: ingest.Parsed) -> ingest.Payload:
        return ingest.Payload(name="direction", tensor=parsed.arrays["direction"],
                              metadata={"note": str(parsed.arrays["other"].size)})

    done = ingest.ingest(_local(_npz(direction=RAMP, other=OTHER)),
                         out="probe.safetensors", subject="probe",
                         root=tmp_path, payload=payload)
    assert load_file(done.path)["direction"].tolist() == RAMP.tolist()


def test_the_tensor_keeps_the_name_the_source_gave_it(tmp_path):
    """A reader diffing our copy against the original diffs the same names."""
    done = ingest.ingest(_local(_npz(whatever_the_author_called_it=RAMP)),
                         out="probe.safetensors", subject="probe", root=tmp_path)
    assert list(load_file(done.path)) == ["whatever_the_author_called_it"]


def test_re_ingesting_a_file_that_already_carries_provenance_is_refused(tmp_path):
    """The collision that matters, and it arrives without anybody arranging it.

    An ingested file carries `source_sha256` in its own header. Put it back
    through the same path and the new source wants that key too. Letting one
    win silently produces a file whose header says it came from somewhere it
    did not, which is worse than a refusal in exactly the way a wrong digest is
    worse than a missing one.
    """
    first = ingest.ingest(_local(BLOB), out="held.safetensors", subject="held",
                          root=tmp_path)
    assert "source_sha256" in artifact.metadata_of(first.path.read_bytes()), (
        "the first pass recorded no provenance, so there is nothing to collide"
    )

    with pytest.raises(ingest.RefusedBytes, match="source_sha256"):
        ingest.ingest(_local(first.path.read_bytes()), out="again.safetensors",
                      subject="again", root=tmp_path)


# Enough header keys that a chance collision is not the reason this passes.
# safetensors serializes its header out of a hash map whose iteration order is
# seeded per process, so with two keys two processes agree about half the time
# and a probe built on two keys is a coin toss dressed as a test. This was
# written with two first, and a mutation that removed `sort_header` altogether
# went unnoticed. Twelve keys is twelve factorial orderings.
HEADER_KEYS = 12
PROCESSES = 6


def test_processes_writing_one_input_produce_one_file(tmp_path):
    """safetensors seeds its header hash map per process, so this is not free.

    Runs in one process would share a seed and prove nothing, which is why
    every one of these is a subprocess. Both halves are here: the ingest path
    has to give one digest across all of them, and the same tensor and header
    written **without** `sort_header` has to give more than one, or the
    reproducibility this project's recorded digests depend on would be a
    property of safetensors rather than of anything here.
    """
    source = tmp_path / "input.npz"
    source.write_bytes(_npz(direction=RAMP))

    script = tmp_path / "once.py"
    script.write_text(
        "import sys, hashlib\n"
        "from pathlib import Path\n"
        f"sys.path.insert(0, {str(ROOT / 'src')!r})\n"
        "import numpy as np\n"
        "from safetensors.numpy import save_file\n"
        "from controlbun import ingest\n"
        f"KEYS = {{f'synthetic_key_{{i}}': str(i) for i in range({HEADER_KEYS})}}\n"
        "def payload(parsed):\n"
        "    return ingest.Payload(name='direction',\n"
        "        tensor=parsed.arrays['direction'], metadata=dict(KEYS))\n"
        f"blob = Path({str(source)!r}).read_bytes()\n"
        "done = ingest.ingest(ingest.LocalBytes(blob=blob, origin='a probe'),\n"
        "    out=sys.argv[1] + '.safetensors', subject='probe',\n"
        f"    payload=payload, root=Path({str(tmp_path)!r}))\n"
        "print(hashlib.sha256(done.path.read_bytes()).hexdigest())\n"
        # The same content, written the way anything would without the fix.
        f"loose = Path({str(tmp_path)!r}) / (sys.argv[1] + '.loose')\n"
        "save_file({'direction': np.arange(1, 9, dtype=np.float32)}, loose,\n"
        "          metadata=dict(KEYS))\n"
        "print(hashlib.sha256(loose.read_bytes()).hexdigest())\n"
    )

    ingested, loose = set(), set()
    for n in range(PROCESSES):
        done = subprocess.run([sys.executable, str(script), str(n)],
                              capture_output=True, text=True)
        assert done.returncode == 0, done.stderr
        one, two = done.stdout.split()
        ingested.add(one)
        loose.add(two)

    assert len(loose) > 1, (
        f"{PROCESSES} processes wrote {HEADER_KEYS} header keys in one order "
        "every time, so safetensors is deterministic here and this probe "
        "cannot observe what sort_header is for"
    )
    assert len(ingested) == 1, (
        f"the ingest produced {len(ingested)} different files from one input: "
        f"{sorted(ingested)}. Every recorded digest is now a number that means "
        "nothing"
    )


# --------------------------------------------------------------------------- #
# 5. A pin is a pin: the URL fetched and the provenance recorded cannot disagree.


@pytest.fixture
def served():
    """A stand-in host. Records every path it was asked for."""
    asked: list[str] = []

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):  # noqa: N802
            asked.append(self.path)
            if self.path.endswith("/direction.npz"):
                body = _npz(direction=RAMP)
                self.send_response(200)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            else:
                self.send_error(404)

        def log_message(self, *a):
            pass

    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    httpd = http.server.HTTPServer(("127.0.0.1", port), Handler)
    # `poll_interval` rather than the 0.5s default, because `shutdown()`
    # blocks until this loop notices the flag. Two servers per test at
    # half a second each was a flat one second of teardown on every
    # test in this file, measured as the largest single cost in the
    # suite on 2026-09-20. It is a poll interval and not a sleep: the
    # shutdown still waits for the loop to actually exit, so nothing
    # here races.
    threading.Thread(
        target=lambda: httpd.serve_forever(poll_interval=0.01),
        daemon=True,
    ).start()
    yield f"http://127.0.0.1:{port}", asked
    httpd.shutdown()


COMMIT = "a" * 40


def test_the_commit_fetched_is_the_commit_recorded(served, tmp_path):
    """One field, formatted into the URL and into the header.

    The failure this forecloses is a source that takes a URL and a commit as
    two arguments, fetches one and records the other, and is correct until
    somebody updates a pin in one place. The template means there is no second
    place.
    """
    base, asked = served
    source = ingest.PinnedRepoFile(
        host="example.test",
        repo="someone/theirs",
        commit=COMMIT,
        path="direction.npz",
        sha256=hashlib.sha256(_npz(direction=RAMP)).hexdigest(),
        url_template=base + "/{repo}/{commit}/{path}",
    )

    done = ingest.ingest(source, out="probe.safetensors", subject="probe",
                         root=tmp_path)

    assert asked == [f"/someone/theirs/{COMMIT}/direction.npz"]
    assert done.header["source_commit"] == COMMIT
    assert done.header["source_repo"] == "example.test/someone/theirs"
    assert done.header["source_path"] == "direction.npz"


def test_a_branch_is_refused_before_anything_is_fetched(served, tmp_path):
    """A tag moves, so a pin to one is a pin to whatever is there today."""
    base, asked = served
    source = ingest.PinnedRepoFile(
        host="example.test", repo="someone/theirs", commit="main",
        path="direction.npz", sha256="0" * 64,
        url_template=base + "/{repo}/{commit}/{path}",
    )
    with pytest.raises(fetch.FetchError, match="not a commit SHA"):
        source.read()
    assert asked == [], "a request went out for a reference that is not a pin"


def test_bytes_from_the_network_that_miss_their_digest_are_refused(served,
                                                                   monkeypatch,
                                                                   tmp_path):
    """The case the pin exists for: a re-pointed object, or a bad CDN edge."""
    base, _asked = served
    spy = _Spy().install(monkeypatch)
    source = ingest.PinnedRepoFile(
        host="example.test", repo="someone/theirs", commit=COMMIT,
        path="direction.npz", sha256="0" * 64,
        url_template=base + "/{repo}/{commit}/{path}",
    )

    with pytest.raises(artifact.MismatchedArtifact, match="sha256"):
        ingest.ingest(source, out="probe.safetensors", subject="probe",
                      root=tmp_path)
    assert spy.calls == 0, "the converter saw bytes that failed their pin"


def test_the_output_stays_inside_the_repository(tmp_path):
    """`local_path`, reused rather than reimplemented.

    A submitted filename reaches this argument the moment there is a write
    path, and a containment check added then is added too late.
    """
    with pytest.raises(artifact.UnsafeArtifactPath):
        ingest.ingest(_local(BLOB), out="../escaped.safetensors",
                      subject="probe", root=tmp_path)
    assert not list(tmp_path.iterdir())
