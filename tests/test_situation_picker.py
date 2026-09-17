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


def test_both_open_fields_have_a_way_out_of_the_list():
    """Without an escape the control is a closed enum on an open field."""
    assert home().count('value="something else"') >= 2, (
        "kind and label are both open strings and each needs its own escape; "
        "a picker with no way out declares that the list is the permitted set"
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


def test_no_option_asks_the_registry_to_pick():
    """The reason 'make a better one' is not on the menu.

    Every option has to be answerable without the registry ranking anything. A
    reader who wants to be told which artifact is good is the reader this
    project is built to disappoint, and offering them that as a choice would
    promise it.
    """
    options = re.findall(r"<option value=\"([^\"]+)\"", home())
    banned = ("better", "best", "top", "recommend", "which one")
    for option in options:
        low = option.lower()
        for word in banned:
            assert word not in low, (
                f"option {option!r} promises a judgment the registry does not make"
            )
