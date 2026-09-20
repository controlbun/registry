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
sys.path.insert(0, str(ROOT / "tests"))

import probe  # noqa: E402
from controlbun import views  # noqa: E402

DIST = ROOT / "astro" / "dist"

# One of each shape, named by what it is rather than by its path.
#
# These pointed at fixture pages until 2026-09-19 and every one of them is a
# real page now. That is worth more than it sounds: seven of these tests were
# skipping, not failing, because `page()` skips a path that was never built, so
# the module went quiet the moment the fixture corpus came out. A test file that
# skips is a test file that says nothing, which is the same defect as an inert
# check one level up.
#
# What the real corpus cannot show is here rather than hidden. Nobody has
# reported a trait score with no coherence measure beside it, so no built page
# carries the uninterpretable state and the test for it works two levels down.
# See `test_a_score_with_no_coherence_beside_it_is_uninterpretable`.
PAGES = {
    # Four takes on one word by one author. The bare-label view, and the only
    # page on the site with more than one claimant on it.
    "label": "models/allenai/Olmo-3-1125-32B/pro-human/index.html",
    # One claimant, which is the other shape a label view has to render well.
    "single": "models/meta-llama/Llama-3.3-70B-Instruct/trauma/index.html",
    # No confound audit and no transfer ratio: that battery was run on the three
    # layer-32 directions and not on this one.
    "unmeasured": "soham/allenai/Olmo-3-1125-32B/pro-human/L24/index.html",
    "submission": "soham/allenai/Olmo-3-1125-32B/pro-human/meandiff/index.html",
}

# The four versions on the label page above, which is what "every claimant"
# means in a corpus where every claimant is the same person.
VERSIONS = ("meandiff", "logistic", "lda", "L24")


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
    for version in VERSIONS:
        assert version in body, (
            f"{version} claims this label and is not on its page"
        )


def test_a_bare_label_says_it_does_not_resolve():
    assert "does not resolve to an artifact" in text_of(page("label"))


def test_a_label_view_counts_people_separately_from_submissions():
    """Four versions by one person are not four claimants, and the page says so.

    This is the copy the fixture removal made dishonest. The lede read "N
    claimants" off the row count, which was the number of people while every
    label had one submission each, and stopped being the number of people the
    moment one author published four takes on one word. Left alone it would
    have read as four people disagreeing on a site where the disagreement is
    exactly what nobody has done yet.

    The single-claimant page has to say the plainer thing: nobody else has
    claimed this word here. That is a fact about a new registry and not an
    apology, and it is computed from the export so it disappears on its own
    when a second claimant arrives.
    """
    many = text_of(page("label"))
    assert re.search(r"4 submissions\s+by\s+1 author", " ".join(many.split())), (
        "the label view counts rows and calls them claimants, which reads as "
        "four people on a page holding one author's four versions"
    )
    assert "Nobody else has claimed this word" in " ".join(many.split())

    one = " ".join(text_of(page("single")).split())
    assert "1 submission by 1 author" in one
    assert "Nobody else has claimed this word" in one


def test_absent_transfer_reads_as_absent_not_zero():
    body = text_of(page("unmeasured"))
    assert "not measured" in body or "no score" in body, (
        "no confound audit or transfer ratio was run against this artifact and "
        "the page must say so"
    )
    for path in every_page():
        assert "0.0000" not in text_of(path.read_text()), (
            f"{path.name} prints a zero where a measurement was not taken"
        )


def test_no_page_claims_a_corpus_it_does_not_have():
    """The marker is absent because nothing is fabricated, and that is checked.

    This asserted the opposite until 2026-09-19: "Synthetic corpus" had to
    appear, because everything on the page was. Inverting it rather than
    deleting it keeps the property that matters in both directions, which is
    that the banner describes the corpus. A banner calling a real measurement
    invented is the expensive direction and the one `DECISIONS.md` 2026-09-14
    was written about.

    The branch that prints it is asserted to still exist, in the layout source,
    because the phrase disappearing from every page is exactly what a deleted
    banner looks like from here.
    """
    payload = json.loads(
        (ROOT / "astro" / "src" / "data" / "controlbun.json").read_text())

    marked = [p.relative_to(DIST) for p in every_page()
              if "Synthetic corpus" in text_of(p.read_text())]
    if payload["any_synthetic"]:
        assert marked, (
            "the corpus holds a fabricated row and no page says so"
        )
        return

    assert not marked, (
        "no row in the corpus is marked synthetic and these pages say otherwise, "
        "which tells a reader a real measurement was invented: "
        + ", ".join(str(m) for m in marked)
    )
    layout = (ROOT / "astro" / "src" / "layouts" / "Base.astro").read_text()
    assert "Synthetic corpus" in layout, (
        "the banner is gone from the layout, so a fabricated submission would "
        "publish with nothing on the page saying so"
    )


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


def test_a_score_with_no_coherence_beside_it_is_uninterpretable(tmp_path):
    """Two levels down, because no page in this corpus is in that state.

    This read a fixture page and asserted "uninterpretable" appeared on it
    where a fabricated trait score had no coherence measure beside it. Nobody
    real has reported that pair, so the page does not exist and the test was
    skipping rather than failing, which is the quiet version of not running.

    So it is checked where it is decided and where it is drawn. `score_state`
    is computed in Python and the templates receive the state rather than the
    number, which is the arrangement that makes the invariant hold without any
    template having to remember it. The probe corpus carries the row the real
    one does not.
    """
    conn = probe.build(tmp_path / "probe.db", tmp_path)
    try:
        row = conn.execute(
            "SELECT * FROM submission WHERE author = 'probe-d'").fetchone()
        view = views.claimant_view(conn, row)
    finally:
        conn.close()

    assert view["trait_score"] is not None, (
        "the probe row reports no trait score, so this proves nothing about "
        "what happens when one is reported without a coherence measure"
    )
    assert view["coherence_score"] is None
    assert view["score_state"] == "uninterpretable", (
        "a trait score with no coherence measure beside it has to reach the "
        "page as a state rather than as a number; judge agreement collapses on "
        "degenerate text and an unpaired score is a broken instrument rather "
        "than a small effect"
    )

    # And the templates still refuse to print the number in that state. Both
    # components that draw a trait measure gate on the state, so a page cannot
    # reach a bare number by holding the value.
    for name in ("ArtifactCard.astro", "Claimant.astro"):
        source = (ROOT / "astro" / "src" / "components" / name).read_text()
        assert re.search(
            r'score_state\s*===\s*"reportable"\s*&&\s*fmt\(\s*c\.trait_score',
            source,
        ), f"{name} prints a trait score without gating on the score state"
        assert 'score_state === "uninterpretable"' in source, (
            f"{name} no longer renders the uninterpretable state at all"
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
    from controlbun import order

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
        (ROOT / "astro" / "src" / "data" / "controlbun.json").read_text())
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


def test_a_reason_for_an_absence_renders_beside_the_absence_and_is_marked():
    """An absence with an account of it reads as both, not as one or the other.

    The absence still says absent, which is invariant 7 and must not change.
    What is new is the sentence next to it, which is the author's own prose and
    carries the file names and line numbers that make it worth anything, so it
    sits inside a `data-authored` region like every other quoted run on this
    site.

    Skipped rather than asserted when no submission in the corpus records one:
    most absences have none, no fixture invents one, and a test that demanded a
    reason exist would be the required field arriving through the suite.
    """
    payload = json.loads(
        (ROOT / "astro" / "src" / "data" / "controlbun.json").read_text())
    accounted = [
        (c, field, reason)
        for entry in payload["labels"] for c in entry["claimants"]
        for field, reason in (c.get("absences") or {}).items()
    ]
    if not accounted:
        pytest.skip("no absence in the corpus carries a reason")

    pages = {p: p.read_text() for p in every_page()}
    for claimant, field, reason in accounted:
        ref = f"{claimant['author']}/{claimant['label']}@{claimant['version']}"
        text = " ".join(reason.split())
        shown = [body for body in pages.values() if text[:60] in
                 " ".join(text_of(body).split())]
        assert shown, f"{ref}: nothing renders the reason recorded for {field}"
        for body in shown:
            assert text[:60] not in " ".join(
                text_of(body, authored=False).split()), (
                f"{ref}: the reason for {field} renders outside a "
                "`data-authored` region, so its file names and line numbers "
                "are scanned as figures this registry derived"
            )
            assert "not recorded" in body, (
                f"{ref}: the reason replaced the absence instead of standing "
                "beside it. An absence renders as its own state, and an "
                "explanation is not a value."
            )
