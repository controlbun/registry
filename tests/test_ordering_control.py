"""The ordering control has to actually reorder, and to agree with order.py.

Two failures these exist to catch, both of which were live:

**The control did nothing.** Buttons rendered, `aria-pressed` was set, the caption
explained what trending meant, and no handler was ever bound. The test we had
asserted that the attribute was in the markup, which it was. A reader clicking it
concluded the ordering could not be changed.

**The control did something other than what it said.** The page describes trending
as engagement decayed by age. The first handler sorted on the raw engagement count,
which is a different ordering. A control that is honest about being switchable and
dishonest about what it switches to is the same problem one layer down.

So these run the page's own script and compare the result against `order.py`, which
is the definition. Drift in either direction fails.
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import ordering_harness as harness  # noqa: E402

from controlbun import order  # noqa: E402

# Fixed so the decay denominator is the same on both sides of the comparison. Far
# enough ahead of the synthetic corpus that every age is positive.
NOW = datetime(2027, 1, 1, tzinfo=timezone.utc)
NOW_MS = int(NOW.timestamp() * 1000)

CHOICES = [order.ORDER_RECENT, order.ORDER_TRENDING]


@pytest.fixture(scope="module")
def pages():
    """Every built page that renders the control.

    One of each shape: a table of models, a table of owners, the claimants on a
    label, and one owner's submissions. They are separate templates that all get
    the control from the layout, which is exactly how five of them ended up with a
    bar and nothing under it to order.
    """
    out = {}
    dist = ROOT / "astro" / "dist"
    for name, rel in [
        ("models", "models/index.html"),
        ("owners", "owners/index.html"),
        ("label", "models/placeholder/other-architecture-7b/refusal/index.html"),
        ("owner", "dana/index.html"),
    ]:
        path = dist / rel
        if path.exists():
            out[name] = path.read_text()
    return out


@pytest.fixture(params=["models", "owners", "label", "owner"])
def page(request, pages):
    if request.param not in pages:
        pytest.skip(f"{request.param} not built; run `make site`")
    return pages[request.param]


def test_every_ordering_is_offered(page):
    """Including the active one.

    The bar used to hide whichever ordering was active, which was harmless while
    the control was a label and became a one-way door the moment it worked: switch
    away and there is no button to switch back.
    """
    assert sorted(harness.bar_choices(page)) == sorted(CHOICES)


def test_the_page_has_something_to_order(page):
    """A bar with no orderable list is the dead control in a second costume."""
    lists = harness.items(page)
    assert lists, "an ordering control renders on a page with no orderable list"
    for items in lists:
        assert items, "an orderable container with no items in it"


def test_every_item_carries_both_ordering_keys(page):
    for items in harness.items(page):
        for item in items:
            assert item["created"], f"no data-created on {item['text'][:40]!r}"
            assert item["engagement"] is not None, (
                f"no data-engagement on {item['text'][:40]!r}; an item missing the "
                "key sorts as zero and silently lands at the bottom"
            )


def test_clicking_binds_and_reorders(page):
    """The regression that started this: the buttons were not wired at all."""
    result = harness.run(page, CHOICES, NOW_MS)
    assert result["bound"], "no click handler is bound to the ordering buttons"
    for key in CHOICES:
        assert result["orders"][key] not in (None, "unbound"), (
            f"the {key!r} button is rendered but nothing happens when it is clicked"
        )


def test_the_pressed_state_follows_the_click(page):
    result = harness.run(page, CHOICES, NOW_MS)
    for key in CHOICES:
        assert result[f"pressed_after_{key}"] == [key], (
            "aria-pressed must name the ordering actually applied, or a screen "
            "reader is told the page is in a state it is not in"
        )


def test_the_caption_names_the_ordering_actually_applied(page):
    """Ordered by X has to keep up with the reader.

    It was rendered once on the server and never touched again, so clicking
    Trending left the page reading "Ordered by Recently added" above a list that
    was no longer in that order. Quieter than a dead control and the same kind of
    wrong: the page describing a state it is not in.
    """
    names = harness.button_names(page)
    result = harness.run(page, CHOICES, NOW_MS)
    for key in CHOICES:
        assert result[f"named_after_{key}"] == names[key]


def test_recency_ordering_matches_order_py(page):
    result = harness.run(page, [order.ORDER_RECENT], NOW_MS)
    for items, got in zip(harness.items(page), result["orders"][order.ORDER_RECENT]):
        want = [i["id"] for i in sorted(
            items, key=lambda i: (-_ms(i["created"]), items.index(i))
        )]
        assert got == want


def test_trending_ordering_matches_order_py(page):
    """The client must compute the function the caption describes.

    Sorting by the raw engagement count would pass a looser test and would still be
    a page that says one thing and does another.
    """
    result = harness.run(page, [order.ORDER_TRENDING], NOW_MS)
    for items, got in zip(harness.items(page), result["orders"][order.ORDER_TRENDING]):
        def weight(i):
            hours = max((NOW_MS - _ms(i["created"])) / 3_600_000.0, 0.0)
            return order.trending_score(int(i["engagement"]), hours)

        want = [i["id"] for i in sorted(
            items, key=lambda i: (-weight(i), items.index(i))
        )]
        assert got == want, (
            "the in-page trending order differs from order.trending_score; the "
            "caption promises engagement decayed by age and the page is computing "
            "something else"
        )


def test_ties_keep_the_order_the_builder_emitted(page):
    """Two items with identical keys must not be reordered against each other.

    Whatever arbitrary order a sort implementation would pick reads as a ranking to
    someone looking at the page, and there is nothing behind it.
    """
    result = harness.run(page, [order.ORDER_RECENT], NOW_MS)
    for items, got in zip(harness.items(page), result["orders"][order.ORDER_RECENT]):
        by_key: dict[str, list[str]] = {}
        for i in items:
            by_key.setdefault(i["created"], []).append(i["id"])
        for tied in by_key.values():
            if len(tied) > 1:
                assert [i for i in got if i in tied] == tied


def _ms(iso: str) -> float:
    return datetime.fromisoformat(iso.replace("Z", "+00:00")).timestamp() * 1000
