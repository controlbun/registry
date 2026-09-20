"""`/sign-in/`: an outbound signpost, and nothing that receives.

Premise, restated because a premise stated in one document gets violated in
every other one: **plurality is the product, the registry never designates, and
consumers pin visibly.** Identity is somebody else's here. This registry issues
no account, and a page that implies it does is advertising a model `V2.md`
section 1 declines: `author` stays a free namespace string and claiming is a
separate object. The home page's Account section came out for exactly that
reason, so the test at the bottom of this file is the one that stops it coming
back in under a new name.

**The structural rule, which `tests/test_intake.py` now states for the whole
build.** It was proposed in `artifacts/SIGNIN.md` and moved there on 2026-09-20
when that file was deleted. The difference that matters is not whether an
element is called "auth". It is whether the element is *a target that receives
data from this page*:

- a form, a POST target, an `enctype`, a `formaction`, a field, a file input,
  an `XMLHttpRequest`, a `sendBeacon` or a scripted request with a body
  all receive;
- an anchor whose `href` is an absolute URL to somebody else's site sends this
  page's data nowhere. The browser navigates away and the page is gone.

`tests/test_intake.py` holds the first list for the whole site and
`tests/test_signed_in_page.py` holds the identity-endpoint line. Neither is
touched here and neither is weakened. What this file adds is the same criterion
applied to the one page whose whole job is to explain what signing in is for,
plus a counterexample proving the criterion is not inert.

**This page still ships no script, and that is the interesting part now that
the site holds a session.** `/signed-in/` does the work. Explaining and doing
are two pages, so there is one place in this build that holds a session rather
than two, and the checks below stay exactly as strict as they were.

**Every URL in this file is either root-relative or Hugging Face's own.**
Nothing here fabricates an identity, a date or a number.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "astro" / "dist"
SOURCE = ROOT / "astro" / "src" / "pages" / "sign-in.astro"
BUILT = DIST / "sign-in" / "index.html"


def built() -> str:
    if not BUILT.exists():
        pytest.skip("site not built; run `make site`")
    return BUILT.read_text()


def text_of(html: str) -> str:
    """Reader-visible copy. Script and style survive naive tag-stripping.

    Same shape as `tests/test_pages.py::text_of`, deliberately: a second way of
    reading a page is a second answer to what the page says.
    """
    for tag in ("script", "style"):
        html = re.sub(rf"<{tag}.*?</{tag}>", "", html, flags=re.S)
    return re.sub(r"<[^>]+>", " ", html)


# --------------------------------------------------------------------------- #
# The structural criterion, as a function so it can be shown to bite.

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

# `<script` is not in the table above, and the reason is worth writing down.
# The shared layout ships two scripts on every page, the theme toggle and the
# ordering control, neither of which receives anything. Banning the tag on the
# built page would fail on markup this page did not write, which is a scanner
# that is red for the wrong reason and gets deleted within a week. What is
# checked instead, below, is that this page contributes no script of its own.


def targets_that_receive(html: str) -> list[str]:
    """Everything on this page that could take data off the reader."""
    found = []
    for pattern, what in RECEIVES.items():
        for m in re.finditer(pattern, html, re.I):
            found.append(f"{what} ({m.group(0)!r})")
    return found


def test_the_criterion_flags_the_things_it_claims_to_flag():
    """The bite. A scanner that is green for the wrong reason is the failure
    mode this repository has hit more than once, so the counterexamples are
    checked rather than assumed.

    Each line below is a plausible next edit to the page: a namespace field
    somebody thought would be helpful, a handle box, the button that posts it,
    and the script that would read a session back off the URL.
    """
    counterexamples = [
        '<form action="/claim" method="post">',
        '<input name="namespace" value="" />',
        '<select name="provider"><option>a</option></select>',
        '<textarea name="why"></textarea>',
        '<button type="submit">Claim</button>',
        '<script>fetch("/x", { method: "POST", body: b })</script>',
        '<a href="#" formaction="/claim">Claim</a>',
        'navigator.sendBeacon("/x", d)',
        'new XMLHttpRequest()',
        '<form enctype="multipart/form-data">',
    ]
    for bad in counterexamples:
        assert targets_that_receive(bad), f"the criterion missed {bad!r}"

    # And it does not flag the thing the page is for. An anchor to somebody
    # else's site is not a target: the browser leaves and this page is gone.
    for fine in ('<a href="https://huggingface.co/join">Create an account</a>',
                 '<a href="https://huggingface.co/login">Sign in</a>',
                 '<a href="/about/">About</a>'):
        assert not targets_that_receive(fine), f"the criterion flagged {fine!r}"


def test_the_page_points_out_and_receives_nothing():
    found = targets_that_receive(built())
    assert not found, (
        "the sign-in page grew a target that receives:\n  " + "\n  ".join(found)
        + "\n\nAn outbound anchor is fine and is the whole page. The page that "
        "takes data off the reader is /signed-in/, and keeping the two apart "
        "is what keeps this one checkable by reading it."
    )


def test_the_page_carries_no_identity_endpoint_and_no_session_handling():
    """The half `tests/test_intake.py` cannot see.

    An authorize URL is an anchor, so the write-surface guard says nothing about
    it, and it is the exact thing that matters here. `tests/test_signed_in_page.py`
    holds this for the rest of `astro/dist`, where exactly one page is allowed
    to carry it; this is the other side of that allowance, saying that this page
    is not the one.
    """
    offenders = [
        m.group(0) for m in
        re.finditer(r"/auth/v1/|supabase|signInWithOAuth|access_token|"
                    r"location\.hash", built(), re.I)
    ]
    assert not offenders, (
        f"the sign-in page carries session handling: {offenders}. One page in "
        "this build holds a session and it is /signed-in/. Two would be two "
        "places for a token to live, which is the shape that leaks one."
    )


# --------------------------------------------------------------------------- #
# What the page says, which is the other half of honest.


def body_html(html: str) -> str:
    """The page minus the site chrome, which every page carries and none owns."""
    return re.sub(r"<header.*?</header>", "", html, flags=re.S)


def anchors(html: str) -> list[tuple[str, str]]:
    """(href, link text) for every anchor in the page body."""
    return [
        (m.group(1), " ".join(re.sub(r"<[^>]+>", " ", m.group(2)).split()))
        for m in re.finditer(r'<a\b[^>]*href="([^"]*)"[^>]*>(.*?)</a>',
                             body_html(html), re.S)
    ]


def test_it_offers_no_account_of_its_own():
    """The Account section came out. This is how it does not come back.

    A stranger reading this site cold ranked the greyed-out Account items the
    single most costly thing on it, and `V2.md` opens by asking for them to go
    because they advertise an account model that plan probably makes wrong.

    Checked on what is offered rather than on a word list. The page says
    "nothing to sign up for" and "no password reaches this site", which are the
    opposite of an offer and which a substring scan would call violations. That
    is the trap `CLAUDE.md` names: a grep catching the sentence rather than the
    meaning. So this reads headings and link text, which is where an offer
    lives.
    """
    html = built()
    body = body_html(html)
    # Headings, link text and button text: the three places an offer is made.
    offers = [t for _, t in anchors(html)] + [
        " ".join(re.sub(r"<[^>]+>", " ", m.group(1)).split())
        for pattern in (r"<h[1-3][^>]*>(.*?)</h[1-3]>",
                        r"<button[^>]*>(.*?)</button>")
        for m in re.finditer(pattern, body, re.S)
    ]
    for offer in offers:
        low = offer.lower()
        assert not re.search(r"\bsign ?up\b|\bregister\b", low), (
            f"{offer!r} offers a registration this site does not perform"
        )
        # "Create a Hugging Face account" is fine and is the point. "Create an
        # account" with nobody named is this registry offering one.
        if "create" in low and "account" in low:
            assert "hugging face" in low, (
                f"{offer!r} does not say whose account is being created"
            )

    # Nothing asks a reader for a secret, because nothing here could receive one.
    assert not re.search(r"(choose|enter|set|confirm) a password",
                         text_of(html), re.I)


def test_creating_an_account_is_hugging_face_s_and_leaves_this_site():
    html = built()
    links = anchors(html)
    assert links, "the page has no links, so it signposts nothing"

    outbound = [h for h, _ in links if "://" in h]
    assert outbound, "the page never leaves this site, so it signposts nothing"
    for href in outbound:
        assert href.startswith("https://"), f"{href} is not a fetchable https URL"

    # A dead `href="#"` renders as a working button and is worse than no link.
    # This is the check that a "not built yet" page does not fake the one thing
    # it says it cannot do.
    for href, textish in links:
        assert href.strip() not in ("#", ""), (
            f"{textish!r} is a placeholder link and reads as a real one"
        )
        assert href.startswith(("https://", "/")), (
            f"{href!r} is neither this site's nor an absolute URL"
        )


def test_it_says_what_signing_in_produces_and_what_it_does_not():
    """The one thing the page must not let a reader misread.

    This used to check for "none of this works yet", which was honest while the
    return leg did not exist and became a lie on 2026-09-20 when it did. Its
    replacement, "signing in writes nothing here", lasted until later the same
    day, when the form started posting: signing in on its own still writes no
    submission, but a page whose banner says nothing is written and whose next
    page writes a row is a page a reader is entitled to feel misled by.

    What is checked now is the narrow claim that is true and stays true.
    Signing in publishes nothing and submits nothing; sending is a separate
    press, named as one; and reading needs none of it.
    """
    body = " ".join(text_of(built()).split()).lower()
    assert "signing in publishes nothing and submits nothing" in body
    assert "separate press" in body, (
        "the page no longer says that sending is its own act, which is the "
        "thing that keeps the banner above it honest"
    )
    assert "dated reading" in body
    assert "needs none of it" in body, (
        "reading stays anonymous, and the page that explains signing in is "
        "where somebody learns they do not have to"
    )


def test_the_namespace_is_shown_and_never_offered():
    """`DECISIONS.md` 2026-09-19. Shown, not offered: no field, and no default
    to type over. The absence of a field is checked structurally above; this
    checks that the page says why, because a rule with no stated cost has not
    been thought through."""
    body = " ".join(text_of(built()).split()).lower()
    assert "no box" in body or "there is no field for it" in body
    assert "pseudonym" in body, (
        "the page has to name what this rule makes impossible to express"
    )


def test_a_membership_is_dated_and_never_called_verified():
    """Nothing rechecks a membership, so a word implying something does is the
    word that turns dated evidence into a standing. Same rule as
    `tests/test_signed_in_page.py` applies to the page that does the reading."""
    html = built()
    assert not re.search(r"\bverif", text_of(html), re.I), (
        "'verified' claims a freshness this registry does not have"
    )
    body = " ".join(text_of(html).split()).lower()
    assert "when it said it" in body or "on a day" in body


def test_the_provider_is_carried_rather_than_declared_the_permitted_one():
    """No closed enum, including provider names. The page names Hugging Face
    because that is what was built, and must not turn that into a set."""
    body = " ".join(text_of(built()).split()).lower()
    for closed in ("supported providers", "allowed providers",
                   "approved providers", "one of the following providers"):
        assert closed not in body, f"{closed!r} is a closed enum in prose"
    assert "not a list of permitted ones" in body


def test_claiming_is_named_as_the_act_that_matters():
    """Signing in on its own gives somebody nothing, and a page that leads with
    the button implies the button is the point."""
    body = " ".join(text_of(built()).split()).lower()
    assert "claim a namespace" in body
    assert "more than one account can claim the same namespace" in body, (
        "a namespace permits an unlimited number of claimants, and the page "
        "that explains claiming is where a reader learns that"
    )


def test_the_page_is_reachable():
    """A page nothing links to is a page nobody reads. `falsifier/links.py`
    proves every link resolves; this proves this one is made."""
    if not DIST.exists():
        pytest.skip("site not built; run `make site`")
    linkers = [
        p.relative_to(DIST) for p in DIST.rglob("*.html")
        if 'href="/sign-in/"' in p.read_text(errors="ignore")
    ]
    assert linkers, "nothing on the site links to /sign-in/"


def test_the_page_contributes_no_script_of_its_own():
    """The return leg is the only reason this page would want script, so the
    absence of script is the absence of the return leg, checked at the source
    where it would be written rather than in bundled output."""
    source = SOURCE.read_text()
    assert "<script" not in source, (
        "the sign-in page grew a script. Reading a session out of a redirect "
        "is what that script would be for, and /signed-in/ already does it. "
        "A second copy is a second place for a token to live."
    )


def test_the_source_says_why_there_is_no_session_handling():
    """The next person to open this file will reach for the return leg. The
    reason it is absent has to be in the file rather than only in a report."""
    source = SOURCE.read_text()
    assert "output: \"static\"" in source or 'output: "static"' in source
    assert "return leg" in source
