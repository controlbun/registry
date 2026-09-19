"""Proof that the ordering tests would have caught the ordering bug.

The control shipped broken under a green suite. The test that was supposed to
cover it asserted that an attribute appeared in the markup, which it did, so the
suite reported health while a reader clicking the buttons got nothing. A test
written after a bug is worth exactly as much as its ability to fail on that bug.

So each case takes a real built page, reintroduces one specific failure, and
asserts the corresponding check goes red. The unbroken page is checked first, so a
green run here is not vacuous.
"""

from __future__ import annotations

import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import ordering_harness as harness  # noqa: E402

from controlbun import order  # noqa: E402

NOW_MS = int(datetime(2027, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)
CHOICES = [order.ORDER_RECENT, order.ORDER_TRENDING]
PAGE = ROOT / "astro" / "dist" / "models" / "index.html"


@pytest.fixture(scope="module")
def clean() -> str:
    if not PAGE.exists():
        pytest.skip("site not built; run `make site`")
    html = PAGE.read_text()
    result = harness.run(html, CHOICES, NOW_MS)
    assert result["bound"], "the unmodified page is already broken"
    return html


def test_the_original_bug_is_caught(clean):
    """The handler is deleted, leaving the buttons and the caption in place.

    This is exactly what shipped: markup that reads as a working control with
    nothing behind it.
    """
    script = harness.ordering_script(clean)
    broken = clean.replace(script, "// nothing at all\n")
    with pytest.raises(AssertionError, match="exactly one ordering script"):
        harness.run(broken, CHOICES, NOW_MS)


def test_a_handler_bound_to_nothing_is_caught(clean):
    """Subtler than no handler: a handler that queries a selector nobody emits."""
    broken = clean.replace('querySelectorAll("[data-orderable]")',
                           'querySelectorAll("[data-sortable]")')
    assert broken != clean
    with pytest.raises(AssertionError, match="unshimmed selector"):
        harness.run(broken, CHOICES, NOW_MS)


def _disagreeing(html: str) -> str:
    """The same page with one row made old and busy and one made new and quiet.

    The synthetic corpus was released on a single day, so recency is a flat tie
    there and decayed trending collapses into the raw engagement count. On that
    data the wrong function and the right one agree, and a check that only ever
    sees agreeing inputs proves nothing. This constructs the disagreement rather
    than waiting for the fixtures to contain one.
    """
    rows = re.findall(r'data-created="[^"]*" data-engagement="[^"]*"', html)
    assert len(rows) >= 2, "need two rows to make them disagree"
    html = html.replace(
        rows[0], 'data-created="2020-01-01T00:00:00Z" data-engagement="50"', 1)
    return html.replace(
        rows[1], 'data-created="2026-12-31T00:00:00Z" data-engagement="0"', 1)


def test_the_wrong_trending_function_is_caught(clean):
    """Flatten the decay and trending becomes a raw engagement count.

    This is the version that was written first. It sorts, it looks alive, and it
    is not the ordering the caption above it describes: an old submission with a
    pile of attacks would outrank everything new forever.
    """
    page = _disagreeing(clean)
    broken = page.replace(
        "Math.pow(hours + corpus.age_offset_hours, corpus.gravity)", "1")
    assert broken != page

    items = harness.items(page)[0]

    def weight(i):
        hours = max((NOW_MS - _ms(i["created"])) / 3_600_000.0, 0.0)
        return order.trending_score(int(i["engagement"]), hours)

    want = [i["id"] for i in sorted(items, key=lambda i: (-weight(i), items.index(i)))]

    honest = harness.run(page, [order.ORDER_TRENDING], NOW_MS)
    assert honest["orders"][order.ORDER_TRENDING][0] == want, (
        "the shipped handler disagrees with order.trending_score"
    )

    flattened = harness.run(broken, [order.ORDER_TRENDING], NOW_MS)
    assert flattened["orders"][order.ORDER_TRENDING][0] != want, (
        "dropping the age decay changed nothing, so this check cannot tell the "
        "described ordering from an undecayed count"
    )


def test_a_row_missing_its_ordering_key_is_caught(clean):
    """A row with no key sorts as zero and lands at the bottom without saying why."""
    broken = clean.replace(' data-engagement="', " data-eng=\"", 1)
    assert broken != clean
    missing = [
        i for lst in harness.items(broken) for i in lst if i["engagement"] is None
    ]
    assert missing, "the mutation did not actually drop a key"


def test_hiding_the_active_choice_is_caught(clean):
    """A bar that omits whichever ordering is already applied.

    Harmless while the control was decorative, and a one-way door once it worked:
    the reader switches away from an ordering and has no button to switch back.
    """
    broken = clean.replace('data-order-key="recently-added"', 'data-inert="x"', 1)
    assert broken != clean
    assert sorted(harness.bar_choices(broken)) != sorted(CHOICES)


def _ms(iso: str) -> float:
    return datetime.fromisoformat(iso.replace("Z", "+00:00")).timestamp() * 1000
