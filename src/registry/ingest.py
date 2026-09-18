"""Bytes in, one safetensors file out, checked against what was claimed about it.

**The set of formats below is what has a converter, not what may be published.**
`kind` is an open string and a file format is the same kind of thing: nobody here
decides which ways of packing a tensor are legitimate. What this path can decide
is which bytes it is able to read without executing them, and that is the line it
draws. A format nobody wrote a converter for is refused with a sentence saying so
and an entry in `FORMATS` is all it takes to change that, from outside this
package, without asking.

**Why this is library code rather than a script.** `artifacts/ingest_arena.py`
did all of it already, welded to one commit in one GitHub repository, for one
`.npz` layout. The steps are the same for an upload, for a pointer at somebody
else's Hub repo, and for the second corpus: take bytes from somewhere, check them
against a digest before anything parses them, convert to safetensors with the
provenance read off the source, and check the file that comes out. Only what
happens to the file afterwards differs between those cases, and that is not here.

**What is deliberately absent.** Nothing in this module serves, publishes,
uploads or mirrors anything. `schema/migrations/004` is explicit that serving a
copy of somebody's artifact makes this a distributor and needs the dual-use
policy, which is deferred. Ingest ends with a checked file on local disk. It is
also not exported from `registry/__init__.py`, which is the consumer surface: a
read-only client package that advertised an ingest entry point would be
advertising a write path that does not exist.

**The order of operations is the security property**, and it is the one
`artifacts/ingest_arena.py` established. The digest is compared before a parser
sees the bytes, because the parser is the first code to touch a file a server we
do not run just sent us. Then the format is sniffed, then a pickle-bearing input
is refused, and only then does numpy get a look.
"""

from __future__ import annotations

import hashlib
import io
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Protocol

import numpy as np
from safetensors.numpy import load as load_bytes
from safetensors.numpy import save_file

from . import fetch
from .artifact import (
    Claim,
    Facts,
    confirm_digest,
    confirmed,
    local_path,
    metadata_of,
    sort_header,
)


class RefusedBytes(ValueError):
    """Bytes this path will not convert, with the reason in the message.

    Distinct from `MismatchedArtifact`, which means somebody made a claim and
    the bytes contradict it. Here nobody has been contradicted: either nothing
    knows how to read the file, or reading it would mean running it.
    """


# --------------------------------------------------------------------------- #
# Where bytes come from.


class Source(Protocol):
    """Somewhere bytes come from, and what is true about where they came from.

    Two methods and no base class, so a caller with a source nobody here
    anticipated writes their own rather than asking for one. `read` returns the
    bytes and is where a digest pin is enforced; `provenance` returns the header
    fields that describe the origin, derived from what the source already holds
    rather than handed in beside it. That second rule is the whole point: a
    provenance header somebody retyped is a claim about the file, not a fact
    from it, and it goes stale the first time one of the two copies is edited.
    """

    def read(self) -> bytes: ...

    def provenance(self) -> dict[str, str]: ...


@dataclass(frozen=True)
class LocalBytes:
    """Bytes already in hand, from an upload or from a file on disk.

    `origin` is free text and is recorded as the submitter's own account of
    where this came from, which is why the header key says origin rather than
    anything implying it was checked. `sha256` is optional and checked when it
    is there: a submitter who states a digest is held to it, and one who states
    nothing is not thereby making a wrong claim.
    """

    blob: bytes
    origin: str
    sha256: str | None = None

    def read(self) -> bytes:
        confirm_digest(self.blob, Claim(sha256=self.sha256), subject=self.origin)
        return self.blob

    def provenance(self) -> dict[str, str]:
        return {
            "source_origin": self.origin,
            "source_sha256": hashlib.sha256(self.blob).hexdigest(),
        }


@dataclass(frozen=True)
class PinnedURL:
    """One URL whose pin is a content digest rather than a name.

    A fetch with no digest beside it resolves to whatever is there today, which
    is exactly what `author/label@version` promises not to be. So the digest is
    not optional here, and it is compared before the bytes reach anything that
    parses them.
    """

    url: str
    sha256: str
    timeout: int = 60

    def read(self) -> bytes:
        blob = fetch.get_url(self.url, timeout=self.timeout)
        confirm_digest(blob, Claim(sha256=self.sha256), subject=self.url)
        return blob

    def provenance(self) -> dict[str, str]:
        return {"source_url": self.url, "source_sha256": self.sha256}


@dataclass(frozen=True)
class PinnedRepoFile:
    """One path in one repository at one commit, pinned to a digest as well.

    `source_repo` carries the host, because `github.com/a/b` and
    `huggingface.co/a/b` are two repositories with one slug and a provenance
    header that cannot tell them apart points at both.

    **`url_template` rather than a table of hosts we know.** The two layouts
    this project already needs are different shapes: GitHub's media host serves
    `{repo}/{commit}/{path}` and the Hub serves `{repo}/resolve/{commit}/{path}`.
    A table of the ones we happen to have met would be a list of where an
    artifact is allowed to come from, which is not ours to write. The template
    belongs to the caller. The commit does not: forty hex characters, by the
    same rule and the same message `fetch.hub_url` applies, because a tag is
    movable by whoever owns the repo.

    The template is also what keeps the fetched URL and the recorded commit from
    disagreeing. Both are formatted from the one field, so there is no second
    copy to go stale.
    """

    host: str
    repo: str
    commit: str
    path: str
    sha256: str
    url_template: str
    timeout: int = 60

    def url(self) -> str:
        return self.url_template.format(
            host=self.host,
            repo=self.repo,
            commit=fetch.commit_sha(self.commit),
            path=self.path,
        )

    def read(self) -> bytes:
        return PinnedURL(self.url(), self.sha256, self.timeout).read()

    def provenance(self) -> dict[str, str]:
        return {
            "source_repo": f"{self.host}/{self.repo}",
            "source_commit": self.commit,
            "source_path": self.path,
            "source_sha256": self.sha256,
        }


# --------------------------------------------------------------------------- #
# What the bytes turn out to be.


# Arrays are out of equality and repr wherever they sit in a record here, for
# the reason `registry.artifact.Facts` gives about its own tensor: an ndarray has
# no scalar `==`, so a generated `__eq__` that touched one would raise rather
# than answer, and a generated `__repr__` would put five thousand floats in an
# error message.
_ARRAYS = dict(compare=False, repr=False)


@dataclass(frozen=True)
class Parsed:
    """Everything a converter found: the arrays, and whatever header they came in."""

    arrays: dict[str, np.ndarray] = field(**_ARRAYS)
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class Payload:
    """The one tensor to write, under the name the source gave it, plus header.

    `name` is carried through from the input rather than assigned here. An
    author who called their array `d` gets a file whose tensor is called `d`,
    so somebody diffing our copy against the original is diffing the same
    names, which is the argument `artifacts/REAL.md` makes about filenames.
    """

    name: str
    tensor: np.ndarray = field(**_ARRAYS)
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class Refusal:
    """A shape of input that gets a reason rather than a shrug.

    Not a gate. Anything these do not match still goes to the converters, and
    anything the converters do not read is still refused at the bottom. These
    exist so that the two cases worth explaining get explained, instead of
    arriving as "nothing here reads this" when the real answer is that reading
    it would mean running it.
    """

    sniff: Callable[[bytes], bool]
    why: Callable[[bytes], str]


@dataclass(frozen=True)
class Format:
    """One way of reading bytes into arrays, and how to tell the bytes are it.

    Detection is by content, never by filename. A name is a claim by whoever
    uploaded the file and the bytes are the fact, and this whole module exists
    because the two can differ.
    """

    sniff: Callable[[bytes], bool]
    read: Callable[[bytes], Parsed]
    note: str


def _zip_members(blob: bytes) -> list[str] | None:
    """The member names, or `None` if these bytes are not a zip archive.

    `zipfile` reads the central directory and nothing else, so this looks at
    what an archive contains without any of it being decoded or executed. That
    is the only reason the check can happen this early.
    """
    if not blob.startswith(b"PK\x03\x04"):
        return None
    try:
        with zipfile.ZipFile(io.BytesIO(blob)) as archive:
            return archive.namelist()
    except zipfile.BadZipFile:
        return None


def _is_pickle(blob: bytes) -> bool:
    # Pickle protocols 2 through 5 open with 0x80 and the protocol number.
    # Protocols 0 and 1 carry no marker and are not caught here; they fall
    # through to the refusal at the bottom, which is also a refusal.
    return len(blob) >= 2 and blob[0] == 0x80 and 2 <= blob[1] <= 5


def _is_archive_of_something_else(blob: bytes) -> bool:
    members = _zip_members(blob)
    return members is not None and not all(m.endswith(".npy") for m in members)


def _reads_as_npz(blob: bytes) -> bool:
    members = _zip_members(blob)
    return bool(members) and all(m.endswith(".npy") for m in members)


def _read_npz(blob: bytes) -> Parsed:
    # `allow_pickle=False` is the check and not a precaution, and it is asserted
    # here rather than left to numpy's default so that flipping it is a visible
    # edit. `numpy.load`'s `allow_pickle` argument is what turns an array file
    # into arbitrary code execution; the argument for refusing it is in
    # `artifacts/ingest_arena.py`'s docstring and is put better there.
    #
    # Two layers, and neither covers the other. The member scan above sees an
    # archive carrying a pickle next to the arrays. This sees an object array
    # inside a member named `d.npy` like every other member, which the scan
    # cannot distinguish: numpy refuses it at access rather than unpickling it,
    # which is why every key is materialized here instead of left lazy.
    archive = np.load(io.BytesIO(blob), allow_pickle=False)
    return Parsed(arrays={name: archive[name] for name in archive.files})


def _reads_as_safetensors(blob: bytes) -> bool:
    # A sniff rather than a parse: if the length prefix describes a JSON header
    # that fits in the file, it is one of these. Routed through the one function
    # that knows the layout, so a change to the offsets cannot leave the sniff
    # reading the old ones. Any failure at all means not this format, which is
    # why the except is wide.
    try:
        metadata_of(blob)
    except Exception:
        return False
    return True


def _read_safetensors(blob: bytes) -> Parsed:
    return Parsed(arrays=load_bytes(blob), metadata=metadata_of(blob))


# Refused with an explanation. A `.pt` is caught by one of these under either
# layout torch has used, raw pickle or a zip archive around one. That torch uses
# those two layouts is inference from the format's shape rather than something
# checked here; what is checked is the rule, which does not depend on it.
REFUSALS: list[Refusal] = [
    Refusal(
        sniff=_is_pickle,
        why=lambda blob: (
            "these bytes are a pickle. Reading one runs whatever is in it, so "
            "this is a refusal rather than a format nobody has got round to. "
            "Publish the tensor as safetensors or as an npz of plain arrays; "
            "the conversion loses nothing that a registry can verify anyway."
        ),
    ),
    Refusal(
        sniff=_is_archive_of_something_else,
        why=lambda blob: (
            "these bytes are a zip archive holding "
            f"{sorted(_zip_members(blob) or [])}, which is not a set of `.npy` "
            "members. An archive that carries a pickle beside its arrays gets "
            "read by unpickling it, and that is the thing this path exists to "
            "not do."
        ),
    ),
]

# What has a converter here. Mutable on purpose: this is the extension point,
# and a format added to it by somebody who never spoke to us works exactly as
# well as the two that shipped. The keys are names for humans reading a
# refusal, and nothing keys off them.
FORMATS: dict[str, Format] = {
    "safetensors": Format(
        sniff=_reads_as_safetensors,
        read=_read_safetensors,
        note="the format this path writes; re-ingest carries the header through",
    ),
    "npz": Format(
        sniff=_reads_as_npz,
        read=_read_npz,
        note="a zip of `.npy` members, loaded with allow_pickle=False",
    ),
}


def read_arrays(blob: bytes) -> Parsed:
    """Bytes to arrays, or a refusal that says which of the two reasons it is."""
    for refusal in REFUSALS:
        if refusal.sniff(blob):
            raise RefusedBytes(refusal.why(blob))

    for form in FORMATS.values():
        if form.sniff(blob):
            return form.read(blob)

    known = "; ".join(f"{name}, {form.note}" for name, form in FORMATS.items())
    raise RefusedBytes(
        "nothing here knows how to read these bytes. What has a converter "
        f"today: {known}. That is a description of what is written, not of "
        "what may be published: a converter is an entry in "
        "`registry.ingest.FORMATS` and adding one needs nobody's agreement. "
        "The only thing that cannot be added is a format this path would have "
        "to execute in order to read."
    )


def one_array(parsed: Parsed) -> Payload:
    """The default payload: the whole file, when the whole file is one array.

    A file holding several arrays is not ambiguous to its author and is
    ambiguous here, and taking the first would take whichever one the format
    happened to serialize first. `artifact.confirmed` refuses a multi-tensor
    safetensors file on the same reasoning. A caller who knows the layout says
    so with `payload=`, which is also where the knowledge belongs: how somebody
    packed their archive is a fact about their corpus, not about ingest.
    """
    if len(parsed.arrays) != 1:
        raise RefusedBytes(
            f"these bytes hold {len(parsed.arrays)} arrays "
            f"({sorted(parsed.arrays)}) and nothing here knows which one is "
            "the artifact. Pass `payload=` to say which, and to say what of "
            "the rest belongs in the header."
        )
    name, tensor = next(iter(parsed.arrays.items()))
    return Payload(name=name, tensor=tensor, metadata=dict(parsed.metadata))


# --------------------------------------------------------------------------- #
# The path itself.


@dataclass(frozen=True)
class Ingested:
    """Where the file landed, what the bytes say, and what went in the header."""

    path: Path
    facts: Facts
    header: dict[str, str]


def confirmed_file(path: str | Path, claim: Claim = Claim(), *,
                   subject: str) -> Facts:
    """One file on disk against what is recorded about it.

    Thin on purpose, and it exists so that the check `ingest` runs on the file
    it just wrote and an offline recheck of a file written months ago are the
    same call. Two spellings of that would be two answers to one question,
    which is the failure `registry.artifact` was consolidated to end.
    """
    return confirmed(Path(path).read_bytes(), claim, subject=subject)


def ingest(
    source: Source,
    *,
    out: str | Path,
    subject: str,
    claim: Claim = Claim(),
    payload: Callable[[Parsed], Payload] | None = None,
    root: Path | None = None,
) -> Ingested:
    """Take bytes from `source`, write one safetensors file, and check it.

    `claim` is about the file this writes, not about the bytes that came in;
    the claim about those is the digest the source is pinned to. A caller that
    has ingested before and recorded a digest passes it and gets a refusal if
    the conversion has moved. A caller doing this for the first time claims
    nothing and gets the derived facts, because absence is a state here as
    everywhere else.

    **The output is written to a temporary name and moved into place only after
    it has been checked.** `artifacts/ingest_arena.py` used to save over the
    committed artifact and compare afterwards, so a conversion that drifted
    reported the drift accurately and had already replaced the good bytes with
    the bad ones. A rerun then compared the drifted file against the record and
    failed again, which is correct and much too late: the thing the recorded
    digest identifies was gone from the working tree.

    The header is the payload's fields plus the source's provenance, and a key
    claimed by both is refused rather than resolved. Silently letting one win
    would make the header describe a different file from the one it came from,
    and re-ingesting an artifact that already carries provenance is exactly the
    case where that happens.
    """
    # Resolved first, so a path that leaves the repository is refused before a
    # byte is fetched. Created last, so a refusal leaves no empty directory
    # behind suggesting something was written there.
    destination = local_path(out, root=root)

    # The digest first, inside `read`, before anything below parses anything.
    blob = source.read()
    chosen = (payload or one_array)(read_arrays(blob))

    provenance = source.provenance()
    header = dict(chosen.metadata)
    both = sorted(set(header) & set(provenance))
    if both:
        raise RefusedBytes(
            f"{subject}: the payload and the source both set {both}. One would "
            "win and the header would then describe something other than where "
            "these bytes came from."
        )
    header.update(provenance)

    # safetensors will not write a non-contiguous array, and a caller's slice or
    # transpose is a reasonable thing to hand over. Copying here rather than in
    # every payload function keeps that out of corpus-specific code.
    tensor = np.ascontiguousarray(chosen.tensor)

    # Same directory as the destination, so the move at the end is a rename
    # within one filesystem rather than a copy that can half-finish.
    destination.parent.mkdir(parents=True, exist_ok=True)
    staged = destination.with_name(destination.name + ".ingesting")
    try:
        save_file({chosen.name: tensor}, staged, metadata=header)
        # safetensors serializes its header out of a hash map whose iteration
        # order is seeded per process, so without this the same tensor written
        # twice is two files. See `registry.artifact`.
        sort_header(staged)
        facts = confirmed_file(staged, claim, subject=subject)
        staged.replace(destination)
    finally:
        staged.unlink(missing_ok=True)

    return Ingested(path=destination, facts=facts, header=header)
