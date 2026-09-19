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
HOST = "github.com"
REPO = "soham-padia/steering-arena"
COMMIT = "b8b472175b7a2af1b7a7ecd7a784e982a6a7453a"

# LFS blobs do not come back from raw.githubusercontent.com, which serves the
# pointer file instead. The media host serves the object, and takes the same
# commit-pinned path.
#
# A template rather than a prefix, because `controlbun.ingest.PinnedRepoFile`
# formats it from the same fields it records as provenance, and since
# `schema/migrations/007` an intervention row records one and
# `controlbun.fetch.pinned_url` formats it from the same four fields on the way
# back out. The commit appears once, in COMMIT, so the URL that is fetched and
# the commit that is written into the file's header cannot come apart.
#
# Neither template carries `{host}`, because GitHub does not serve file content
# from the host its repos are on. That is the reason a row records the host and
# the template separately rather than deriving one from the other.
MEDIA = "https://media.githubusercontent.com/media/{repo}/{commit}/{path}"

# The other half of the same host, for a file git-LFS does not track. Nothing
# here fetches through it: all four directions are LFS objects. It is recorded
# because the intake form offers both as suggestions, and because the pair is
# the evidence for the column: one host, two layouts, and each one 404s on the
# other's files.
#
# Rechecked with curl on 2026-09-18, against REPO at COMMIT. The media host
# returned the 22,424-byte object for `data/directions/d_olmo3_v1.npz`, whose
# sha256 is the one recorded below; the raw host returned the 130-byte LFS
# pointer naming the same oid; and the media host returned 404 for README.md,
# which is not LFS-tracked.
RAW = "https://raw.githubusercontent.com/{repo}/{commit}/{path}"

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
    # Layer 24, and the odd one out in three ways. It is at a different layer
    # from the three above, its own `meta` calls it a "Layer-sweep candidate",
    # and Season 2's migration pins it as that season's direction. All three are
    # true: the sweep produced it and then it was the one that shipped.
    #
    # Adding it does not reopen the settled decision that the five-point sweep
    # is recipe payload rather than five submissions. That decision is against
    # turning a diagnostic into five rows. This is the one point of it that was
    # selected and used, which is a different fact about the same file.
    ("d_olmo3_L24_logistic.npz",
     "ee714589a1da99c4eff445dd63612c15847b51d142cdc78f0476cdd2bbaec6f6",
     "e448b8f4266403f17e32182b2d2a5ed9a62bc86078fe7e6cec397daa49494616"),
]

LICENSE = (
    "allenai/Olmo-3-1125-32B is apache-2.0, confirmed from the Hub model API "
    "on 2026-09-14. A direction is derived from model weights, so redistributing "
    "one is governed by the model's license and not by who ran the extraction."
)
