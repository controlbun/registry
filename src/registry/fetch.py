"""Resolve an artifact to bytes, locally or from the host a row names, at a commit.

Premise, restated because a premise stated in one file gets violated in every
other one: **the registry never designates.** That applies to hosts. Nobody
decided the Hub was this registry's host; it is where the first artifacts were
going and this module was written to match. A row carries its own host and its
own URL template now, so a host nobody here has met works by construction.

Four things this deliberately does not do.

**It does not keep a table of hosts it knows.** `registry.ingest.PinnedRepoFile`
settled the principle on the write side: "A table of the ones we happen to have
met would be a list of where an artifact is allowed to come from, which is not
ours to write." The read side takes the same fields. The one host named below is
`hub_pin`, and it is a default for a row that records nothing rather than an
entry in a list: every row in this database was written before there was a
column to say otherwise, and absence is a state rather than an error.

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

The cache is keyed by the URL, so it cannot go stale: the URL carries the commit,
a commit names one set of bytes forever, and two rows whose URLs differ are two
sets of bytes even when their repo, commit and path are identical. See
`_cache_path`, where that last one is not hypothetical.
"""

from __future__ import annotations

import hashlib
import os
import string
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from .artifact import local_path

ROOT = Path(__file__).resolve().parents[2]

# Overridable so tests can point at a local server instead of reaching the
# network, and so a fork can point at a different Hub without editing code. Read
# at call time by `hub_pin` rather than frozen into a template at import, so a
# test that repoints it repoints both what gets fetched and what gets recorded.
HUB = os.environ.get("REGISTRY_HUB", "https://huggingface.co")
CACHE = Path(os.environ.get("REGISTRY_CACHE", ROOT / ".cache" / "artifacts"))

# 40 hex characters. Anything else is a branch, a tag, or a mistake.
_SHA = 40

# The four values a template is formatted from. Named here because
# `_plain_fields` checks a template against them before formatting it, and
# because the refusal quotes the list back to whoever wrote the template.
_FIELDS = ("host", "repo", "commit", "path")

# What a GET can be checked over by somebody who is not on this machine.
#
# **The inverse question, because this is the one thing here that refuses.** What
# it makes impossible to express is an artifact pinned at `file:`, `data:` or
# `ftp:`. A `file:` URL is not a fetch, it is a local read wearing a URL: it
# resolves to different bytes on every machine, or to nothing, so it cannot be
# the thing `author/label@version` promises and nobody else can check it. That is
# refusing what cannot be verified rather than listing where an artifact may come
# from, which is the distinction the module docstring above draws. Any http or
# https host works, including ones nobody here has heard of, which is the point.
_OVER_THE_NETWORK = ("http", "https")


class FetchError(RuntimeError):
    """An artifact could not be resolved to bytes."""


def commit_sha(value: str) -> str:
    """Forty hex characters, or a refusal. One rule, stated once.

    `registry.ingest` pins a repo file the same way and against a different
    host, and two copies of this would be two chances for one of them to start
    accepting a tag.
    """
    if len(value) != _SHA or not all(c in "0123456789abcdef" for c in value.lower()):
        raise FetchError(
            f"{value!r} is not a commit SHA. Resolution is by commit only: a "
            "branch or tag can be moved by whoever owns the repo, so pinning to "
            "one pins to whatever is there today."
        )
    return value


def hub_pin() -> tuple[str, str]:
    """The host and URL template of the one host this module still names.

    Two callers and two reasons. `from_repo` uses it for a row that records
    neither, which is every row written before `schema/migrations/007` existed;
    `artifacts/publish.py` records it onto the rows it publishes, so a pin made
    after 007 says where it points instead of relying on this.

    Derived from `HUB` rather than written out, so a fork or a test that
    repoints it gets the same answer from both callers. The host comes back as a
    bare authority and the template carries the scheme, which is the shape the
    columns document and the shape `PinnedRepoFile` already writes.
    """
    split = urllib.parse.urlsplit(HUB)
    base = f"{split.scheme}://{{host}}{split.path.rstrip('/')}"
    return split.netloc, base + "/{repo}/resolve/{commit}/{path}"


def _plain_fields(url_template: str) -> None:
    """Every placeholder is a bare `{name}`, or a refusal saying why.

    `str.format` is more than substitution, and a template is data out of a
    row. `{repo:>200000000}` allocates two hundred megabytes of padding from a
    seventeen-character string, and `{host.__class__}` walks attributes of the
    value rather than printing it. Neither reaches anything here: the four
    values are plain strings, so attribute traversal gets `str`'s own members
    and not a module's globals, which is what makes the classic `str.format`
    leak work. The padding one is a real allocation from a value nobody typed
    at a prompt.

    So the conversions, the format specs and the attribute and index syntax all
    go, none of which a URL template has any use for. What this makes
    impossible to express is a URL whose text depends on how a field is padded
    or repr'd, which is not a URL layout any host serves.
    """
    try:
        placeholders = list(string.Formatter().parse(url_template))
    except ValueError as malformed:
        raise FetchError(
            f"{url_template!r} is not a URL template this row can be fetched "
            f"with ({malformed}). The fields are "
            f"{', '.join('{' + f + '}' for f in _FIELDS)}, and a template may "
            "use any of them or none. Nothing here decides what a host's URLs "
            "look like, so a template that does not parse is a typo rather "
            "than an unrecognized host."
        ) from malformed

    for _, field, spec, conversion in placeholders:
        if field is None:
            continue
        if field not in _FIELDS:
            raise FetchError(
                f"{url_template!r} interpolates {'{' + field + '}'}, which is "
                f"not one of {', '.join('{' + f + '}' for f in _FIELDS)}. A "
                "template may use any of those or none of them. Attribute and "
                "index syntax is refused rather than resolved: a URL is text, "
                "and a template that reaches into a value is doing something "
                "other than building one."
            )
        if spec or conversion:
            raise FetchError(
                f"{url_template!r} applies a format spec or a conversion to "
                f"{'{' + field + '}'}. Padding and repr have no meaning in a "
                "URL, and a width in a template out of a row is an allocation "
                "nobody asked for. Write the placeholder on its own."
            )


def pinned_url(*, host: str, repo: str, commit: str, path: str,
               url_template: str) -> str:
    """The URL a pinned artifact lives at, built from the row's own template.

    The same four fields `registry.ingest.PinnedRepoFile` formats on the way in,
    so the URL a row is fetched from and the provenance written into the file's
    header come from one set of values rather than two that can drift.

    **Four things are checked, and none of them is who the host is.**

    `commit` goes through `commit_sha`, which is the one rule.

    The scheme has to be one a fetch can happen over; see `_OVER_THE_NETWORK`.

    The commit has to survive into the URL's path or query. That is the property
    a pin is, stated directly rather than as a list of characters to watch for,
    and it catches both ways of losing it: a template that never interpolates
    `{commit}` at all, and a substituted field that pushes it into a query string
    or a fragment. `repo` and `path` are quoted for the same reason, which closes
    the hole recorded as S2 in `V1.md`: a repo carrying a `?` used to turn
    `{repo}/resolve/{commit}/{path}` into a query on a bare repo URL, fetch
    whatever is at HEAD, and pass everything downstream silently.

    A template is data out of a row, and `str.format` does more than
    substitute. `_plain_fields` is the fourth thing checked and the reason is
    written there.
    """
    commit = commit_sha(commit)
    _plain_fields(url_template)
    fields = {
        # A scheme in the host works and so does a bare authority, because the
        # template decides which it needs. What neither may do is carry a `?`,
        # a `#` or whitespace into the URL's structure.
        "host": urllib.parse.quote(host, safe=":/"),
        "repo": urllib.parse.quote(repo.strip("/"), safe="/"),
        "commit": commit,
        "path": urllib.parse.quote(path.lstrip("/"), safe="/"),
    }
    try:
        url = url_template.format(**fields)
    except (KeyError, IndexError, ValueError) as unusable:
        # `_plain_fields` has already refused an unknown name and a format
        # spec, so what reaches here is a brace that does not close. Named
        # anyway rather than left to surface as a traceback.
        raise FetchError(
            f"{url_template!r} is not a URL template this row can be fetched "
            f"with ({unusable}). The fields are {{host}}, {{repo}}, {{commit}} "
            "and {path}, and a template may use any of them or none. Nothing "
            "here decides what a host's URLs look like, so a template that does "
            "not format is a typo rather than an unrecognized host."
        ) from unusable

    split = urllib.parse.urlsplit(url)
    if split.scheme.lower() not in _OVER_THE_NETWORK:
        raise FetchError(
            f"{url} is not something this can fetch over the network. A pin has "
            "to resolve to the same bytes for everybody, and a local or inline "
            "URL resolves to whatever is on the machine that reads it. Publish "
            "the bytes somewhere with a URL and pin that; any http or https "
            "host works and none of them is on a list here."
        )
    if commit not in split.path and commit not in split.query:
        raise FetchError(
            f"{url} does not carry {commit[:12]}, so it is not a pinned fetch. "
            "Either the template never interpolates {commit}, or a value in it "
            "ended the path early and what is left resolves to whatever is "
            "there today, which is the opposite of what `author/label@version` "
            "promises."
        )
    return url


def _cache_path(url: str, path: str) -> Path:
    """Where fetched bytes rest, keyed on the URL and nothing else.

    The URL is what determines the bytes, and every other candidate key is a
    subset of it that collides. Keyed on repo, commit and path, as this was
    before `schema/migrations/007`, two hosts with one repo slug share a cache
    entry, which is the collision `PinnedRepoFile` names.

    **The template has to be in the key too, and that is not theoretical.**
    `github.com/soham-padia/steering-arena` at one commit and one path serves
    22,424 bytes of LFS object through `media.githubusercontent.com` and a
    130-byte LFS pointer through `raw.githubusercontent.com`. Same repo, same
    commit, same path, different bytes, and only the template tells them apart.
    Checked with curl on 2026-09-18.

    Hashed rather than nested, because a repo id contains a slash and a path may
    contain several. The filename is kept off the end so a human looking in the
    cache can see what is there.
    """
    key = hashlib.sha256(url.encode()).hexdigest()[:32]
    return CACHE / key / (Path(path).name or "artifact")


def get_url(url: str, *, timeout: int = 60, not_found: str | None = None) -> bytes:
    """One GET, with the failures named rather than surfacing as HTTP internals.

    Shared with `registry.ingest`, which fetches a digest-pinned URL that is
    not always a Hub URL. A second copy of this would be a second place to
    forget that a redirect is the normal case here rather than the exception,
    which is the one thing in it that is not obvious.
    """
    try:
        # Redirects are followed by default and matter here: LFS objects, which
        # is every real artifact, redirect to a CDN rather than being served
        # from the host that was asked.
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return r.read()
    except urllib.error.HTTPError as e:
        if e.code == 404:
            raise FetchError(not_found or (
                f"{url} returned 404. Either the commit does not exist or the "
                "file was never in it. A pinned fetch does not fall back to "
                "another revision."
            )) from e
        if e.code in (401, 403):
            raise FetchError(
                f"{url} is not publicly readable. This client sends no "
                "credentials, and everything this registry points at is public by "
                "construction, so a private artifact is a fact about the "
                "submission rather than a login prompt."
            ) from e
        raise FetchError(f"{url} returned {e.code}") from e
    except urllib.error.URLError as e:
        raise FetchError(f"{url} could not be reached: {e.reason}") from e


def from_repo(*, repo: str, commit: str, path: str, host: str | None = None,
              url_template: str | None = None, timeout: int = 60) -> bytes:
    """Bytes of one file, at one commit, from wherever the row says it lives.

    Cached forever, because a SHA is forever.

    `host` and `url_template` are both optional and fall back together to
    `hub_pin`. A row recording neither is not a broken row: it is a row written
    before there was a column to record them in, and it resolves exactly where
    it resolved then.
    """
    default_host, default_template = hub_pin()
    url = pinned_url(
        host=host or default_host,
        repo=repo,
        commit=commit,
        path=path,
        url_template=url_template or default_template,
    )

    cached = _cache_path(url, path)
    if cached.exists():
        return cached.read_bytes()

    blob = get_url(
        url,
        timeout=timeout,
        # Named here rather than in `get_url`, which has only the URL to go on.
        not_found=(
            f"{repo}@{commit[:12]} has no {path} at {url}. Either the commit "
            "does not exist, the file was never in it, or the template names a "
            "URL layout this host does not serve. A pinned fetch does not fall "
            "back to another revision."
        ),
    )

    cached.parent.mkdir(parents=True, exist_ok=True)
    cached.write_bytes(blob)
    return blob


def resolve(
    *,
    artifact_path: str | None,
    served_repo: str | None = None,
    served_commit: str | None = None,
    served_host: str | None = None,
    served_url_template: str | None = None,
    artifact_repo: str | None = None,
    artifact_commit: str | None = None,
    artifact_host: str | None = None,
    artifact_url_template: str | None = None,
) -> bytes:
    """Bytes for one artifact, from whichever source is available.

    Order: our served copy, then the author's repo, then a local file. Our copy
    first because it is the one whose availability we control; the author's repo
    next because it is where the bytes actually came from; the local path last
    because it is how the synthetic fixtures work and how anyone runs this from a
    clean checkout with no network.

    Both remote branches take a host and a template, and neither knows a host by
    name. `schema/migrations/004` keeps the two pairs apart because one pair of
    columns cannot express a mirror that has drifted from its origin; a served
    copy that could only ever be on one host would be the same gap in half.
    """
    if served_repo and served_commit:
        return from_repo(repo=served_repo, commit=served_commit,
                         path=artifact_path or "", host=served_host,
                         url_template=served_url_template)
    if artifact_repo and artifact_commit:
        return from_repo(repo=artifact_repo, commit=artifact_commit,
                         path=artifact_path or "", host=artifact_host,
                         url_template=artifact_url_template)
    if artifact_path:
        local = local_path(artifact_path, root=ROOT)
        if not local.exists():
            raise FetchError(
                f"{artifact_path} is not on disk and no repo is recorded, so there "
                "is nowhere to get these bytes from."
            )
        return local.read_bytes()
    raise FetchError("no artifact recorded: no served copy, no repo, no local path")
