"""Artifact bytes: written so a rebuild reproduces them, read only from inside.

safetensors is Rust-backed and serializes its header out of a HashMap, whose
iteration order is randomly seeded per process. The tensor payload is stable and
the header byte order is not, so writing the same tensor twice produces two
different files. For a project whose whole claim is that published numbers
re-derive from raw artifacts, a file that does not reproduce itself is not
acceptable: the sha256 in the ingest record would be a number that means nothing.

Every writer needs the same guarantee, which is why `sort_header` is here rather
than in any of them. `fixtures/build.py` writes the synthetic corpus and
`registry.ingest` writes whatever arrives from anywhere else, including the real
directions `artifacts/ingest_arena.py` converts.

`local_path` is here for the mirror-image reason: four callers turn a database
value into a filesystem path, and all four have to refuse the same things.

`Claim`, `Facts`, `disagreements` and `confirmed` are here for the third version
of that reason, and it is the one this repository has already got wrong twice.
**Do these bytes agree with what is recorded about them?** is asked when a row is
written, when the client fetches an artifact, and again by the falsifier. Asked
in three places it gets three answers, and they drift: that is what happened to
`pairwise` against `similarity_matrix`, which now share `_angle_between`, and to
the two `<head>` blocks.
So the comparison is written once, below, and the three callers differ only in
what they claim and in what they do with a mismatch. The writers and the client
refuse; the falsifier reports, because a falsifier that raises is
indistinguishable from a falsifier that is broken.
"""

from __future__ import annotations

import hashlib
import json
import struct
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
# Aliased, and the alias is the point rather than a style choice. client.py
# imported safetensors' `load` into a module exposing its own public `load(ref)`
# and shadowed it, so every call went to the parser and got a ref where it
# wanted bytes. This module has no `load` today and could grow one tomorrow.
from safetensors.numpy import load as load_bytes

ROOT = Path(__file__).resolve().parents[2]


class UnsafeArtifactPath(ValueError):
    """An `artifact_path` that does not stay inside the repository."""


class MismatchedArtifact(RuntimeError):
    """The bytes are not what somebody said they were.

    Raised rather than warned, on both sides of the record. On the read path a
    tensor whose shape disagrees with the record is not a degraded version of
    the artifact, it is a different artifact, and handing it back would make
    every number on the page describe something else. On the write path the
    asymmetry is worse: the record is about to be published and the bytes are
    right there, so a row that goes in anyway is a typo that every later check
    then enforces against the author's own file.

    Lives here rather than in `client` because the comparison that raises it
    lives here, and `client` re-exports it so `except client.MismatchedArtifact`
    keeps meaning what it meant.
    """


# The one number in this module with a tolerance question, and the same one
# `falsifier/verify.py` already applies to it.
#
# **Matching it is the decision, not a coincidence.** A write-time rule stricter
# than the gate that rechecks the row later refuses artifacts that would have
# reconciled fine; a looser one admits rows that gate will reject after they are
# published. Equal is the only setting at which the two agree about the same
# artifact, so the two copies became one and the falsifier reaches it through
# `disagreements` rather than keeping its own.
#
# **Why a norm gets a tolerance and a digest does not.** A digest identifies a
# file: there is one right answer and no arithmetic between the bytes and it. A
# norm is derived, and the two ends of the comparison can derive it differently.
# `artifacts/soham/d_olmo3_v1.safetensors` norms to exactly 1.0 read as float32
# and to 1.0000000000683045 promoted to float64, and its row records 1.0 because
# that is the value cited from the arena.
#
# **Where the size comes from.** Everything this project publishes renders
# through `.toFixed(4)`, so a figure read back off a page is knowable to 5e-5
# and no better, which is the floor; and a difference of a whole rendered digit
# would show on the page while being recorded as agreement, which is the
# ceiling. The norm is not what identifies an artifact and this number is not
# doing that job, the digest is. `tests/test_write_claim_bite.py` holds the
# band, because a tolerance with no bound is a place to put a difference.
L2_TOLERANCE = 1e-4


@dataclass(frozen=True)
class Claim:
    """What somebody says about bytes, before anything has read them.

    Every field is optional and that is the design, not laxness. A caller with
    nothing to say about a norm is not making a wrong claim about it, and the
    row it writes records an absence rather than a number somebody invented to
    fill the column. `schema/migrations/005` and `006` both turn on that
    distinction: requiring a value does not produce the value, it produces a
    string, and a string in a load-bearing column is worse than the hole.
    """

    shape: str | None = None
    dtype: str | None = None
    l2_norm: float | None = None
    sha256: str | None = None


@dataclass(frozen=True)
class Facts:
    """What the bytes say, with `None` for anything this caller did not derive.

    Partial on purpose. The falsifier's digest check hashes a file without
    parsing it and the check beside it parses a tensor it has already cached, so
    neither is in a position to fill all four, and neither should have to
    pretend. A comparison fires only where a claim and a derived fact are both
    present, so an absent fact is silent rather than a mismatch against `None`.
    """

    shape: str | None = None
    dtype: str | None = None
    l2_norm: float | None = None
    sha256: str | None = None
    # Not claimed by anything and never compared. It is here because a digest
    # mismatch alongside a byte count nothing like the original is a truncated
    # transfer rather than a substitution, and the reader of the error is the
    # person who has to tell those apart.
    size: int | None = None
    # The parsed tensor, so the client does not parse the same bytes a second
    # time to get the thing it came for. Out of equality and repr: an ndarray
    # has no scalar `==` and this record is otherwise four small values.
    tensor: np.ndarray | None = field(default=None, compare=False, repr=False)


def local_path(rel: str | Path, *, root: Path | None = None) -> Path:
    """Resolve an `artifact_path` against the repository, or refuse it.

    `ROOT / value` is not containment. pathlib drops the left operand entirely
    when the right is absolute, so `artifact_path = "/etc/passwd"` resolves to
    `/etc/passwd`, and `..` is not normalized away either. Four callers did that:
    `fetch.resolve`, `comparison.load_vector`, and two sites in the falsifier.
    Nothing writes a hostile value today because nothing but this repository
    writes rows at all, and that stops being true the moment there is an upload
    path, which is exactly when a check added afterwards is added too late.

    Refuses rather than clamps. A path that escapes is not a path with a typo in
    it; it is a row claiming the registry holds something it does not, and the
    caller needs to see that rather than receive some other file's bytes.
    """
    base = (root or ROOT).resolve()
    candidate = (base / rel).resolve()
    if not candidate.is_relative_to(base):
        raise UnsafeArtifactPath(
            f"{str(rel)!r} resolves to {candidate}, which is outside {base}. "
            "An artifact path is relative to the repository and stays in it."
        )
    return candidate


def _split(raw: bytes) -> tuple[dict, bytes]:
    """A safetensors file as its header and everything after it.

    One place that knows the layout, because a second would be a second place
    to get the offset wrong: an 8-byte little-endian length, that many bytes of
    JSON, then the tensor payload. Three callers read it now, one to rewrite
    the header and two to look at what is in it.
    """
    size = struct.unpack("<Q", raw[:8])[0]
    return json.loads(raw[8:8 + size]), raw[8 + size:]


def metadata_of(blob: bytes) -> dict[str, str]:
    """The `__metadata__` block, or an empty one where the writer set none.

    Absent metadata is not an error and does not become one here. A file
    somebody wrote without a header is a file with nothing recorded in it,
    which is a state.
    """
    return _split(blob)[0].get("__metadata__", {})


def tensor_names(blob: bytes) -> list[str]:
    """The tensors a safetensors file declares, read off its header alone.

    Here rather than in a caller for the reason `_split` is here: the 8-byte
    length prefix is known in one place, and a second reader of that layout is
    a second chance to get the offset wrong. Nothing is parsed and no payload is
    touched, so a caller holding a large file can pass a prefix of it.

    Displayed, never compared. `confirmed` already refuses a file carrying more
    than one tensor, and which name the author gave theirs is carried through
    rather than assigned, which is the point `registry.ingest.Payload` makes.
    """
    return sorted(k for k in _split(blob)[0] if k != "__metadata__")


def header_of(path: str | Path) -> bytes:
    """Enough of a safetensors file on disk to read its header, and no payload.

    For the case the functions above are awkward in: half a gigabyte on disk
    whose tensor name somebody wants to show. Reading the file to answer that
    would be a second full copy in memory for a string.
    """
    with Path(path).open("rb") as handle:
        prefix = handle.read(8)
        size = struct.unpack("<Q", prefix)[0]
        return prefix + handle.read(size)


def sort_header(path: str | Path) -> None:
    """Rewrite a safetensors header with sorted keys, in place.

    Trailing whitespace padding is permitted by the format and preserves the
    8-byte alignment the writer uses, so the tensor payload does not move.
    """
    path = Path(path)
    raw = path.read_bytes()
    header, payload = _split(raw)

    sorted_header = json.dumps(header, sort_keys=True, separators=(",", ":")).encode()
    sorted_header += b" " * (-len(sorted_header) % 8)
    path.write_bytes(struct.pack("<Q", len(sorted_header)) + sorted_header + payload)


# --------------------------------------------------------------------------- #
# What the bytes say, what somebody claimed, and the one comparison between them.


def facts_of(tensor, *, sha256: str | None = None,
             size: int | None = None) -> Facts:
    """Derive a tensor's facts one way, so two callers cannot derive them two ways.

    Small enough to inline and that is exactly why it is not. `str(list(shape))`
    against `f"[{shape[0]}]"` agree on every 1-D tensor in the corpus and part
    company on the first 2-D one, and `np.linalg.norm` on a float32 array
    returns a float32, which rounds differently from the float64 the same
    expression returns after a promotion. Two callers each picking a spelling is
    how a tolerance stops meaning anything.
    """
    return Facts(
        shape=str(list(tensor.shape)),
        dtype=str(tensor.dtype),
        l2_norm=float(np.linalg.norm(tensor)),
        sha256=sha256,
        size=size,
        tensor=tensor,
    )


def disagreements(claim: Claim, facts: Facts) -> list[str]:
    """Every field where a claim and a derived fact do not match.

    **The one comparison.** Returns sentences rather than raising, because the
    three callers want different things done with the answer and only one of
    them is allowed to stop: the falsifier reports and carries on, the client
    and the writers refuse. Handing back the finding and letting the caller
    decide is what keeps this from being forked into a raising copy and a
    reporting copy that stop agreeing about what a mismatch is.

    Each sentence names both sides, claimed first. An error that says only that
    two things differ leaves the reader to go and find out which two.
    """
    counted = f"the {facts.size} bytes" if facts.size is not None else "the bytes"
    out: list[str] = []

    if claim.sha256 is not None and facts.sha256 is not None \
            and claim.sha256 != facts.sha256:
        out.append(
            f"recorded as sha256 {claim.sha256} and {counted} hash to "
            f"{facts.sha256}. These are not the bytes the record was written "
            "from. A pinned reference resolves to one frozen artifact forever, "
            "so this is not a newer version of it; one of the two moved."
        )

    if claim.shape is not None and facts.shape is not None \
            and claim.shape != facts.shape:
        out.append(
            f"recorded as shape {claim.shape} and the bytes hold {facts.shape}. "
            "The artifact and the record have come apart; nothing that reads "
            "either is safe to use until that is explained."
        )

    if claim.dtype is not None and facts.dtype is not None \
            and claim.dtype != facts.dtype:
        out.append(
            f"recorded as {claim.dtype} and the bytes hold {facts.dtype}."
        )

    if claim.l2_norm is not None and facts.l2_norm is not None \
            and abs(float(claim.l2_norm) - facts.l2_norm) > L2_TOLERANCE:
        out.append(
            f"recorded as L2 norm {claim.l2_norm} and the bytes norm to "
            f"{facts.l2_norm:.6f}. Two derivations of one float are allowed "
            f"{L2_TOLERANCE} between them and this is wider than that."
        )

    return out


def _refuse(subject: str, found: list[str]) -> None:
    """Every mismatch at once, not the first one.

    A record that has two things wrong with it gets fixed twice if the error
    names one of them, and the second fix is made by somebody who now believes
    the first was the whole problem.
    """
    if found:
        raise MismatchedArtifact(
            "\n".join(f"{subject} is {line}" for line in found)
        )


def _keep_the_claim(claim: Claim, facts: Facts) -> Facts:
    """The claim where somebody made one, the derived value where nobody did.

    **This is the half that is easy to get backwards, so it is a function with a
    name.** A version of this that recomputed and overwrote would be simpler and
    would destroy the thing the check is for. `artifacts/seed.py` claims
    `[5120]`, `float32` and a unit norm because those are cited: 5120 is the
    residual width of the model the arena ran (`CONTEXT.md`), the ingest refuses
    anything but a 1-D float32 array, and `artifacts/REAL.md` states the shipped
    directions are unit-norm. What that row is worth is that the citation and
    the bytes agree. Overwrite it with a recomputation and the column holds a
    number that agrees with the bytes by construction, which is the same nothing
    `fixtures/build.py` already says its own digest is worth.

    So the value recorded stays the value somebody stood behind, and what this
    function has established by the time it runs is that standing behind it was
    warranted.
    """
    return Facts(
        shape=claim.shape if claim.shape is not None else facts.shape,
        dtype=claim.dtype if claim.dtype is not None else facts.dtype,
        l2_norm=claim.l2_norm if claim.l2_norm is not None else facts.l2_norm,
        sha256=claim.sha256 if claim.sha256 is not None else facts.sha256,
        size=facts.size,
        tensor=facts.tensor,
    )


def confirm_digest(blob: bytes, claim: Claim = Claim(), *,
                   subject: str) -> str:
    """The digest half, run before any parser sees the bytes. Returns it.

    Split out of `confirmed` because the ingest path needs this half on bytes
    `confirmed` cannot parse at all: a `.npz` arriving from somebody else's
    server is checked against its recorded digest here, and only then handed to
    numpy. Same comparison, same refusal, one function, so a caller cannot get
    a weaker version of the check by being early in the pipeline.
    """
    digest = hashlib.sha256(blob).hexdigest()
    _refuse(subject, disagreements(claim, Facts(sha256=digest, size=len(blob))))
    return digest


def confirmed(blob: bytes, claim: Claim = Claim(), *, subject: str) -> Facts:
    """Bytes plus what is claimed about them, in: the facts to record, or a refusal.

    **Why the write path needs this and the read path was not enough.** Before
    this existed, two scripts put tensor facts into the `intervention` table by
    typing them, one field of the same `INSERT` was derived from the bytes, and
    nothing compared the other three against anything. The values happened to be
    right. The mechanism was that somebody had been careful, and a mechanism
    that is somebody being careful fails the first time it is somebody else.
    Downstream does not save it either, because downstream compares *against*
    the record: a mistyped shape makes the client refuse the author's own
    artifact and name their bytes as the wrong ones, and for a row whose bytes
    live in somebody else's repo the falsifier never sees it at all.

    **`subject` is required.** Every message names what it is about, and a
    default would be taken by every caller in a hurry.

    **The digest is compared before the parser runs**, which is the order
    `artifacts/ingest_arena.py` established. safetensors cannot express an
    object array, so the arbitrary-code argument that motivated it there does
    not carry here; what remains is that the parser is the first code to touch
    bytes a server we do not run just sent us, and one hash of a 20KB buffer is
    a cheap thing to do first. The comparison is called twice for that reason
    and is the same comparison both times, once with only a digest derived and
    once with everything.
    """
    digest = confirm_digest(blob, claim, subject=subject)

    tensors = load_bytes(blob)
    if len(tensors) != 1:
        # Not a field comparison, so not in `disagreements`: there is no claim
        # to compare against and no single tensor to derive facts from. Taking
        # the first would work, silently, and pick by whatever order the file
        # happens to serialize in.
        raise MismatchedArtifact(
            f"{subject} is a file holding {len(tensors)} tensors "
            f"({sorted(tensors)}). A submission is one artifact."
        )

    facts = facts_of(next(iter(tensors.values())), sha256=digest, size=len(blob))
    _refuse(subject, disagreements(claim, facts))
    return _keep_the_claim(claim, facts)
