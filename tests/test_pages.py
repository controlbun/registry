"""What a reader is actually shown.

The invariant tests catch banned constructs in the templates. These check the
rendered output, which is the only place the rules finally bind: a template can be
clean and still print a number it should not.

These ran against the Jinja frontend until it was retired, which meant they were
checking a frontend nobody visited while the shipped one went unchecked. They now
read the built Astro pages, so a claim here is a claim about the site.

`make verify` builds the site before running the suite. Running `make test` alone
against a stale `astro/dist` checks the last build rather than the tree, which is
why the build is a gate step and not a fixture: rebuilding per test session would
mean an npm install inside pytest.
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

DIST = ROOT / "astro" / "dist"

# One of each shape, named by what it is rather than by its path.
PAGES = {
    "label": "models/placeholder/other-architecture-7b/refusal/index.html",
    "kindness": "models/placeholder/does-not-resolve-1b/kindness/index.html",
    # erik reported a trait score and no coherence, so this page is the one that
    # has to refuse to print a number.
    "unpaired": "erik/placeholder/other-architecture-7b/refusal/v1/index.html",
    # fern reported nothing at all.
    "unmeasured": "fern/placeholder/other-architecture-7b/refusal/v1/index.html",
}


def page(name: str) -> str:
    path = DIST / PAGES[name]
    if not path.exists():
        pytest.skip(f"{path.relative_to(ROOT)} not built; run `make site`")
    return path.read_text()


def every_page() -> list[Path]:
    if not DIST.exists():
        pytest.skip("site not built; run `make site`")
    return sorted(DIST.rglob("index.html"))


AUTHORED = re.compile(r"<(\w+)[^>]*\sdata-authored[^>]*>.*?</\1>", re.S)


def text_of(html: str, *, authored: bool = True) -> str:
    """Reader-visible copy only.

    Script and style contents survive naive tag-stripping and are not text a reader
    sees. Leaving CSS in produced a false positive once already: the hex color
    #1a1a1a contains "#1" and read as a ranking marker.

    `authored=False` also drops the regions the page attributes to an author.
    Whether that is right depends entirely on the question being asked, so it
    is a parameter rather than a default: what a page *shows* includes quoted
    prose, and what the *registry asserts* does not.
    """
    for tag in ("script", "style"):
        html = re.sub(rf"<{tag}.*?</{tag}>", "", html, flags=re.S)
    if not authored:
        html = AUTHORED.sub(" ", html)
    return re.sub(r"<[^>]+>", " ", html)


def test_every_claimant_appears():
    body = text_of(page("label"))
    for author in ("dana", "erik", "fern"):
        assert author in body, f"{author} claims this label and is not on its page"


def test_a_bare_label_says_it_does_not_resolve():
    assert "does not resolve to an artifact" in text_of(page("label"))


def test_absent_transfer_reads_as_absent_not_zero():
    body = text_of(page("unmeasured"))
    assert "not measured" in body or "no score" in body, (
        "fern measured nothing and the page must say so"
    )
    for path in every_page():
        assert "0.0000" not in text_of(path.read_text()), (
            f"{path.name} prints a zero where a measurement was not taken"
        )


def test_synthetic_corpus_is_announced():
    assert "Synthetic corpus" in text_of(page("label"))


def test_no_angle_is_shown_until_the_reader_points_the_column():
    """The static page ships the column empty.

    Astro replaced the quadratic pairwise table with a column the reader aims at a
    reference of their choosing, so nothing arrives pre-compared. A page that
    shipped angles already filled in would be the registry choosing the comparison,
    which is the pairwise table again with fewer cells.
    """
    body = text_of(page("label"))
    assert "Similarity" in body
    assert not re.search(r"\b0\.\d{4}\b", body), (
        f"an angle is printed before the reader asked for one: {body[:200]!r}"
    )


def test_the_code_that_prints_an_angle_also_prints_its_caveat():
    """The caveat travels with the number, not with the page.

    Both are injected by the same script when the reader picks a reference, which
    is the only arrangement where the invariant cannot come apart: there is no
    state in which a number has been written and the caveat has not.
    """
    raw = page("label")
    assert "not evidence" in raw, "no caveat ships with the similarity column"
    writes = raw.index("not evidence")
    scripts = [m for m in re.finditer(r"<script.*?</script>", raw, flags=re.S)]
    assert any(m.start() < writes < m.end() for m in scripts), (
        "the caveat is static copy while the number is injected, so a reader can "
        "reach a state where the number is on screen and the caveat is not"
    )


def test_nothing_is_ranked():
    """What the registry asserts, not what an author wrote inside quotation.

    Read with authored prose stripped, because this asks whether the registry
    ranks anything and a definition is one author describing their own work. A
    real submission contains the phrase "~25-token 1st-person retrospective
    reports", and a substring scan called that an ordinal and failed the build.
    That is the trap `CLAUDE.md` names about "better" and "best": a word list
    catching the sentence rather than the meaning. The marking that makes this
    separable is the same `data-authored` the falsifier reads.
    """
    for path in every_page():
        body = text_of(path.read_text(), authored=False).lower()
        # The word "rank" appears in captions saying nothing is ranked. What must
        # be absent is an actual ordering: positions, ordinals, a composite.
        for marker in ("#1", "#2", "1st", "2nd", "overall score",
                       "composite", "top pick", "ranked #"):
            assert marker not in body, (
                f"{path.name} implies an ordering via {marker!r}"
            )
        # "winner" is checked by construction rather than as a bare word. The home
        # page says the registry "does not pick a winner", which is the thesis, and
        # a literal match called that a violation.
        assert not re.search(r"\bwinner\s*[:=]|\bthe winner is\b", body), (
            f"{path.name} designates a winner"
        )


def test_the_active_ordering_is_named_on_screen():
    """Both names, not either.

    This used to assert that `data-order=` appeared in the markup and called that
    "a reader must be able to change the ordering". It was true of a control with
    no handler behind it, which is what shipped. Behavior is tested by running the
    page's own script in test_ordering_control.py; what belongs here is the copy.
    A bar naming only the active ordering leaves the alternative undiscoverable.
    """
    body = text_of(page("label"))
    assert "ordered by" in body.lower(), "the active ordering must be named on screen"
    assert "Recently added" in body
    assert "Trending" in body


def test_ordering_explains_itself():
    body = text_of(page("label")).lower()
    assert "newest-first" in body or "decayed by age" in body, (
        "an ordering the reader cannot interrogate is a verdict wearing a label"
    )


def test_score_without_coherence_renders_as_uninterpretable():
    body = text_of(page("unpaired"))
    assert "uninterpretable" in body
    assert "0.5555" not in body, (
        "a trait score with no coherence measure beside it must not print as a "
        "number; judge agreement collapses on degenerate text and an unpaired "
        "score is a broken instrument rather than a small effect"
    )


def test_a_rendered_date_matches_its_own_datetime_attribute():
    """Every date on the site rendered a day early outside UTC.

    Timestamps are stored as UTC midnight and `toLocaleDateString` resolves them
    in the reader's zone, so west of Greenwich `2026-09-12T00:00:00Z` printed as
    "Sep 11, 2026". The machine-readable attribute was correct the whole time and
    only the human text was wrong, which is the version of this nobody notices and
    the version a reader acts on.
    """
    months = {
        "Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6,
        "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12,
    }
    seen = 0
    for path in every_page():
        for iso, shown in re.findall(
            r'<time datetime="([^"]+)"[^>]*>([^<]+)</time>', path.read_text()
        ):
            stamp = datetime.fromisoformat(iso.replace("Z", "+00:00"))
            m = re.match(r"([A-Z][a-z]{2}) (\d{1,2})(?:, (\d{4}))?", shown.strip())
            assert m, f"{path.name}: unparsed date text {shown!r}"
            seen += 1
            assert (months[m.group(1)], int(m.group(2))) == (stamp.month, stamp.day), (
                f"{path.name}: shows {shown.strip()!r} for {iso}. The stored "
                "timestamp and the text a reader sees are different days."
            )
            if m.group(3):
                assert int(m.group(3)) == stamp.year

    assert seen, "no dates rendered anywhere, so this proves nothing"


def test_the_navigation_offers_nothing_it_cannot_deliver():
    """A greyed-out link is worse than no link.

    The home page carried an Account section (Profile, Submissions, Settings) and
    a Resources section (Getting started, Documentation, Publishing a submission),
    all marked "not in v0". A stranger reading the site cold ranked that the single
    most costly thing on it: the site named their three needs by name and marked
    all three unavailable, leaving nowhere to go but data it had already declared
    fabricated.

    Checked against the built page rather than the source, because what matters is
    what a reader is offered.
    """
    home = DIST / "index.html"
    if not home.exists():
        pytest.skip("site not built; run `make site`")
    html = home.read_text()

    assert "not in v0" not in html, "the navigation still advertises what it lacks"
    for promised in ("Getting started", "Publishing a submission", "Settings"):
        assert promised not in html, f"{promised!r} is offered and does not exist"

    # Every remaining destination resolves. `falsifier/links.py` proves this for
    # the whole site; this keeps the home page honest on its own.
    for real in ('href="/models/"', 'href="/owners/"', 'href="/about/"'):
        assert real in html, f"{real} is missing from the navigation"


def test_the_ordering_bar_does_not_quote_an_uninterpretable_threshold():
    """It read "under the 100 at which engagement starts to mean anything".

    100 is a threshold somebody chose. `order.py` justifies it only as the point
    below which "engagement data is too thin to mean anything", which is honest
    about being a judgment and does not derive the number. Printing it gave the
    reader a figure they could not interpret and a question with no answer, on
    every list page. The corpus size is a fact and stays.
    """
    from registry import order

    for path in every_page():
        body = text_of(path.read_text())
        if "Ordered by" not in body:
            continue
        assert f"the {order.CORPUS_THRESHOLD}" not in body, (
            f"{path.relative_to(DIST)} quotes the threshold as if it were derived"
        )


def test_every_definition_is_marked_as_the_authors_words():
    """Authored prose is excluded from the number scan, so it has to be marked.

    Proven to bite: removing `data-authored` from `ArtifactCard.astro` and
    rebuilding produces sixteen falsifier failures, the five quoted figures in
    a real definition plus a fixture-value collision plus one line per
    claimant. The exclusion is only worth as much as the marking, so the
    marking is a test and not a convention.
    """
    payload = json.loads(
        (ROOT / "astro" / "src" / "data" / "registry.json").read_text())
    definitions = [
        " ".join((c.get("definition") or "").split())
        for entry in payload["labels"] for c in entry["claimants"]
    ]
    definitions = [d for d in definitions if d]
    assert definitions, "no definitions in the corpus, so this test is inert"

    unmarked = " ".join(
        " ".join(text_of(p.read_text(), authored=False).split())
        for p in every_page()
    )
    for text in definitions:
        assert text[:60] not in unmarked, (
            f"a definition renders outside a `data-authored` region: {text[:60]!r}"
        )
