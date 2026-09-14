"""Where the real artifacts came from, in one place so two files cannot disagree.

`ingest_arena.py` fetches and verifies against this table. `seed.py` writes the
same commit into the recipe payload that gets published. A second copy of a
commit SHA is a second copy that can go stale.
"""

from __future__ import annotations

# github.com/soham-padia/steering-arena. The working tree was dirty when the
# manifest was generated, so this is not its HEAD: it is a commit at which all
# three blobs verify, confirmed by reading the git-LFS pointer at that commit and
# matching its oid against the sha256 below.
REPO = "soham-padia/steering-arena"
COMMIT = "b8b472175b7a2af1b7a7ecd7a784e982a6a7453a"

# LFS blobs do not come back from raw.githubusercontent.com, which serves the
# pointer file instead. The media host serves the object, and takes the same
# commit-pinned path.
MEDIA = "https://media.githubusercontent.com/media"

# source filename, sha256 of the .npz at COMMIT, sha256 of the .safetensors
# `ingest_arena.py` writes from it.
DIRECTIONS = [
    ("d_olmo3_v1.npz",
     "8406d93a724bd80940a968e0ab23cd5f155672664653eb715c1b58dcba71e909",
     "cfc5e2b7d670d509ccbb0bf71dbd9b75daa8f445afffa5738558ee40219dc186"),
    ("d_olmo3_logistic.npz",
     "f8ae8523065536df24ae0c4d08bd0e2ef4b08df92f6b59e4dc259ef8f8014877",
     "0471128514fed62eba8e9ba1bfbd3595026eddfacc3154ea740372f4f0c5a8f1"),
    ("d_olmo3_lda.npz",
     "09cc9991b9361840a2717534ccdabbca7e2a117fcae3cdcc169f89a57df1c3f1",
     "54b6aebafdb2533c81616c9aa4e27d20dd44b9a70b25c95f330111f9f550e173"),
]

LICENSE = (
    "allenai/Olmo-3-1125-32B is apache-2.0, confirmed from the Hub model API "
    "on 2026-09-14. A direction is derived from model weights, so redistributing "
    "one is governed by the model's license and not by who ran the extraction."
)
