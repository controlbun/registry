"""The home page's situation picker: open where the schema is open, and wired.

A researcher read the old opening aloud in a meeting and finished with "I didn't
understand the task". The prose was abstract and she answered it as one: "ten
people will extract kindness" got back "Who are the 10 people? Like any
researcher? Why 10". The picker replaces the abstraction with a sentence she
completes using her own artifact and her own reason.

Two properties are worth a test and neither is cosmetic.

**It must stay open where the schema is open.** `kind` is deliberately an open
string, and a dropdown listing the three kinds this corpus happens to hold
declares that those are the three. That is the closed-enum trip-wire at field
level, arriving through a control rather than through a `CHECK` constraint.

**It must actually be wired.** The ordering control shipped for days rendering
buttons with no handler bound, which looked finished. A select the script never
finds is the same failure.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "astro" / "dist"
EXPORT = ROOT / "astro" / "src" / "data" / "registry.json"


def home() -> str:
    path = DIST / "index.html"
    if not path.exists():
        pytest.skip("site not built; run `make site`")
    return path.read_text()


def visible(html: str) -> str:
    for tag in ("script", "style"):
        html = re.sub(rf"<{tag}.*?</{tag}>", "", html, flags=re.S)
    return re.sub(r"<[^>]+>", " ", html)


def test_it_offers_every_kind_and_label_the_corpus_holds():
    """Derived from the corpus, not declared.

    `DECISIONS.md` 2026-09-13 settles that faceted browsing over kinds is built
    from what the corpus actually contains. A hand-written list drifts from the
    data the first time somebody publishes a kind nobody thought of, which is
    the case the open string exists for.
    """
    payload = json.loads(EXPORT.read_text())
    html = home()

    for kind in payload["kinds"]:
        assert f'value="{kind}"' in html, f"{kind!r} is in the corpus and not offered"
    for label in {entry["label"] for entry in payload["labels"]}:
        assert f'value="{label}"' in html, f"{label!r} is claimed and not offered"

    # Corpus first, so what actually exists sorts to the top of autocomplete.
    labels = re.search(r'<datalist id="labels">(.*?)</datalist>', html, re.S)
    first = re.findall(r'value="([^"]+)"', labels.group(1))[: len(payload["labels"])]
    assert set(first) == {entry["label"] for entry in payload["labels"]}, (
        "suggestions from elsewhere outrank the labels this registry holds"
    )


def test_both_open_fields_accept_anything():
    """They are text inputs with suggestions, not dropdowns with an escape.

    `kind` and the label are open strings in the schema. A `<select>` listing a
    hundred concepts grouped into categories is a taxonomy, and publishing one
    declares which concepts are legitimate: `CLAUDE.md`'s closed-enum failure
    arriving through a control rather than a `CHECK`. The instruction there is
    document common values and enforce none, which is what a datalist behind a
    free-text field is.

    An earlier version used `<select>` with a "something else" option. That was
    an escape hatch bolted onto a closed control; this removes the need for one.
    """
    html = home()
    for field in ("pick-kind", "pick-label"):
        assert f'<input id="{field}"' in html, f"{field} is not a text input"
        assert f'<select id="{field}"' not in html, (
            f"{field} is a dropdown, which makes its options the permitted set"
        )
        assert f'list="' in html, f"{field} offers no suggestions at all"


def test_the_suggestions_go_well_past_what_the_corpus_holds():
    """Otherwise a visitor concludes their concept does not belong here.

    Three labels is what this corpus contains and is not what the schema takes.
    A reader whose artifact is about sandbagging or evaluation-awareness should
    see it recognised, which is the whole reason the picker exists.
    """
    payload = json.loads(EXPORT.read_text())
    html = home()
    suggestions = re.search(r'<datalist id="labels">(.*?)</datalist>', html, re.S)
    assert suggestions, "no label suggestions"
    values = re.findall(r'value="([^"]+)"', suggestions.group(1))

    held = {entry["label"] for entry in payload["labels"]}
    assert held <= set(values), "the corpus's own labels are not suggested"
    assert len(values) > 5 * len(held), (
        f"only {len(values)} suggestions against {len(held)} labels held; a "
        "visitor whose concept is absent will read that as not belonging"
    )


def test_it_answers_before_any_script_runs():
    """A reader with JavaScript off gets the strongest true answer, not a blank.

    Rendered server-side with the default already chosen. The blind crawl that
    found half the defects on this site read it over curl with no JavaScript,
    which is a fair model of some readers and of every crawler.
    """
    body = visible(home())
    assert "cannot tell whether to trust it" in body
    assert "Nothing is scored and nothing is ranked" in body, (
        "the default answer is not in the HTML, so the box is empty until a "
        "script runs"
    )


def test_the_script_and_the_markup_have_not_drifted():
    """Every id the script reaches for exists. The ordering-control failure."""
    html = home()
    wanted = set(re.findall(r'getElementById\("([^"]+)"\)', html))
    assert wanted, "nothing reaches for the picker, so it renders and does nothing"
    for element_id in sorted(wanted):
        assert f'id="{element_id}"' in html, (
            f"the script queries #{element_id} and no element carries that id"
        )


def test_no_option_asks_the_registry_to_designate():
    """Better is fine. Best is not, and the difference is the whole project.

    **Better is a consumer's judgment, made for one purpose.** Somebody compares
    two claimants and picks one for their own work; that is pinning, it is
    ordinary experimental control, and informing it is what this registry is
    for. The founding sentence on /about/ is "if I could reuse someone else's
    better pro-human direction without the effort".

    **Best is the registry's judgment, made for everyone.** A total ordering, one
    answer, nobody's purpose in particular. That is designation and it is the
    thing refused.

    So this bans the superlative and the words that ask us to choose, and lets
    the comparative through. The first version of this test banned the substring
    "better" and would have forbidden the sentence the project started over,
    which is what applying a word list instead of the designate-or-pin test in
    CLAUDE.md gets you.
    """
    options = re.findall(r"<option value=\"([^\"]+)\"", home())
    assert options, "no options rendered"

    # Superlatives, and phrasings that hand the choice to the registry.
    designating = (
        "best", "top ", "top-", "highest", "leading", "recommended",
        "official", "approved", "verified", "which one should",
    )
    for option in options:
        low = option.lower()
        for word in designating:
            assert word not in low, (
                f"option {option!r} asks the registry to designate. A reader "
                "comparing two claimants for their own purpose is the product; "
                "being told which is the right one is not."
            )
