"""The home page's situation picker: open where the schema is open, and wired.

A researcher read the old opening aloud in a meeting and finished with "I didn't
understand the task". The prose was abstract and she answered it as one: "ten
people will extract kindness" got back "Who are the 10 people? Like any
researcher? Why 10". The picker replaces the abstraction with a sentence she
completes using her own artifact and her own reason.

Two properties are worth a test and neither is cosmetic.

**It must stay open where the schema is open.** `kind` is deliberately an open
string, and a control listing the three kinds this corpus happens to hold
declares that those are the three. That is the closed-enum trip-wire at field
level, arriving through a control rather than through a `CHECK` constraint.

**It must actually be wired.** The ordering control shipped for days rendering
buttons with no handler bound, which looked finished. A type-ahead is a worse
case of the same thing: it has no resting appearance to be wrong, so a field
whose popup never opens looks exactly like a field nobody has clicked.

The control is two layers and the tests below are in two halves to match.
`<input list>` over a `<datalist>` is what ships and is the whole control when
no script runs; a script reads that datalist, drops the `list` attribute and
draws a listbox in its place. The first half reads the HTML, because that is
what the no-script reader gets. The second half runs the real script in Node
through `combobox_harness`, because nothing else can tell you whether the thing
a reader actually operates does what the markup implies.

Several assertions here used to name the markup instead of the property: that
`<input id="pick-kind"` appeared in the page, that a `<datalist>` existed, that
`list="` was somewhere in the file. All three were true of the old control and
are true of this one, and none of them was the thing worth protecting. They are
now stated as the properties they were standing in for, checked against a parse
on the no-script side and against the running control on the other.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "astro" / "dist"
EXPORT = ROOT / "astro" / "src" / "data" / "registry.json"

sys.path.insert(0, str(Path(__file__).resolve().parent))

import combobox_harness as cb  # noqa: E402

KIND_FIELD, LABEL_FIELD = "pick-kind", "pick-label"
KIND_LIST, LABEL_LIST = "kinds", "labels"


def home() -> str:
    path = DIST / "index.html"
    if not path.exists():
        pytest.skip("site not built; run `make site`")
    return path.read_text()


def corpus() -> dict:
    payload = json.loads(EXPORT.read_text())
    return {
        "kinds": list(payload["kinds"]),
        "labels": sorted({entry["label"] for entry in payload["labels"]}),
    }


def visible(html: str) -> str:
    for tag in ("script", "style"):
        html = re.sub(rf"<{tag}.*?</{tag}>", "", html, flags=re.S)
    return re.sub(r"<[^>]+>", " ", html)


def offered(field: dict) -> list[str]:
    """The suggestions a popup is showing, without the reader's own text.

    The last row is whatever is in the field, which is not a suggestion and must
    not be counted as one when the ordering rule is under test.
    """
    return [o["value"] for o in field["listbox"]["options"] if o["cls"] != "literal"]


def own_text_row(field: dict) -> dict | None:
    rows = [o for o in field["listbox"]["options"] if o["cls"] == "literal"]
    return rows[0] if rows else None


# --------------------------------------------------------------------------- #
# What ships in the HTML, which is the whole control when no script runs.


def test_it_offers_every_kind_and_label_the_corpus_holds():
    """Derived from the corpus, not declared.

    `DECISIONS.md` 2026-09-13 settles that faceted browsing over kinds is built
    from what the corpus actually contains. A hand-written list drifts from the
    data the first time somebody publishes a kind nobody thought of, which is
    the case the open string exists for.
    """
    held = corpus()
    html = home()

    for kind in held["kinds"]:
        assert kind in cb.suggestions(html, KIND_LIST), (
            f"{kind!r} is in the corpus and is not offered for kind"
        )
    for label in held["labels"]:
        assert label in cb.suggestions(html, LABEL_LIST), (
            f"{label!r} is claimed and is not offered for the label"
        )


def test_what_the_corpus_holds_is_offered_first():
    """The one ordering rule the picker has, and it is about provenance.

    Not quality and not a ranking: the entries at the top are the ones a reader
    can go and read on this site. Checked here on the list the page ships and
    again below on the list the script draws, because those are two different
    orderings that have to agree.
    """
    held = corpus()
    for list_id, words in (
        (KIND_LIST, held["kinds"]),
        (LABEL_LIST, held["labels"]),
    ):
        shipped = cb.suggestions(home(), list_id)
        assert set(shipped[: len(words)]) == set(words), (
            f"in #{list_id}, suggestions from elsewhere outrank what this "
            "registry holds"
        )


def test_the_suggestions_go_well_past_what_the_corpus_holds():
    """Otherwise a visitor concludes their concept does not belong here.

    Three labels is what this corpus contains and is not what the schema takes.
    A reader whose artifact is about sandbagging or evaluation-awareness should
    see it recognised, which is the whole reason the picker exists.
    """
    held = set(corpus()["labels"])
    words = cb.suggestions(home(), LABEL_LIST)

    assert held <= set(words), "the corpus's own labels are not suggested"
    assert len(words) > 5 * len(held), (
        f"only {len(words)} suggestions against {len(held)} labels held; a "
        "visitor whose concept is absent will read that as not belonging"
    )


def test_nothing_in_the_shipped_markup_constrains_what_can_be_typed():
    """The no-script half of "it takes anything".

    This used to assert that the string `<input id="pick-kind"` appeared in the
    page and that `<select id="pick-kind"` did not, which is a spelling and not
    a property: a text input with `pattern` or `readonly` would have passed it
    while rejecting most of the schema. So the element is parsed and asked what
    it actually permits.

    A `<select>` of a hundred concepts grouped into nine categories is a
    taxonomy, and publishing one declares which concepts are legitimate:
    `CLAUDE.md`'s closed-enum failure arriving through a control rather than
    through a `CHECK`. The instruction there is document common values and
    enforce none, which is what a datalist behind a free-text field is. An even
    earlier version used `<select>` with a "something else" option, an escape
    hatch bolted onto a closed control; this removes the need for one.
    """
    page = cb.parse(home())
    for field in (KIND_FIELD, LABEL_FIELD):
        node = page.nodes.get(field)
        assert node is not None, f"#{field} is not in the page at all"
        assert node["tag"] == "input", (
            f"#{field} is a <{node['tag']}>, and anything other than a text "
            "input makes its options the permitted set"
        )
        attrs = node["attrs"]
        assert attrs.get("type", "text") == "text", (
            f"#{field} is type={attrs['type']!r}, which constrains what it takes"
        )
        for constraint in ("pattern", "readonly", "disabled", "maxlength"):
            assert constraint not in attrs, (
                f"#{field} carries {constraint}, which narrows an open string"
            )
        # Advisory by spec: a datalist suggests and never rejects. Its presence
        # is what a reader with no script gets instead of the popup below.
        assert attrs.get("list"), f"#{field} offers no suggestions without a script"


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

    # The two comboboxes take their ids as arguments, so the regex above cannot
    # see them and a typo would go unnoticed until a reader clicked. The harness
    # refuses to run when one is absent, which covers the rest.
    page = cb.parse(html)
    missing = [i for i in cb.WATCHED if i not in page.nodes]
    assert not missing, f"the script is handed ids nothing in the page carries: {missing}"


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


# --------------------------------------------------------------------------- #
# What the script makes of it, run rather than read.


@pytest.fixture(scope="module")
def html() -> str:
    return home()


@pytest.fixture(params=[KIND_FIELD, LABEL_FIELD])
def field(request) -> str:
    """Both open fields, because they are two calls and only one gets read."""
    return request.param


def test_enhancement_binds_a_real_combobox(html, field):
    """The dead-control test, in the form this control can fail it.

    A button with no handler at least looks like a button. A field whose script
    never ran looks like a field nobody has clicked, so nothing short of driving
    it distinguishes the two.
    """
    got = cb.run(html, [cb.click(field)])["fields"][field]

    assert got["role"] == "combobox"
    assert got["listbox"] is not None, "nothing built a list for the field to control"
    assert got["listbox"]["role"] == "listbox"
    assert got["expanded"] == "true", "clicking the field does not open anything"
    assert got["listbox"]["hidden"] is False
    assert got["listbox"]["options"], "the popup opened with nothing in it"
    for option in got["listbox"]["options"]:
        assert option["role"] == "option", (
            "rows without a role are divs in a trench coat; a screen reader is "
            "told there is a list and then handed nothing it can walk"
        )


def test_the_native_popup_is_taken_away_so_two_do_not_open(html, field):
    """`list` stays in the markup and comes off at runtime.

    Both halves matter. Shipping it is what a reader with no script gets; taking
    it off is what stops the browser drawing its own unstyled popup underneath
    this one, which is the exact appearance this replaced.
    """
    assert cb.parse(html).nodes[field]["attrs"].get("list"), (
        "the no-script layer is gone: nothing suggests anything without JS"
    )
    got = cb.run(html, [cb.click(field)])["fields"][field]
    assert got["list"] is None, (
        "the native datalist popup is still attached, so two lists open at once"
    )


def test_the_running_field_takes_anything_typed(html, field):
    """The property the whole control exists to keep.

    `kind` and the label are open strings in the schema. Typing a word that is
    in no list has to survive every way of leaving the field, and the popup has
    to offer it back rather than showing an empty box, which a reader reads as
    a refusal.
    """
    mine = "a concept nobody has named"
    for after in ([], [cb.press(field, "Enter")], [cb.press(field, "Tab")],
                  [cb.press(field, "Escape")], [cb.blur(field)]):
        got = cb.run(html, [cb.typing(field, mine)] + after)["fields"][field]
        assert got["value"] == mine, (
            f"after {[s['do'] for s in after]} the field no longer holds what "
            "was typed into it"
        )

    got = cb.run(html, [cb.typing(field, mine)])["fields"][field]
    row = own_text_row(got)
    assert row is not None, (
        "a word in no list produced an empty popup, which reads as a refusal"
    )
    assert row["value"] == mine
    assert row["note"] == "as typed"


def test_taking_the_reader_s_own_text_changes_nothing_about_it(html, field):
    """The last row is the input's value handed straight back.

    A row that normalised, trimmed to a slug or lower-cased would be a quiet
    little validator, which is the closed enum again with better manners.
    """
    mine = "Mixed Case With Spaces"
    steps = [cb.typing(field, mine), cb.press(field, "ArrowUp"), cb.press(field, "Enter")]
    got = cb.run(html, steps)["fields"][field]
    assert got["value"] == mine


def test_what_the_corpus_holds_sorts_first_in_the_popup(html):
    """Same rule as the shipped list, now on the list a reader actually sees.

    Checked on a query that matches both sides, because an empty query would
    pass on the emitted order alone and prove nothing about the ranking.
    """
    held = [w.lower() for w in corpus()["labels"]]
    query = _query_matching_both(held, cb.suggestions(home(), LABEL_LIST))

    got = cb.run(html, [cb.typing(LABEL_FIELD, query)])["fields"][LABEL_FIELD]
    flags = [w.lower() in held for w in offered(got)]
    assert any(flags) and not all(flags), (
        f"{query!r} was supposed to match both sides and did not"
    )
    assert flags == sorted(flags, reverse=True), (
        f"filtering on {query!r} put a suggestion above something this registry "
        f"holds: {offered(got)}"
    )


@pytest.mark.parametrize("query", ["form", "aware", "self", "co", "e"])
def test_the_ranking_is_the_one_the_page_describes(html, query):
    """Corpus first, then exact, then prefix, then a hyphen boundary, anywhere.

    Stated as a monotonicity check over the whole result rather than as a
    handful of expected orderings, so it holds for any query and cannot be
    satisfied by a sort that happens to agree on the examples.
    """
    held = {w.lower() for w in corpus()["labels"]}
    got = cb.run(html, [cb.typing(LABEL_FIELD, query)])["fields"][LABEL_FIELD]
    words = offered(got)
    assert words, f"{query!r} matched nothing, so this asserts nothing"

    keys = [(0 if w.lower() in held else 1, _tier(w.lower(), query)) for w in words]
    assert keys == sorted(keys), (
        f"the popup's order for {query!r} is not the one described:\n"
        + "\n".join(f"  {k}  {w}" for k, w in zip(keys, words))
    )


def test_an_exact_prefix_beats_a_match_in_the_middle(html):
    """The one ranking claim spelled out, because it is the one a reader feels.

    Typing the start of a word and finding it below three words that merely
    contain those letters is the moment a type-ahead stops being worth using.
    """
    got = cb.run(html, [cb.typing(LABEL_FIELD, "form")])["fields"][LABEL_FIELD]
    words = [w.lower() for w in offered(got)]
    prefixed = [w for w in words if w.startswith("form")]
    middled = [w for w in words if not w.startswith("form")]
    assert prefixed and middled, "the fixture no longer exercises this"
    assert words.index(prefixed[-1]) < words.index(middled[0])


def test_filtering_narrows_to_what_was_typed(html, field):
    every = len(cb.run(html, [cb.click(field)])["fields"][field]["listbox"]["options"])
    some = offered(cb.run(html, [cb.typing(field, "e")])["fields"][field])
    assert 0 < len(some) < every, "typing does not narrow the list"
    assert all("e" in w.lower() for w in some)


def test_opening_a_filled_field_shows_the_whole_list(html, field):
    """And stands on the row the field is already holding.

    Filtering by the value that is already there answers a click with one row,
    its own, which looks like a control that found nothing.
    """
    got = cb.run(html, [cb.click(field)])["fields"][field]
    assert len(got["listbox"]["options"]) == len(
        cb.suggestions(home(), KIND_LIST if field == KIND_FIELD else LABEL_LIST)
    ), "opening a filled field filtered by its own contents"

    standing = [o for o in got["listbox"]["options"] if o["selected"] == "true"]
    assert len(standing) == 1
    assert standing[0]["value"] == got["value"]
    assert got["active"] == standing[0]["id"]


def test_the_keyboard_walks_the_list_and_enter_takes_a_row(html, field):
    """Down, down, Enter. The path somebody who never touches a mouse uses."""
    steps = [cb.typing(field, "e"), cb.press(field, "ArrowDown"),
             cb.press(field, "ArrowDown")]
    got = cb.run(html, steps)["fields"][field]
    walked = offered(got)
    assert got["active"] == got["listbox"]["options"][1]["id"], (
        "two presses of Down did not land on the second row"
    )
    assert [o["selected"] for o in got["listbox"]["options"][:3]] == \
        ["false", "true", "false"], "more than one row is marked as the one in hand"

    took = cb.run(html, steps + [cb.press(field, "Enter")])["fields"][field]
    assert took["value"] == walked[1], "Enter did not take the highlighted row"
    assert took["expanded"] == "false", "the popup stayed open after Enter"
    assert took["active"] is None


def test_arrow_up_from_nothing_lands_on_the_last_row(html, field):
    got = cb.run(html, [cb.typing(field, "e"), cb.press(field, "ArrowUp")])["fields"][field]
    rows = got["listbox"]["options"]
    assert got["active"] == rows[-1]["id"]


def test_the_walk_wraps_at_both_ends(html, field):
    rows = cb.run(html, [cb.typing(field, "e")])["fields"][field]["listbox"]["options"]
    n = len(rows)
    downs = [cb.press(field, "ArrowDown")] * (n + 1)
    got = cb.run(html, [cb.typing(field, "e")] + downs)["fields"][field]
    assert got["active"] == rows[0]["id"], "walking off the bottom did not wrap"


def test_escape_dismisses_and_keeps_what_was_typed(html, field):
    steps = [cb.typing(field, "refu"), cb.press(field, "ArrowDown"),
             cb.press(field, "Escape")]
    got = cb.run(html, steps)["fields"][field]
    assert got["expanded"] == "false"
    assert got["active"] is None
    assert got["value"] == "refu", (
        "Escape overwrote the field. Dismissing a popup is not a decision about "
        "its contents, and clearing here is hostile to a field whose point is "
        "that it takes anything"
    )


def test_tab_leaves_without_overwriting_what_was_typed(html, field):
    """The behaviour that quietly replaces somebody's own word with a guess."""
    steps = [cb.typing(field, "refu"), cb.press(field, "ArrowDown"),
             cb.press(field, "Tab")]
    got = cb.run(html, steps)["fields"][field]
    assert got["value"] == "refu"
    assert got["expanded"] == "false"


def test_the_pointer_takes_a_row_without_blurring_the_field_first(html, field):
    """mousedown has to be cancelled or the popup closes before the click.

    This is the classic way a type-ahead ends up looking broken on a mouse and
    fine on a keyboard: blur fires between mousedown and click, the list is
    gone by the time the click resolves, and nothing is ever selected.
    """
    list_id = ("kinds" if field == KIND_FIELD else "labels") + "-listbox"
    result = cb.run(html, [cb.click(field), cb.choose(list_id, 2)])
    got = result["fields"][field]
    assert result["trace"][-1]["prevented"], (
        "mousedown on a row is not cancelled, so the field blurs and the popup "
        "closes before the click lands"
    )
    wanted = cb.suggestions(home(), "kinds" if field == KIND_FIELD else "labels")[2]
    assert got["value"] == wanted
    assert got["expanded"] == "false"


def test_the_answer_follows_a_suggestion_taken_by_pointer(html):
    """Assigning `.value` from script raises no input event.

    So the paragraph under the sentence keeps describing the previous word
    unless the script says so itself, which is a page stating something it knows
    to be false and is the same failure as the ordering caption that never
    updated.
    """
    absent = [w for w in cb.suggestions(home(), LABEL_LIST)
              if w not in corpus()["labels"]]
    at = cb.suggestions(home(), LABEL_LIST).index(absent[0])
    result = cb.run(html, [cb.click(LABEL_FIELD), cb.choose("labels-listbox", at)])
    assert result["fields"][LABEL_FIELD]["value"] == absent[0]
    assert "Neither of those is a list you pick from" in result["answer"], (
        "a word the corpus does not hold was taken from the popup and the "
        "answer still reads as though it does"
    )


def test_the_aria_wiring_points_at_things_that_exist(html, field):
    """`aria-activedescendant` naming nothing is worse than naming nothing.

    A screen reader is told the focus is on an option and then finds no such
    element, so it reads the field as empty while the page looks highlighted.
    """
    got_all = cb.run(html, [cb.typing(field, "e"), cb.press(field, "ArrowDown")])
    got = got_all["fields"][field]
    assert got["autocomplete"] == "list"
    assert got["controls"] == got["listbox"]["id"]
    assert got["listbox"]["label"], "the listbox has no name to announce"
    assert got["active"] in got_all["ids"], (
        f"aria-activedescendant is {got['active']!r} and no element carries it"
    )
    assert got["active"] == got["listbox"]["options"][0]["id"]

    closed = cb.run(html, [cb.typing(field, "e"), cb.press(field, "ArrowDown"),
                           cb.press(field, "Escape")])["fields"][field]
    assert closed["active"] is None, (
        "the field still points at an option in a list that is closed"
    )


def test_the_number_of_matches_is_said_out_loud(html, field):
    """A list appearing under a field is a visual event and nothing else."""
    got = cb.run(html, [cb.typing(field, "e")])
    assert re.fullmatch(r"\d+ suggestions?", got["status"]), got["status"]

    none = cb.run(html, [cb.typing(field, "qqqq not a word")])
    assert "taken as it is" in none["status"], (
        "no match announced as silence, which sounds like a rejection"
    )

    shut = cb.run(html, [cb.typing(field, "e"), cb.press(field, "Escape")])
    assert shut["status"] == "", "the live region still describes a closed popup"


def test_the_popup_stays_inside_the_viewport(html, field):
    """The sentence wraps, so a field can sit hard against the right edge."""
    over = cb.run(html, [cb.click(field)], viewport=420, popup_right=600)
    assert "flip" in over["fields"][field]["listbox"]["cls"], (
        "a popup running past the right edge is left hanging off it"
    )
    fits = cb.run(html, [cb.click(field)], viewport=1280, popup_right=500)
    assert "flip" not in fits["fields"][field]["listbox"]["cls"], (
        "the popup flips when it did not need to, so it opens away from its field"
    )


def test_the_field_grows_with_what_is_in_it(html, field):
    """`size` is the fallback where `field-sizing: content` is not supported.

    It is also the width the page ships with, so the sentence is the right shape
    before the script runs and does not jump when it does.
    """
    short = cb.run(html, [cb.typing(field, "ab")])["fields"][field]
    long = cb.run(html, [cb.typing(field, "a" * 40)])["fields"][field]
    assert short["size"] < long["size"]
    assert long["size"] <= 28, "one long paste breaks the line the sentence sits on"


# --------------------------------------------------------------------------- #
# helpers


def _tier(word: str, query: str) -> int:
    """Where a match sits in the ranking, mirroring the page's own function."""
    query = query.strip().lower()
    if not query:
        return 1
    at = word.find(query)
    if word == query:
        return 0
    if at == 0:
        return 1
    return 2 if word[at - 1] == "-" else 3


def _query_matching_both(held: list[str], words: list[str]) -> str:
    """A query on which corpus-first is the only reason the corpus is first.

    Derived rather than written down, so the test keeps testing the rule when
    the corpus changes underneath it, and derived with a condition: some word
    from elsewhere has to match *better* than anything the corpus holds. Pick a
    query where the corpus entry already wins on prefix and the test passes
    whether or not the rule exists.
    """
    elsewhere = [w.lower() for w in words if w.lower() not in held]
    mine = [w.lower() for w in words if w.lower() in held]
    best = ""
    for word in held:
        for size in range(len(word), 1, -1):
            for start in range(len(word) - size + 1):
                part = word[start:start + size]
                ours = [_tier(w, part) for w in mine if part in w]
                theirs = [_tier(w, part) for w in elsewhere if part in w]
                if ours and theirs and min(theirs) < min(ours) and len(part) > len(best):
                    best = part
    if not best:
        raise AssertionError(
            "no query makes the corpus-first rule load-bearing, so this test "
            "would pass with the rule deleted"
        )
    return best
