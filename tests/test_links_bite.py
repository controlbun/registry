"""Proof that the link check finds a broken link.

`/carol/` was linked from a built page and did not exist, and every test in the
suite passed. The invariants read source, the page tests read one page at a time,
and the falsifier re-derives numbers. None of them follow a link, so nothing could
have caught it.

A checker added after that failure is worth exactly as much as its ability to fail
on that failure. Each case copies the built site, breaks one link in one specific
way, and asserts it goes red. The unbroken copy is checked first, so a green run
here is not vacuous.

carol was a fixture and left with the rest of them on 2026-09-19. The two cases
that named her and named a placeholder model now read the owner and the model
link off the build instead, which is what they should have done from the start:
a bite that names a row stops biting when the row goes, and stopping quietly is
the failure this whole file is about.
"""

from __future__ import annotations

import re
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


def _an_owner_linked_by_name(site: Path) -> str:
    """An owner whose page exists and whose name is linked from another page.

    Read off the build rather than written down. This test named carol, who was
    a fixture and left with the rest of them on 2026-09-19, and a test that
    names a row is a test that dies with the row. What it is about is the
    shape, not the person: somebody's name in a link, and a page at the other
    end that a later change could stop generating.
    """
    owners = sorted(
        p.parent.name for p in site.glob("*/index.html")
        if f'href="/{p.parent.name}/"' in (site / "owners" / "index.html").read_text()
    )
    assert owners, (
        "no owner page is linked by name from /owners/, so the failure this "
        "file exists to reproduce cannot be reproduced"
    )
    return owners[0]


def test_an_owner_linked_by_name_with_no_page_is_caught(site):
    """The exact shape of the original: a person linked by name with no page.

    `/carol/` shipped this way for days. Deleting the page rather than editing
    a link, because that is how it happened. Nobody wrote a bad href; the page
    was simply never generated, and the name went on being printed as a link.

    Only `index.html` goes, not the directory, so what is left is the state the
    build would actually produce: everything filed under that owner still
    exists and the owner's own page does not.
    """
    owner = _an_owner_linked_by_name(site)
    (site / owner / "index.html").unlink()
    broken = linkcheck.broken_links(site)
    assert f"/{owner}/" in broken
    assert broken[f"/{owner}/"], (
        "the check found the dead target but not who links it"
    )


def test_a_typo_in_an_href_is_caught(site):
    page = site / "models" / "index.html"
    before = page.read_text()
    # Read off the page rather than typed, for the reason above: the model this
    # named was a placeholder in the fixture corpus. The mutation drops one
    # character from the end of a real model link, which is the typo shape.
    link = re.search(r'href="(/models/[^"]+/)"', before)
    assert link, "no model link on /models/, so there is nothing here to break"
    after = before.replace(
        f'href="{link.group(1)}"', f'href="{link.group(1)[:-2]}/"', 1
    )
    # The mutation has to land, or this asserts the checker found nothing and
    # calls that a pass. The first draft of this test did exactly that.
    assert after != before, "the href this test mutates is no longer on the page"
    page.write_text(after)
    assert link.group(1)[:-2] + "/" in linkcheck.broken_links(site)


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
