"""Proof that the link check finds a broken link.

`/carol/` was linked from a built page and did not exist, and every test in the
suite passed. The invariants read source, the page tests read one page at a time,
and the falsifier re-derives numbers. None of them follow a link, so nothing could
have caught it.

A checker added after that failure is worth exactly as much as its ability to fail
on that failure. Each case copies the built site, breaks one link in one specific
way, and asserts it goes red. The unbroken copy is checked first, so a green run
here is not vacuous.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "falsifier"))

import links as linkcheck  # noqa: E402

DIST = ROOT / "astro" / "dist"


@pytest.fixture
def site(tmp_path):
    if not DIST.exists():
        pytest.skip("site not built; run `make site`")
    dest = tmp_path / "dist"
    shutil.copytree(DIST, dest)
    assert not linkcheck.broken_links(dest), "the unmodified site is already broken"
    return dest


def test_the_carol_case_is_caught(site):
    """The exact shape of the original: a person linked by name with no page.

    Deleting the directory rather than editing a link, because that is how it
    happened. Nobody wrote a bad href. The page was simply never generated.
    """
    shutil.rmtree(site / "carol")
    broken = linkcheck.broken_links(site)
    assert "/carol/" in broken
    assert broken["/carol/"], "the check found the dead target but not who links it"


def test_a_typo_in_an_href_is_caught(site):
    page = site / "models" / "index.html"
    before = page.read_text()
    after = before.replace(
        'href="/models/placeholder/does-not-resolve-1b/"',
        'href="/models/placeholder/does-not-resolv-1b/"',
    )
    # The mutation has to land, or this asserts the checker found nothing and
    # calls that a pass. The first draft of this test did exactly that.
    assert after != before, "the href this test mutates is no longer on the page"
    page.write_text(after)
    assert "/models/placeholder/does-not-resolv-1b/" in linkcheck.broken_links(site)


def test_a_link_to_a_page_that_was_never_built_is_caught(site):
    page = site / "index.html"
    page.write_text(
        page.read_text().replace("</body>", '<a href="/v1/upload/">x</a></body>')
    )
    assert "/v1/upload/" in linkcheck.broken_links(site)


def test_a_fragment_is_not_treated_as_a_missing_page(site):
    """`/models/#claimants` is a target on a page, not another page."""
    page = site / "index.html"
    page.write_text(
        page.read_text().replace("</body>", '<a href="/models/#claimants">x</a></body>')
    )
    assert not linkcheck.broken_links(site)


def test_an_asset_link_resolves_by_exact_path(site):
    """CSS and the search bundle are linked directly, not as clean URLs.

    Resolving every href as a directory would have flagged all of them, which is
    the failure mode that makes a checker get switched off.
    """
    assert not linkcheck.broken_links(site)
    css = [p for p in site.rglob("*.css")]
    assert css, "no stylesheet in the build to exercise this"
