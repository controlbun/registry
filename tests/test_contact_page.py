"""`/contact/`: a way back to the author, and nothing that receives.

Premise, restated because a premise stated in one document gets violated in
every other one: **plurality is the product, the registry never designates, and
consumers pin visibly.** A registry is contributor-first, and until this page
existed the site had three outbound links, two of them to somebody else's
sign-in and one to the bytes of a single artifact. A reader who disagreed with
the argument on `/about/` had nowhere to put it. That is the reader whose
response is worth most, and the design was optimized against them by accident.

Three properties, and none of them is about the author's sentences, which are
his to rewrite:

**The address is clickable.** The href and the text say the same thing, so a
later attempt to hide the address from scrapers cannot quietly cost a reader the
click. The address is already the git author identity on every commit in a
public repository, which is the argument recorded in `astro/src/pages/contact.astro`.

**The page receives nothing.** Same structural criterion as
`tests/test_sign_in_page.py`, applied to the other page whose whole job is to
point somewhere else, and proved against counterexamples here rather than
imported, because a criterion shared between two files is a criterion that can
be weakened in one place for the other's reasons.

**What it says about the corpus is computed.** The count is read off the export
by the page, so a number written into a sentence goes stale silently and this is
where that gets caught.

The off-site links themselves are accounted for in `tests/test_pinned_page.py`,
which owns the rule that every link leaving this site was either derived from a
row or written down by somebody.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "astro" / "dist"
SOURCE = ROOT / "astro" / "src" / "pages" / "contact.astro"
BUILT = DIST / "contact" / "index.html"
EXPORT = ROOT / "astro" / "src" / "data" / "controlbun.json"

# The two things the page exists to carry. Named here as well as in the page, so
# a change to either has to be made in two places and the second is a test.
EMAIL = "sohampadia10@gmail.com"
REPO = "https://github.com/controlbun/registry"


def built() -> str:
    if not BUILT.exists():
        pytest.skip("site not built; run `make site`")
    return BUILT.read_text()


def text_of(html: str) -> str:
    """Reader-visible copy. Script and style survive naive tag-stripping."""
    for tag in ("script", "style"):
        html = re.sub(rf"<{tag}.*?</{tag}>", "", html, flags=re.S)
    return " ".join(re.sub(r"<[^>]+>", " ", html).split())


# --------------------------------------------------------------------------- #
# The two links, and the click.


def test_the_address_is_linked_and_says_what_it_links_to():
    """An address a reader has to retype is a contact route with a step in it.

    The failure this guards is not hypothetical and it arrives as an
    improvement: somebody writes the address as "sohampadia10 at gmail" or
    entity-encodes it against scrapers, the link stops matching the text or
    stops being a link, and the cost lands on every reader while the scraper
    reads the same address out of the commit log next door.
    """
    html = built()
    anchor = re.search(r'<a\b[^>]*href="mailto:([^"]+)"[^>]*>(.*?)</a>', html, re.S)
    assert anchor, "the contact page has no mailto anchor, so there is no way to reply"
    assert anchor.group(1) == EMAIL, (
        f"the link addresses {anchor.group(1)!r} and the page is for {EMAIL!r}"
    )
    assert " ".join(re.sub(r"<[^>]+>", " ", anchor.group(2)).split()) == EMAIL, (
        "the link text is not the address it sends to. A reader copying what "
        "they can see gets something other than where the click goes."
    )


def test_the_repository_is_one_click_away():
    """Most of what publishing the repo was for. A reader who wants to check a
    claim on this site should not have to search for the code."""
    assert f'href="{REPO}"' in built(), (
        "the site names no repository, so every claim on it has to be taken on "
        "trust by a reader who cannot find the thing that produced it"
    )


def test_the_page_is_reachable_without_reading_the_argument_first():
    """A contact link only on `/about/` reaches the reader who already stayed.

    The one worth hearing from is the reader who bounced off the home page, so
    the home page has to carry it. `falsifier/links.py` proves the link
    resolves; this proves it is made where it matters.
    """
    if not DIST.exists():
        pytest.skip("site not built; run `make site`")
    linkers = {
        p.relative_to(DIST).as_posix() for p in DIST.rglob("*.html")
        if 'href="/contact/"' in p.read_text(errors="ignore")
    }
    assert linkers, "nothing on the site links to /contact/"
    assert "index.html" in linkers, (
        "the home page does not link to /contact/, so a reader who leaves from "
        "there never sees that there is anybody to write to"
    )


# --------------------------------------------------------------------------- #
# Receives nothing, proved against counterexamples.

RECEIVES = {
    r"<form\b": "a form element",
    r"<input\b": "a field",
    r"<select\b": "a field",
    r"<textarea\b": "a field",
    r"\benctype\b": "a form encoding, which only a submitting form needs",
    r"\bformaction\b": "a submit button with its own target",
    r"type\s*=\s*[\"']?submit\b": "a submit button",
    r"method\s*=\s*[\"']?\s*post\b": "a POST target",
    r"\bXMLHttpRequest\b": "a scripted request older than fetch",
    r"\bsendBeacon\b": "a fire-and-forget POST",
    r"\bfetch\s*\(": "a scripted request",
}


def targets_that_receive(html: str) -> list[str]:
    found = []
    for pattern, what in RECEIVES.items():
        for m in re.finditer(pattern, html, re.I):
            found.append(f"{what} ({m.group(0)!r})")
    return found


def test_the_criterion_flags_the_things_it_claims_to_flag():
    """The bite. A contact page is where a form arrives, so the scanner that
    says there is none has to be shown catching one."""
    for bad in ('<form action="/contact" method="post">',
                '<input name="email" value="" />',
                '<textarea name="message"></textarea>',
                '<button type="submit">Send</button>',
                '<script>fetch("/x", { method: "POST", body: b })</script>',
                'navigator.sendBeacon("/x", d)'):
        assert targets_that_receive(bad), f"the criterion missed {bad!r}"

    for fine in (f'<a href="mailto:{EMAIL}">{EMAIL}</a>',
                 f'<a href="{REPO}">the code</a>',
                 '<a href="/about/">About</a>'):
        assert not targets_that_receive(fine), f"the criterion flagged {fine!r}"


def test_the_page_points_out_and_receives_nothing():
    found = targets_that_receive(built())
    assert not found, (
        "the contact page grew a target that receives:\n  " + "\n  ".join(found)
        + "\n\nA mailto anchor hands the reader to their own mail client and "
        "this page is gone. A contact form is the write path arriving under a "
        "friendlier name, and the dual-use question a write path raises has "
        "not been answered."
    )


def test_the_source_carries_no_script_of_its_own():
    assert "<script" not in SOURCE.read_text(), (
        "the contact page grew a script. Assembling the address at runtime to "
        "hide it from scrapers is what that script would be for, and it costs "
        "the click for every reader without script while the address stays "
        "readable in the commit log."
    )


# --------------------------------------------------------------------------- #
# What it says about the corpus, which is a fact and not a sentence.


def test_the_state_of_the_corpus_is_read_off_the_export():
    """A number written into prose is a number that goes stale silently.

    The page says how small this is, because that is what tells a reader
    whether their mail would matter. Saying it in words rather than from the
    data means the sentence stops being true on the day somebody submits, which
    is the day it would most embarrass the person who wrote it.
    """
    size = json.loads(EXPORT.read_text())["corpus"]["size"]
    body = text_of(built())
    assert f"{size} submissions" in body, (
        f"the page does not say the corpus size the export holds ({size}). "
        "Interpolate it from `data.corpus.size` rather than typing the number "
        "or spelling it out."
    )
