"""The 404 is a page on this site, and its links are checked like any other.

Two things are under test and they are separate.

The page itself: Astro's built-in 404 is a dark monospace framework default with
no header, no navigation and no way home, against a light serif site. A stranger
reading the site cold hit it twice, once on a nonsense URL and once by trimming a
submission URL back to reach the label view, which is the guess a GitHub-shaped
URL trains you to make. Being lost is the one moment the header matters most.

And the link checker, which globbed `index.html`. Clean URLs mean almost every
page is an index.html, so scanning only those made the one page that is not
invisible: `404.html` shipped with six links and nothing read them. That is the
same shape as the invariant scanner enumerating two directories and missing the
third, so it gets the same treatment: a probe that goes unnoticed under the old
pattern.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "astro" / "dist"
PAGE = DIST / "404.html"

sys.path.insert(0, str(ROOT / "falsifier"))


def page() -> str:
    if not PAGE.exists():
        pytest.skip("astro/dist/404.html not built; run `make site`")
    return PAGE.read_text()


def test_the_404_is_built_at_all():
    assert PAGE.exists(), (
        "no 404.html in the build, so the host serves its own default"
    )


def test_the_404_carries_the_site_and_a_way_home():
    html = page()
    # The nav, which is the thing the default threw away.
    assert "SiteNav" in html or 'href="/models/"' in html, "no site navigation"
    assert 'href="/owners/"' in html
    # An explicit way back, not just the wordmark.
    assert 'href="/"' in html, "no link home"
    # The site's own stylesheet rather than a framework default.
    assert "<style" in html or ".css" in html, "unstyled"


def test_the_404_does_not_claim_anything_was_removed():
    """A 404 that apologizes implies the thing existed and is gone."""
    html = page().lower()
    for phrase in ("has been removed", "no longer available", "was deleted"):
        assert phrase not in html, f"the 404 says {phrase!r}, which is a claim"


def test_the_404_carries_no_synthetic_marker():
    """It publishes no figure, so the corpus marker would describe nothing."""
    assert "Synthetic corpus" not in page()


# --------------------------------------------------------------------------- #
# The link checker, and the bite.


def _links():
    import importlib

    module = importlib.import_module("links")
    return importlib.reload(module)


def test_the_link_checker_reads_the_404():
    """It globbed index.html, so this page's links were never read."""
    links = _links()
    if not DIST.exists():
        pytest.skip("site not built; run `make site`")

    pages = list(DIST.rglob("*.html"))
    indexes = list(DIST.rglob("index.html"))
    assert len(pages) > len(indexes), (
        "no non-index page exists, so this test cannot tell the two globs apart"
    )
    assert not links.broken_links(), "the built site has broken links"


def test_a_broken_link_on_the_404_is_caught(tmp_path):
    """The probe, and it is asserted to go unnoticed under the old glob.

    Built by hand rather than by mutating `astro/dist`, because mutating the real
    build in place is a defect this suite already carries elsewhere and an
    interrupt mid-run leaves it broken.
    """
    links = _links()
    site = tmp_path / "dist"
    (site / "real").mkdir(parents=True)
    (site / "index.html").write_text('<a href="/real/">fine</a>')
    (site / "real" / "index.html").write_text("<p>here</p>")
    (site / "404.html").write_text('<a href="/does-not-exist/">broken</a>')

    # Wide: caught.
    broken = links.broken_links(site)
    assert "/does-not-exist/" in broken, "a broken link on the 404 went unnoticed"
    assert broken["/does-not-exist/"] == {"/404.html"}

    # Narrow, the old behavior: nothing. This is the gap, reproduced.
    missed: dict[str, set[str]] = {}
    pages = links.built_pages(site)
    for p in sorted(site.rglob("index.html")):
        rel = p.relative_to(site).as_posix()
        source = "/" + rel[: -len("index.html")]
        for href in links.HREF.findall(p.read_text()):
            target = href.split("#")[0].split("?")[0]
            if target and target not in pages:
                missed.setdefault(target, set()).add(source)
    assert not missed, (
        "the old index.html-only glob would have caught this, so the widening is "
        "not what fixed it and this test proves nothing"
    )
