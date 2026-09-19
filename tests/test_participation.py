"""Somebody who only checks other people's work still exists here.

`/carol/` was a 404 for days. carol owns an eval suite and ran the only attack in
the fixture corpus, and her name is linked from the page that attack appears on,
and there was nothing at the other end. Same for gus and hana, who filed the
support cards. The cause was not missing fixture data: an owner page existed
because someone had published a submission, so anyone who contributed evidence
rather than artifacts was unlinkable by construction.

That is the wrong way round for this registry. The evidence layer is the thing
nobody else has, it is written by people pointing their suites at other people's
submissions, and a reader weighing an attack cannot weigh the attacker if the
attacker has no page.

These check the three things that has to mean: the pages exist, they say what the
person actually did, and zero submissions renders as a fact rather than as an
empty profile.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

DIST = ROOT / "astro" / "dist"

# Everyone in the corpus who took part without publishing an artifact.
EVIDENCE_ONLY = {
    "carol": "ran the only attack, and owns an eval suite",
    "gus": "filed a support card",
    "hana": "filed a support card",
}


def page(owner: str) -> str:
    path = DIST / owner / "index.html"
    if not DIST.exists():
        pytest.skip("site not built; run `make site`")
    assert path.exists(), (
        f"/{owner}/ was not built, but {owner} is linked by name from the pages "
        f"their work appears on: {EVIDENCE_ONLY.get(owner, 'they participated')}"
    )
    return path.read_text()


def text_of(html: str) -> str:
    for tag in ("script", "style"):
        html = re.sub(rf"<{tag}.*?</{tag}>", "", html, flags=re.S)
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html))


@pytest.mark.parametrize("owner", sorted(EVIDENCE_ONLY))
def test_an_evidence_only_participant_has_a_page(owner):
    assert page(owner)


@pytest.mark.parametrize("owner", sorted(EVIDENCE_ONLY))
def test_no_submissions_reads_as_a_fact_not_an_empty_profile(owner):
    body = text_of(page(owner))
    assert "has not published an artifact" in body, (
        "a page with no submissions must say so in words; an empty table reads as "
        "a failed query"
    )
    assert "none claimed" not in body, "that copy belongs on the owners index"


def test_carols_page_names_what_she_actually_did():
    body = text_of(page("carol"))
    assert "Attacks" in body
    assert "alternative-confound-axis" in body, "her attack method is not shown"
    assert "alice/placeholder/does-not-resolve-1b/kindness@v1" in body, (
        "what she attacked is not named, in full: a reference without the "
        "model does not say which artifact she attacked"
    )
    assert "warmth-adversarial@v1" in body, "her eval suite is not shown"


def test_a_support_reporter_page_names_what_they_used():
    body = text_of(page("gus"))
    assert "Applied use" in body
    assert "@v1" in body, "the pinned version they used is not named"


def test_the_owners_index_lists_them():
    index = (DIST / "owners" / "index.html")
    if not index.exists():
        pytest.skip("site not built; run `make site`")
    body = text_of(index.read_text())
    for owner in EVIDENCE_ONLY:
        assert owner in body, f"{owner} took part and is missing from /owners/"
    assert "none claimed" in body, (
        "an owner with no labels must read as absence rather than as an empty cell"
    )


def test_an_attack_count_is_not_presented_as_the_attackers_score():
    """Attacking a lot is not an achievement the page ranks anyone by.

    Two earlier versions of this were wrong in opposite ways. The first asserted a
    disclaimer sentence was present, which is the weak shape: a page can carry the
    sentence and rank anyway, and the test broke when the sentence was cut for
    being the site arguing with its reader rather than when the page changed.

    The second scanned the prose for words like "score" and failed on the synthetic
    banner, which says "Scores are repeated-digit decimals". Scanning prose for
    single words finds the word, not the meaning.

    So this checks the only thing that would actually rank an attacker: a column
    holding a tally. Each attack is listed as its own event, against what, by what
    method, and when. There is no number aggregating them.
    """
    raw = page("carol")
    headers = [
        re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", h)).strip().lower()
        for h in re.findall(r"<th[^>]*>(.*?)</th>", raw, re.S)
    ]
    assert headers, "no table on the page, so this proves nothing"
    for h in headers:
        assert not any(w in h for w in ("count", "score", "rank", "total")), (
            f"a column headed {h!r} would read as a tally of the attacker rather "
            "than as one more thing they did"
        )


def test_the_ordering_bar_is_absent_where_there_is_nothing_to_order():
    """carol has no submissions, so the one orderable list on an owner page is
    empty. A bar over an empty table is the dead control returning."""
    raw = page("carol")
    assert 'class="ordering"' not in raw, (
        "an ordering control renders on a page whose only orderable list is empty"
    )
