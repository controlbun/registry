"""Artifact bytes, written so a rebuild reproduces them.

safetensors is Rust-backed and serializes its header out of a HashMap, whose
iteration order is randomly seeded per process. The tensor payload is stable and
the header byte order is not, so writing the same tensor twice produces two
different files. For a project whose whole claim is that published numbers
re-derive from raw artifacts, a file that does not reproduce itself is not
acceptable: the sha256 in the ingest record would be a number that means nothing.

Both writers need the same guarantee, which is why this is here rather than in
either of them. `fixtures/build.py` writes the synthetic corpus and
`artifacts/ingest_arena.py` converts real directions somebody else published.
"""

from __future__ import annotations

import json
import struct
from pathlib import Path


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
