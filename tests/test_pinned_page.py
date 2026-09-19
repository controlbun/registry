"""The page points at the artifact, and at nothing it made up.

The registry's premise is that it points at artifacts rather than serving them,
and for a while its pages pointed at nothing. `artifact_path` travelled into the
export and `artifact_repo`, `artifact_commit`, `artifact_host`,
`artifact_url_template` and `artifact_sha256` did not, so migration 007, the
any-host templates and `artifacts/publish.py` were all invisible to anybody
reading the website. `registry.load(...).vector()` resolved the one real pin
from a cold cache; a person with a browser had a page naming an artifact and no
way to get it. Nothing failed, because the pin work went end to end through the
Python client and the client never touches the export.

Three things are checked here and the third is the one that keeps the other two
honest.

**The pin reaches the page.** Host, repo, commit, digest and a link.

**The URL is built once, in Python.** `registry.fetch.row_url` owns the rule
that turns host, repo, commit, path and template into a URL, including the three
refusals: a template that drops the commit is not a pin, a scheme that is not a
network fetch cannot be checked by anybody else, and a placeholder carrying a
format spec is doing something other than building a URL. The page prints what
that function returned. A component assembling a URL from parts beside it would
be a second copy of that rule in the half nobody runs `tests/test_fetch.py`
against.

**Nothing is invented for a row with no pin.** Nine of the ten rows in this
corpus record no repo. Five are synthetic fixtures and four are real directions
their author never published at a URL, and both are ordinary states rather than
gaps. So the check is not "the unpinned page says the right sentence", which a
template can satisfy while linking somewhere anyway. It is that every off-site
link on the whole built site is a URL the export carries.
"""

from __future__ import annotations

import json
import re
import sqlite3
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from registry import fetch, views  # noqa: E402

DIST = ROOT / "astro" / "dist"
EXPORT = ROOT / "astro" / "src" / "data" / "registry.json"

# The one real pin in the corpus, and the only thing in this file that names a
# specific row. Recorded in `artifacts/intake.jsonl` and confirmed against the
# host on 2026-09-19: the URL below returned 33,056 bytes whose sha256 is the
# one the row records.
PINNED = "soham/trauma@d61-diffmeans-expository-L34"

HREF = re.compile(r'href="([^"]*)"')


def payload() -> dict:
    return json.loads(EXPORT.read_text())


def claimants() -> list[dict]:
    return [c for entry in payload()["labels"] for c in entry["claimants"]]


def ref(c: dict) -> str:
    return f"{c['author']}/{c['label']}@{c['version']}"


def pinned_claimant() -> dict:
    match = next((c for c in claimants() if ref(c) == PINNED), None)
    if match is None:
        pytest.skip(f"{PINNED} is not in the export")
    return match


def pages() -> list[Path]:
    if not DIST.exists():
        pytest.skip("site not built; run `make site`")
    return sorted(DIST.rglob("*.html"))


def page_of(c: dict) -> str:
    """The built submission page for one claimant, found by its own URL.

    Located through the link the site itself publishes rather than by rebuilding
    the route here, so a change to the URL shape does not quietly make this skip.
    """
    want = f"/{c['author']}/{c['model_id']}/{c['label']}/{c['version']}/"
    path = DIST / want.strip("/") / "index.html"
    if not path.exists():
        pytest.skip(f"{want} not built; run `make site`")
    return path.read_text()


# --------------------------------------------------------------------------- #
# The five fields, and the URL derived from four of them.


def test_the_export_carries_where_the_artifact_is():
    c = pinned_claimant()
    p = c["published"]
    assert p, f"{PINNED} has a pin in the database and none in the export"
    assert p["repo"] and p["commit"] and p["path"], p
    assert p["host"], p
    assert p["url_template"], p
    assert c["artifact_sha256"], (
        "the digest is the only field on the page a reader can check the bytes "
        "against by hand, and it did not travel"
    )


def test_the_exported_url_is_the_one_the_client_would_fetch():
    """Not "a URL for this row". The URL, from the function that owns the rule.

    `registry.fetch.row_url` is what `from_repo` resolves through, so this
    asserts the reader and the client are sent to the same bytes.
    """
    c = pinned_claimant()
    p = c["published"]
    assert p["url"] == fetch.row_url(
        repo=p["repo"], commit=p["commit"], path=p["path"],
        host=p["host"], url_template=p["url_template"],
    )
    assert p["refusal"] is None


def test_the_url_carries_the_commit():
    """The property a pin is, restated at the export boundary.

    `pinned_url` enforces it and this is not a second copy of the rule: it is
    the assertion that the enforcement is still in the path the page reads,
    which a future export that stopped calling `row_url` would break silently.
    """
    p = pinned_claimant()["published"]
    assert p["commit"] in p["url"]


# --------------------------------------------------------------------------- #
# What the page shows.


def test_the_page_shows_the_host_the_repo_the_commit_and_the_digest():
    c = pinned_claimant()
    html = page_of(c)
    p = c["published"]
    for field, value in (
        ("host", p["host"]),
        ("repo", p["repo"]),
        ("commit", p["commit"]),
        ("sha256", c["artifact_sha256"]),
    ):
        assert value in html, (
            f"the page does not show the {field} of an artifact it points at. A "
            "reader cannot check bytes against a record the record does not print"
        )


def test_the_page_links_to_the_bytes():
    c = pinned_claimant()
    assert f'href="{c["published"]["url"]}"' in page_of(c), (
        "the pinned artifact has no link on its own page, so the registry names "
        "a place and does not point at it"
    )


def test_the_page_gives_the_client_call_that_checks_the_digest():
    """The link hands over bytes and leaves the check to the reader.

    `Submission.vector()` compares what arrives against the recorded digest
    before returning a tensor, so the one-line call is the path that does the
    check rather than describing it. It is on the page for that reason and not
    as documentation.
    """
    c = pinned_claimant()
    html = page_of(c)
    assert f'registry.load("{PINNED}").vector()' in html.replace("&quot;", '"')


def test_an_unpinned_row_says_so_and_keeps_its_digest():
    unpinned = [c for c in claimants() if c["published"] is None]
    assert unpinned, "every row is pinned, so this check no longer looks at anything"
    for c in unpinned:
        html = page_of(c)
        assert "Nobody recorded where these bytes are published" in html, (
            f"{ref(c)} has no pin and its page does not say so"
        )
        assert c["artifact_sha256"] in html, (
            f"{ref(c)} dropped its digest along with its absent pin. The digest "
            "is a fact about the bytes and not about where they are"
        )


def test_an_unpinned_row_does_not_read_as_degraded():
    """Absence is a state, not a fault, and the copy has to stay that way.

    Nine of ten rows here are unpinned. Wording that calls those missing,
    incomplete or unavailable would make being fetchable a quality, and the step
    after a quality is an ordering.
    """
    c = next(c for c in claimants() if c["published"] is None)
    html = page_of(c)
    # Bounded at the next heading, so this reads that section and not whatever
    # follows it. An unbounded slice would start failing on somebody else's copy.
    after = html[html.find("Where the bytes are"):]
    block = after[: after.find("<h2", 1)].lower()
    assert "sha256" in block, "the section boundary moved and this is reading nothing"
    for word in ("missing", "incomplete", "unavailable", "not yet", "error"):
        assert word not in block, (
            f"the unpinned artifact block calls the absence {word!r}, which "
            "makes a pin into a bar rather than a fact"
        )


# --------------------------------------------------------------------------- #
# Nothing invented. The check, and then the proof that it bites.


def site_origin() -> str:
    config = (ROOT / "astro" / "astro.config.mjs").read_text()
    m = re.search(r'site:\s*["\']([^"\']+)["\']', config)
    assert m, "astro.config.mjs no longer declares a site, so own-origin is unknown"
    return m.group(1).rstrip("/")


def offsite_links(html_by_page: dict[str, str], origin: str) -> dict[str, str]:
    """Every link leaving the site, as target -> the page it is on.

    Own-origin absolutes are the canonical tags in `<head>`; root-relative links
    are `falsifier/links.py`'s job and resolve inside the build.
    """
    out: dict[str, str] = {}
    for where, html in html_by_page.items():
        for href in HREF.findall(html):
            if not href.startswith(("http://", "https://")):
                continue
            if href.startswith(origin):
                continue
            out[href] = where
    return out


def test_every_offsite_link_is_a_url_the_export_carries():
    """The check that makes the unpinned case real rather than a form of words.

    A template can print "nobody recorded where these bytes are" and link
    somewhere anyway, and a template that guesses a plausible Hub URL for a row
    with no repo would look right on every page in this corpus. So the question
    is asked of the whole build at once: is there any off-site link here that
    the export did not put there.
    """
    origin = site_origin()
    found = offsite_links(
        {str(p.relative_to(DIST)): p.read_text() for p in pages()}, origin
    )
    known = {
        c["published"]["url"]
        for c in claimants()
        if c["published"] and c["published"]["url"]
    }
    invented = {url: where for url, where in found.items() if url not in known}
    assert not invented, (
        "the site links off-site to somewhere the exported data does not name:\n"
        + "\n".join(f"  {where}: {url}" for url, where in sorted(invented.items()))
    )


def test_the_offsite_check_bites():
    """Prove the check above fails when violated, or it is decoration.

    Two hostile pages: one linking at a host nothing in this corpus records, and
    one linking at a Hub URL that is the right shape and names a commit no row
    holds, which is what a template guessing at a URL would produce.
    """
    origin = site_origin()
    guessed = (
        "https://huggingface.co/someone/directions/resolve/"
        + "a" * 40 + "/vectors/kindness.safetensors"
    )
    hostile = {
        "alice/index.html": f'<a href="{guessed}">get it</a>',
        "bob/index.html": '<a href="https://example.invalid/vector.safetensors">x</a>',
        # Not findings: an own-origin canonical and an internal link.
        "carol/index.html": f'<link href="{origin}/carol/"><a href="/models/">m</a>',
    }
    found = offsite_links(hostile, origin)
    assert set(found) == {guessed, "https://example.invalid/vector.safetensors"}
    assert found[guessed] == "alice/index.html"


def test_a_url_and_a_digest_are_not_read_as_published_numbers():
    """The falsifier holds every `\\d\\.\\d{4}` in rendered copy to the export.

    A digest is hex and a commit is hex, so neither carries a decimal point and
    neither can collide. A URL can: a host like `cdn2.12345.example` would put
    one on the page, the falsifier would ask the export to account for it, and
    the build would fail naming a figure nobody published. Checked here rather
    than assumed, so that if it ever happens the failure has a name.

    A URL and a digest are not authored prose and are not marked `data-authored`
    per the 2026-09-19 decision. They are facts out of a row, which is what the
    falsifier is supposed to be scanning.
    """
    published_number = re.compile(r"(?<![\d.])\d\.\d{4}(?![\d.])")
    for c in claimants():
        p = c["published"]
        for value in (c["artifact_sha256"], p and p["url"], p and p["commit"]):
            if not value:
                continue
            assert not published_number.search(value), (
                f"{ref(c)} renders {value!r}, which the falsifier will read as a "
                "published measurement and hold to the exported data"
            )


# --------------------------------------------------------------------------- #
# `published_at` itself, on the rows this corpus does not contain.


def row(**columns) -> sqlite3.Row:
    """One intervention row's worth of columns, without a database.

    `published_at` reads five names off a row and nothing else, so a mapping
    with those names is the whole fixture. Nothing here is a measurement and
    nothing here is written anywhere.
    """
    base = {
        "artifact_repo": None, "artifact_commit": None, "artifact_path": None,
        "artifact_host": None, "artifact_url_template": None,
        "artifact_sha256": None,
    }
    return {**base, **columns}


SHA = "b" * 40


def test_a_row_with_no_repo_is_none_rather_than_an_empty_pin():
    assert views.published_at(None) is None
    assert views.published_at(row(artifact_path="fixtures/x.safetensors")) is None
    assert views.published_at(row(artifact_repo="a/b")) is None, (
        "a repo with no commit is not a pin, and rendering it as one would show "
        "a reader a location that resolves to whatever is there today"
    )


def test_a_row_recording_no_host_resolves_where_the_client_resolves_it():
    """A row written before `schema/migrations/007` records neither host nor
    template, and the URL printed beside it has to be the URL it is fetched
    from. The recorded fields stay None on the page rather than being backfilled
    with the default, which would read as a fact somebody checked.
    """
    p = views.published_at(row(
        artifact_repo="whoever/whatever", artifact_commit=SHA,
        artifact_path="vectors/d.safetensors",
    ))
    assert p["host"] is None and p["url_template"] is None
    assert p["url"] == fetch.row_url(
        repo="whoever/whatever", commit=SHA, path="vectors/d.safetensors",
    )
    assert SHA in p["url"]


def test_a_template_that_drops_the_commit_renders_its_refusal_and_no_url():
    """One unresolvable row renders as that row saying so.

    Raising here would take the whole export down, which means one bad template
    in one row costs the corpus its website. The refusal is `pinned_url`'s own
    sentence, so what the page prints is the reason rather than a restatement of
    it written beside the template.
    """
    p = views.published_at(row(
        artifact_repo="whoever/whatever", artifact_commit=SHA,
        artifact_path="vectors/d.safetensors",
        artifact_host="example.invalid",
        artifact_url_template="https://{host}/{repo}/{path}",
    ))
    assert p["url"] is None
    assert "not a pinned fetch" in p["refusal"]
    assert p["repo"] == "whoever/whatever", (
        "the recorded pin still shows. A row whose template does not resolve is "
        "still a row that recorded a repo and a commit"
    )


def test_a_scheme_nobody_can_fetch_over_refuses_rather_than_linking():
    p = views.published_at(row(
        artifact_repo="whoever/whatever", artifact_commit=SHA,
        artifact_path="d.safetensors",
        artifact_host="localhost",
        artifact_url_template="file://{host}/{repo}/{commit}/{path}",
    ))
    assert p["url"] is None
    assert "not something this can fetch over the network" in p["refusal"]
