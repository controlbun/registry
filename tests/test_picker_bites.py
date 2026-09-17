"""Proof that the picker tests would catch the ways a type-ahead goes wrong.

Same argument as `test_ordering_bites.py`, for the same reason. The ordering
control shipped broken under a green suite, because the test covering it asserted
that an attribute appeared in the markup, which it did. A test written after a
bug is worth exactly what its ability to fail on that bug is worth.

The failures reintroduced below are not invented. Four of them are the standard
ways this control breaks: the popup that closes before a click resolves, the
field that quietly replaces what somebody typed, the answer that keeps describing
the previous word, and `aria-activedescendant` naming an element that does not
exist. Two more are this project's own: the open field closing over time, and the
corpus losing its place at the top of the list.

Each case takes the real built page, makes one change, and asserts the matching
check goes red. The unmodified page is driven first, so a green run here is not
vacuous.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

import combobox_harness as cb  # noqa: E402

PAGE = ROOT / "astro" / "dist" / "index.html"
FIELD, LIST = "pick-label", "labels-listbox"
MINE = "a concept nobody has named"


@pytest.fixture(scope="module")
def clean() -> str:
    if not PAGE.exists():
        pytest.skip("site not built; run `make site`")
    html = PAGE.read_text()
    got = cb.run(html, [cb.click(FIELD)])["fields"][FIELD]
    assert got["role"] == "combobox" and got["expanded"] == "true", (
        "the unmodified page is already broken, so nothing below proves anything"
    )
    return html


def mutate(html: str, old: str, new: str) -> str:
    """One change, and only where it was meant to go."""
    assert html.count(old) == 1, (
        f"the anchor for this bite is not unique ({html.count(old)} hits): {old[:60]!r}"
    )
    return html.replace(old, new)


def test_a_picker_that_never_runs_is_caught(clean):
    """The original bug in this control's shape: markup, no behaviour.

    A reader sees a field with a word in it, which is what a working field also
    looks like, so nothing short of driving it tells the two apart.
    """
    broken = clean.replace(cb.picker_script(clean), "// nothing at all\n")
    with pytest.raises(AssertionError, match="exactly one picker script"):
        cb.run(broken, [cb.click(FIELD)])


def test_a_field_that_quietly_corrects_what_was_typed_is_caught(clean):
    """The failure the whole control exists to avoid.

    Snapping to the nearest suggestion on the way out is a helpful-looking
    behaviour that turns an open string into a closed one: whatever the reader
    meant is replaced by the nearest thing on a list somebody else wrote.
    """
    broken = mutate(
        clean,
        """} else if (key === "Tab") {
              // Leaves with what is typed. Committing the highlighted row here
              // is the behaviour that quietly overwrites somebody's own word.
              hide();
            }""",
        """} else if (key === "Tab") {
              if (open && choices.length) take(choices[0]);
              hide();
            }""",
    )
    # A partial word rather than MINE, because a word matching nothing offers
    # only itself and snapping to the first row would be a no-op.
    got = cb.run(broken, [cb.typing(FIELD, "refus"), cb.press(FIELD, "Tab")])
    assert got["fields"][FIELD]["value"] != "refus", "this bite no longer bites"


def test_an_empty_popup_over_an_unrecognised_word_is_caught(clean):
    """Nothing in the list and nothing offered reads as a refusal.

    The row that hands the typed text back is what makes the openness visible at
    the moment it matters, rather than a claim in prose somewhere else.
    """
    broken = mutate(
        clean, 'rows.push(row(typed, 0, 0, "as typed", "literal"));', "",
    )
    got = cb.run(broken, [cb.typing(FIELD, MINE)])["fields"][FIELD]
    assert got["listbox"]["options"] == [], "this bite no longer bites"


def test_the_corpus_losing_the_top_of_the_list_is_caught(clean):
    """One clause dropped from the comparator, which is how this would go.

    Nobody decides to demote what the registry holds. Somebody tidies a sort
    function and the rule leaves with it.
    """
    broken = mutate(
        clean,
        "out.sort((a, b) => a.held - b.held || a.tier - b.tier || a.n - b.n);",
        "out.sort((a, b) => a.tier - b.tier || a.n - b.n);",
    )
    # `hum` is the query that makes the rule load-bearing: `pro-human` matches
    # it after a hyphen and `humility` matches it as a prefix, so the corpus
    # entry is only at the top because the corpus is at the top.
    got = cb.run(broken, [cb.typing(FIELD, "hum")])["fields"][FIELD]
    words = [o["value"].lower() for o in got["listbox"]["options"] if o["cls"] != "literal"]
    held = {"kindness", "pro-human", "refusal"}
    flags = [w in held for w in words]
    assert flags != sorted(flags, reverse=True), "this bite no longer bites"


def test_a_popup_that_closes_before_the_click_lands_is_caught(clean):
    """Blur fires between mousedown and click.

    The classic one. Fine on a keyboard, dead on a mouse, and invisible to any
    test that only presses keys.
    """
    broken = mutate(
        clean, 'li.addEventListener("mousedown", (e) => e.preventDefault());', "",
    )
    got = cb.run(broken, [cb.click(FIELD), cb.choose(LIST, 2)])
    assert not got["trace"][-1]["prevented"], "this bite no longer bites"


def test_an_answer_left_describing_the_previous_word_is_caught(clean):
    """Assigning `.value` from script raises no input event.

    The same failure as the ordering caption that was rendered once on the
    server and never updated: the page stating something it knows is false.
    """
    broken = mutate(
        clean,
        """            hide();
            // Assigning .value from script raises no input event, so without
            // this the paragraph below would keep describing the previous word.
            render();""",
        "            hide();",
    )
    absent = [w for w in cb.suggestions(clean, "labels")
              if w not in {"kindness", "pro-human", "refusal"}]
    at = cb.suggestions(clean, "labels").index(absent[0])
    got = cb.run(broken, [cb.click(FIELD), cb.choose(LIST, at)])
    assert got["fields"][FIELD]["value"] == absent[0]
    assert "Neither of those is a list you pick from" not in got["answer"], (
        "this bite no longer bites"
    )


def test_an_activedescendant_naming_nothing_is_caught(clean):
    """A screen reader is told where the focus is and finds no such element."""
    broken = mutate(
        clean,
        'input.setAttribute("aria-activedescendant", rows[n].id);',
        'input.setAttribute("aria-activedescendant", "no-such-row");',
    )
    got = cb.run(broken, [cb.typing(FIELD, "e"), cb.press(FIELD, "ArrowDown")])
    assert got["fields"][FIELD]["active"] not in got["ids"], "this bite no longer bites"


def test_two_popups_opening_at_once_is_caught(clean):
    """Leaving `list` on the input draws the browser's own list underneath.

    Which is the appearance this control was built to replace, arriving back
    through the layer that was meant to be the fallback.
    """
    broken = mutate(clean, 'input.removeAttribute("list");', "")
    got = cb.run(broken, [cb.click(FIELD)])["fields"][FIELD]
    assert got["list"] is not None, "this bite no longer bites"


def test_a_prefix_match_buried_under_the_middle_of_other_words_is_caught(clean):
    """Where a type-ahead stops being worth using.

    Type the first four letters of a word and find it below three words that
    merely contain those letters somewhere.
    """
    broken = mutate(clean, ": at === 0 ? 1", ": at === 0 ? 3")
    got = cb.run(broken, [cb.typing(FIELD, "form")])["fields"][FIELD]
    words = [o["value"].lower() for o in got["listbox"]["options"] if o["cls"] != "literal"]
    prefixed = [w for w in words if w.startswith("form")]
    assert words.index(prefixed[-1]) > 0, "this bite no longer bites"


def test_a_constraint_smuggled_onto_the_shipped_input_is_caught(clean):
    """The case the old markup check could not see.

    It asserted that `<input id="pick-kind"` appeared in the page. A text input
    carrying `pattern` satisfies that string and rejects most of the schema, so
    the element is parsed and asked what it permits instead.
    """
    broken = mutate(
        clean, '<input id="pick-label" list="labels"',
        '<input id="pick-label" pattern="[a-z-]+" list="labels"',
    )
    attrs = cb.parse(broken).nodes[FIELD]["attrs"]
    assert "pattern" in attrs, "this bite no longer bites"


def test_a_field_turned_back_into_a_dropdown_is_caught(clean):
    """The shape this replaced, and the one it will drift back towards.

    A `<select>` of a hundred concepts is a taxonomy, and publishing one
    declares which concepts are legitimate.
    """
    broken = clean.replace('<input id="pick-label"', '<select id="pick-label"')
    assert cb.parse(broken).nodes[FIELD]["tag"] == "select", "this bite no longer bites"
