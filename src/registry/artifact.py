"""Artifact bytes: written so a rebuild reproduces them, read only from inside.

safetensors is Rust-backed and serializes its header out of a HashMap, whose
iteration order is randomly seeded per process. The tensor payload is stable and
the header byte order is not, so writing the same tensor twice produces two
different files. For a project whose whole claim is that published numbers
re-derive from raw artifacts, a file that does not reproduce itself is not
acceptable: the sha256 in the ingest record would be a number that means nothing.

Both writers need the same guarantee, which is why `sort_header` is here rather
than in either of them. `fixtures/build.py` writes the synthetic corpus and
`artifacts/ingest_arena.py` converts real directions somebody else published.

`local_path` is here for the mirror-image reason: four callers turn a database
value into a filesystem path, and all four have to refuse the same things.
"""

from __future__ import annotations

import json
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class UnsafeArtifactPath(ValueError):
    """An `artifact_path` that does not stay inside the repository."""


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


def sort_header(path: str | Path) -> None:
    """Rewrite a safetensors header with sorted keys, in place.

    Trailing whitespace padding is permitted by the format and preserves the
    8-byte alignment the writer uses, so the tensor payload does not move.
    """
    path = Path(path)
    raw = path.read_bytes()
    size = struct.unpack("<Q", raw[:8])[0]
    header = json.loads(raw[8:8 + size])
    payload = raw[8 + size:]

    sorted_header = json.dumps(header, sort_keys=True, separators=(",", ":")).encode()
    sorted_header += b" " * (-len(sorted_header) % 8)
    path.write_bytes(struct.pack("<Q", len(sorted_header)) + sorted_header + payload)
