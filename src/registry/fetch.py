"""Resolve an artifact to bytes, locally or from the Hub, pinned to a commit.

Three things this deliberately does not do.

**It does not depend on `huggingface_hub`.** Downloading one file at a pinned
commit is a GET at a documented URL. The library is nine transitive packages plus
a Rust binary, and it earns that when there is upload, auth and listing to do,
which is the v1 upload path. Paying for it now would be a permanent cost for a
capability v0 does not have.

**It does not authenticate.** Everything this registry points at is public, by
construction: a submission nobody can see cannot be attacked, evaluated by anyone
else, or compared. So no token ships, none is needed, and nobody installing the
client has to have one. If a fetch ever returns 401 or 403, that is a fact about
the artifact worth surfacing rather than a credential to go find.

**It does not resolve a branch or a tag.** Only a commit SHA. A tag is movable by
whoever owns the repo, so a pin to one is a pin to whatever is there today, which
is the opposite of what `author/label@version` promises.

The cache is keyed by the commit, so it cannot go stale: a SHA names one set of
bytes forever, and if the bytes differ the SHA differs.
"""

from __future__ import annotations

import hashlib
import os
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

# Overridable so tests can point at a local server instead of reaching the
# network, and so a fork can point at a different Hub without editing code.
HUB = os.environ.get("REGISTRY_HUB", "https://huggingface.co")
CACHE = Path(os.environ.get("REGISTRY_CACHE", ROOT / ".cache" / "artifacts"))

# 40 hex characters. Anything else is a branch, a tag, or a mistake.
_SHA = 40


class FetchError(RuntimeError):
    """An artifact could not be resolved to bytes."""


def hub_url(repo: str, commit: str, path: str) -> str:
    """The URL a pinned artifact lives at.

    Split out so a test can assert the shape without a network call, and so the
    one place that knows the Hub's URL layout is named.
    """
    if len(commit) != _SHA or not all(c in "0123456789abcdef" for c in commit.lower()):
        raise FetchError(
            f"{commit!r} is not a commit SHA. Resolution is by commit only: a "
            "branch or tag can be moved by whoever owns the repo, so pinning to "
            "one pins to whatever is there today."
        )
    return f"{HUB}/{repo}/resolve/{commit}/{path.lstrip('/')}"


def _cache_path(repo: str, commit: str, path: str) -> Path:
    # The commit alone would collide across repos that share a filename, so the
    # key covers all three. Hashed rather than nested, because a repo id contains
    # a slash and a path may contain several.
    key = hashlib.sha256(f"{repo}@{commit}/{path}".encode()).hexdigest()[:32]
    return CACHE / key / Path(path).name


def from_hub(repo: str, commit: str, path: str, *, timeout: int = 60) -> bytes:
    """Bytes of one file, at one commit. Cached forever, because a SHA is forever."""
    cached = _cache_path(repo, commit, path)
    if cached.exists():
        return cached.read_bytes()

    url = hub_url(repo, commit, path)
    try:
        # Redirects are followed by default and matter here: LFS objects, which
        # is every real artifact, redirect to a CDN rather than being served
        # from the Hub host.
        with urllib.request.urlopen(url, timeout=timeout) as r:
            blob = r.read()
    except urllib.error.HTTPError as e:
        if e.code == 404:
            raise FetchError(
                f"{repo}@{commit[:12]} has no {path}. Either the commit does not "
                "exist or the file was never in it. A pinned fetch does not fall "
                "back to another revision."
            ) from e
        if e.code in (401, 403):
            raise FetchError(
                f"{repo} is not publicly readable. This client sends no "
                "credentials, and everything this registry points at is public by "
                "construction, so a private artifact is a fact about the "
                "submission rather than a login prompt."
            ) from e
        raise FetchError(f"{url} returned {e.code}") from e
    except urllib.error.URLError as e:
        raise FetchError(f"{url} could not be reached: {e.reason}") from e

    cached.parent.mkdir(parents=True, exist_ok=True)
    cached.write_bytes(blob)
    return blob


def resolve(
    *,
    artifact_path: str | None,
    served_repo: str | None = None,
    served_commit: str | None = None,
    artifact_repo: str | None = None,
    artifact_commit: str | None = None,
) -> bytes:
    """Bytes for one artifact, from whichever source is available.

    Order: our served copy, then the author's repo, then a local file. Our copy
    first because it is the one whose availability we control; the author's repo
    next because it is where the bytes actually came from; the local path last
    because it is how the synthetic fixtures work and how anyone runs this from a
    clean checkout with no network.
    """
    if served_repo and served_commit:
        return from_hub(served_repo, served_commit, artifact_path or "")
    if artifact_repo and artifact_commit:
        return from_hub(artifact_repo, artifact_commit, artifact_path or "")
    if artifact_path:
        local = ROOT / artifact_path
        if not local.exists():
            raise FetchError(
                f"{artifact_path} is not on disk and no repo is recorded, so there "
                "is nowhere to get these bytes from."
            )
        return local.read_bytes()
    raise FetchError("no artifact recorded: no served copy, no repo, no local path")
