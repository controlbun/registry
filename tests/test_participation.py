"""Somebody who only checks other people's work still exists here.

`/carol/` was a 404 for days. carol owned an eval suite and ran the only attack
in the corpus, and her name was linked from the page that attack appears on, and
there was nothing at the other end. Same for gus and hana, who filed the support
cards. The cause was not missing data: an owner page existed because someone had
published a submission, so anyone who contributed evidence rather than artifacts
was unlinkable by construction.

That is the wrong way round for this registry. The evidence layer is the thing
nobody else has, it is written by people pointing their suites at other people's
submissions, and a reader weighing an attack cannot weigh the attacker if the
attacker has no page.

**Where these properties live now.** carol, gus and hana were fixtures and left
on 2026-09-19 with the rest of the synthetic corpus. The real corpus has no
evidence-only participant at all: one author, five submissions, no attacks, no
support cards, nobody who took part without publishing. The state cannot be put
on a page here, and a test that sat waiting for one would be inert, which is the
failure this repository has shipped often enough to have a name for.

So the file splits across three levels, and each one says which it is:

  * **The data**, against `tests/probe.py`, which holds the participants the
    real corpus does not. Whether an owner entry exists because somebody took
    part is decided in `controlbun.export` and not in a template, so this is the
    level the property actually lives at.
  * **The page**, against the real build. The owner page that does exist has to
    render an absence as a sentence rather than as an empty table, and no column
    on it may tally anybody.
  * **The template**, against the source of `astro/src/pages/[...path].astro`.
    The branches that render the states this corpus cannot reach are asserted to
    still be there.

The third is weaker than reading a built page and is written down as weaker: it
catches a branch someone deleted and it would not catch a branch that renders
wrong. It is here because the alternative is no check at all on the half of this
page nobody can currently see.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tests"))

import probe  # noqa: E402
from controlbun import export  # noqa: E402

DIST = ROOT / "astro" / "dist"
OWNER_TEMPLATE = ROOT / "astro" / "src" / "pages" / "[...path].astro"
OWNERS_INDEX_TEMPLATE = ROOT / "astro" / "src" / "pages" / "owners" / "index.astro"


def text_of(html: str) -> str:
    for tag in ("script", "style"):
        html = re.sub(rf"<{tag}.*?</{tag}>", "", html, flags=re.S)
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html))


# --------------------------------------------------------------------------- #
# The data. Against the probe corpus, because the real one has nobody in this
# state and the question is what the exporter does when somebody is.


@pytest.fixture(scope="module")
def probed(tmp_path_factory):
    """The export the probe corpus produces, built the way the site builds it."""
    conn = probe.build(tmp_path_factory.mktemp("participation") / "probe.db")
    return export.build(conn)


@pytest.fixture(scope="module")
def evidence_only(probed):
    """Everyone in the probe corpus who took part without publishing.

    Derived rather than listed. This file named carol, gus and hana, and a test
    that names rows is a test that dies with them; what it is about is the
    shape. The assertion that the set is non-empty is the guard that keeps the
    parametrized cases below from passing on an empty list.
    """
    people = sorted(
        o["owner"] for o in probed["owner_index"] if not o["submissions"]
    )
    assert people, (
        "the probe corpus holds nobody who took part without publishing, so "
        "every case below would pass on an empty set"
    )
    return people


def entry(probed: dict, owner: str) -> dict:
    found = next((o for o in probed["owner_index"] if o["owner"] == owner), None)
    assert found is not None, (
        f"{owner} took part and has no entry in the owner index, so there is "
        "nothing for their name to link to"
    )
    return found


def test_the_probe_corpus_holds_the_three_shapes(evidence_only):
    """The attacker and the two support reporters, by the roles they play.

    Named here and nowhere else below, so the cases that follow read off the
    derived set and this one asserts the derived set is the set that was meant.
    """
    assert set(evidence_only) >= {
        "probe-attacker", "probe-user-one", "probe-user-two"
    }, (
        f"the probe corpus lost an evidence-only participant: {evidence_only}"
    )


def test_an_evidence_only_participant_has_an_entry(probed, evidence_only):
    """The original failure, at the level it was actually caused.

    An owner existed because somebody had published an artifact. Everyone else
    was linked by name from the pages their work appears on and had nothing at
    the other end. `controlbun.export` is where that is decided.
    """
    for owner in evidence_only:
        assert entry(probed, owner)


def test_no_submissions_is_a_state_and_not_an_empty_profile(probed, evidence_only):
    """Zero submissions carries the rest of the record rather than blanking it.

    An entry with an empty submission list, an empty label list and a date is a
    person who did things here. An entry with no date would be a person the
    page cannot say anything about, and the template would have nothing to put
    in the sentence it writes instead of the table.
    """
    for owner in evidence_only:
        person = entry(probed, owner)
        assert person["submissions"] == []
        assert person["labels"] == [], (
            "somebody who published nothing claims no label; a label here would "
            "have come from work that is not theirs"
        )
        assert person["latest"], (
            "their evidence is dated and the entry has to carry a date, or the "
            "ordering reads them as never having been here"
        )
        assert person["engagement"] == 0, (
            "engagement is scrutiny received on your own submissions. Somebody "
            "with none cannot receive any, and a number here would be counting "
            "what they did to other people as something done to them"
        )


def test_the_entry_names_what_the_attacker_actually_did(probed):
    """Their attack, their suite, and in full what they attacked.

    The reference has to carry the model. A reader weighing an attack against
    `probe-a/probe-trait@v1` cannot tell which artifact that was without it,
    because one author may claim one label on two models.
    """
    person = entry(probed, "probe-attacker")

    assert person["attacks_made"], "the attacker's attack is not on their entry"
    attack = person["attacks_made"][0]
    assert attack["method"] == "alternative-confound-axis"
    assert attack["subject"] == "probe-a/placeholder/does-not-resolve-1b/probe-trait@v1", (
        "what they attacked is not named in full: a reference without the model "
        "does not say which artifact it was"
    )
    assert attack["disposition"], (
        "the attacker's own reading of what they found is not recorded, so the "
        "page could only show that an attack happened"
    )

    assert person["suites"], "their eval suite is not on their entry"
    assert person["suites"][0]["suite"] == "probe-adversarial@v1"

    assert person["evaluations"], (
        "they pointed their own suite at somebody else's submission and the "
        "entry does not say so"
    )


def test_the_entry_names_what_a_support_reporter_used(probed):
    """Applied use, with the version they pinned.

    A support card is about one frozen submission. Without the version it reads
    as a report about the label, which is a claim about everybody's work.
    """
    person = entry(probed, "probe-user-one")
    assert person["support_given"], "their support card is not on their entry"
    card = person["support_given"][0]
    assert card["subject"].endswith("@v1"), (
        f"the version they used is not named: {card['subject']}"
    )
    assert card["purpose"], "what they used it for is not recorded"


def test_taking_part_without_publishing_still_reaches_the_owner_index(
    probed, evidence_only
):
    """The index is everyone who took part, not everyone who shipped something."""
    listed = {o["owner"] for o in probed["owner_index"]}
    missing = [o for o in evidence_only if o not in listed]
    assert not missing, f"{missing} took part and are missing from the owner index"


def test_an_attack_count_is_not_an_attackers_score(probed):
    """Attacking a lot is not an achievement anything ranks anyone by.

    At the data level this is the absence of an aggregate: the attacks are a
    list of events, each with what it was against, by what method and when.
    There is no number over them, so there is nothing for a template to sort on
    even if somebody wanted to.
    """
    person = entry(probed, "probe-attacker")
    for key in person:
        assert not re.search(r"(count|score|rank|total)", key), (
            f"the owner entry carries {key!r}, which is a tally of the person "
            "rather than a record of what they did"
        )
    assert isinstance(person["attacks_made"], list)


# --------------------------------------------------------------------------- #
# The page. Against the real build, so only the states this corpus reaches.


def owners_on_the_index() -> list[str]:
    """The names `/owners/` lists, read out of the table rather than the page.

    Scoped to the table body on purpose. Every href on the page was the obvious
    reading and it collects the site navigation too, so `/about/` came back as
    a person. Narrowing to the rows is also the truthful reading: the table is
    the list of owners and the nav is the same on every page.
    """
    index = DIST / "owners" / "index.html"
    if not DIST.exists() or not index.exists():
        pytest.skip("site not built; run `make site`")
    body = re.search(r"<tbody[^>]*>(.*?)</tbody>", index.read_text(), re.S)
    assert body, "no owner table on /owners/, so nothing below proves anything"
    named = sorted(set(re.findall(r'href="/([^/"]+)/"', body.group(1))))
    assert named, "no owner is listed on /owners/, so this proves nothing"
    return named


def owner_pages() -> list[Path]:
    return [DIST / owner / "index.html" for owner in owners_on_the_index()]


def test_every_owner_named_on_the_index_has_a_page():
    """The link check covers this too, and this covers the reason for it.

    `falsifier/links.py` would catch a dead `/name/` href. What it cannot say is
    that the missing page belongs to a person, which is the half that made the
    original failure a statement about the corpus rather than a broken button.
    """
    for owner in owners_on_the_index():
        assert (DIST / owner / "index.html").exists(), (
            f"/{owner}/ is listed by name on /owners/ and was not built"
        )


def test_an_absence_on_an_owner_page_reads_as_a_sentence():
    """The property carol's page was for, on the page this corpus does have.

    Nobody here has evaluated, attacked or reported use of anybody else's
    submission, which is the mirror of nobody having published one: a section
    with nothing in it. It has to say so in words. An empty table reads as a
    failed query, and on this site a failed query and a true zero are different
    claims about the corpus.
    """
    pages = owner_pages()
    assert pages, "no owner page was built"
    # Bound to the owner's own name, which is how the template writes it. A bare
    # "has not" would also match a caption somewhere and pass on the wrong
    # sentence, which is the mistake the header scan below already records.
    found = [
        p for p in pages
        if f"{p.parent.name} has not " in text_of(p.read_text())
    ]
    assert found, (
        "no owner page states an absence in words. Every owner in this corpus "
        "has an empty section somewhere, and an empty table in its place is the "
        "state this test exists to keep off the page"
    )


def test_no_column_on_an_owner_page_tallies_the_person():
    """The only thing that would actually rank a participant: a column of totals.

    Two earlier versions of this were wrong in opposite ways. The first asserted
    a disclaimer sentence was present, which is the weak shape: a page can carry
    the sentence and rank anyway, and the test broke when the sentence was cut
    for being the site arguing with its reader rather than when the page
    changed. The second scanned the prose for words like "score" and failed on
    the synthetic banner, which said "Scores are repeated-digit decimals".
    Scanning prose for single words finds the word, not the meaning.

    So this reads the table headers, which is the one place a tally would have
    to appear.
    """
    for page in owner_pages():
        raw = page.read_text()
        headers = [
            re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", h)).strip().lower()
            for h in re.findall(r"<th[^>]*>(.*?)</th>", raw, re.S)
        ]
        assert headers, f"no table on /{page.parent.name}/, so this proves nothing"
        for h in headers:
            assert not any(w in h for w in ("count", "score", "rank", "total")), (
                f"a column headed {h!r} on /{page.parent.name}/ would read as a "
                "tally of the person rather than as one more thing they did"
            )


# --------------------------------------------------------------------------- #
# The template. Weaker than reading a page, and here because the states below
# are unreachable in this corpus and would otherwise be checked by nothing.


def test_the_template_still_writes_the_no_submissions_sentence():
    """The branch carol's page needed, held in place while nobody needs it.

    This is the one the data-level cases above cannot reach: the exporter
    produces an entry with an empty submission list and something has to turn
    that into a sentence. Deleting the branch would leave an empty table, which
    is what the whole file is about, and nothing built today would notice.
    """
    source = OWNER_TEMPLATE.read_text()
    assert "owner.submissions.length === 0" in source, (
        "no branch on an empty submission list, so a participant who published "
        "nothing renders as a table with no rows"
    )
    assert "has not published an artifact" in source, (
        "the branch exists and no longer says anything, which is the empty "
        "table arriving under a conditional"
    )


def test_the_ordering_bar_is_gated_on_there_being_something_to_order():
    """A bar over an empty table is the dead control returning.

    carol's page had one orderable list and it was empty. The gate is an
    expression in the template and there is currently no built page where it
    evaluates false, so this reads the expression.
    """
    source = OWNER_TEMPLATE.read_text()
    assert re.search(r"ordering=\{owner\.submissions\.length\s*>\s*0\}", source), (
        "the ordering control on an owner page is not gated on the owner having "
        "submissions, so it renders over an empty list"
    )


def test_the_template_still_renders_each_kind_of_participation():
    """Attacks, independent measurements and applied use each have their own block.

    Three ways of taking part that are not publishing. Folding them into one
    list would lose what somebody actually did, and the probe corpus proves the
    exporter still separates them; this proves the page still does.
    """
    source = OWNER_TEMPLATE.read_text()
    for heading in ("Attacks", "Independent measurements", "Applied use"):
        assert f"<h3>{heading}</h3>" in source, (
            f"the {heading!r} block is gone from the owner page, so that kind of "
            "participation renders as nothing"
        )
    assert "has not evaluated, attacked or reported use" in source, (
        "no sentence for somebody who has done none of the three"
    )


def test_the_owners_index_still_writes_no_labels_as_absence():
    """An owner with no labels reads as absence rather than as an empty cell.

    Unreachable in this corpus, because the only owner claims two labels. It was
    reachable when carol was here and it will be again the first time somebody
    attacks a submission without publishing one.
    """
    source = OWNERS_INDEX_TEMPLATE.read_text()
    assert "none claimed" in source, (
        "an owner with no labels renders as a blank cell, which reads as a "
        "failed lookup rather than as a fact about what they have published"
    )
