"""Every page gets the same head.

There were two of them. `Base.astro` builds the document for every page except the
home page, which builds its own because it has a different column layout. They
drifted, and the drift had a consequence: the script that reads the reader's saved
theme was only on the home page. You could switch to light, click through to
`/models/`, and land back in dark, because the preference was written by a toggle
on one page and read by nobody anywhere else.

That is the same failure as the two frontends, one page instead of one framework:
a second copy of something that has to stay in step, with nothing keeping it there.

These check the things a head is load-bearing for, across every built page, so a
third head cannot be added quietly.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "astro" / "dist"


def pages() -> list[Path]:
    if not DIST.exists():
        pytest.skip("site not built; run `make site`")
    found = sorted(DIST.rglob("index.html"))
    assert found, "no built pages"
    return found


def test_every_page_applies_the_saved_theme():
    """The bug this file exists for.

    Dark is the default, the toggle writes `theme` to localStorage, and a page
    that never reads it renders the default no matter what the reader chose.
    """
    for p in pages():
        assert 'localStorage.getItem("theme")' in p.read_text(), (
            f"{p.relative_to(DIST)} never reads the saved theme, so a reader who "
            "picked one gets the default here"
        )


def test_the_theme_script_runs_before_paint():
    """Inline, not a module.

    A bundled or deferred script runs after first paint, which produces exactly
    the flash of the wrong theme the script is there to prevent.
    """
    for p in pages():
        html = p.read_text()
        # Absence is the other test's finding. Crashing here would report a
        # ValueError for a condition that already has a clear failure message.
        if 'localStorage.getItem("theme")' not in html:
            continue
        i = html.index('localStorage.getItem("theme")')
        tag_start = html.rindex("<script", 0, i)
        tag = html[tag_start:html.index(">", tag_start) + 1]
        assert "src=" not in tag, f"{p.relative_to(DIST)}: theme script is external"
        assert "type=\"module\"" not in tag, (
            f"{p.relative_to(DIST)}: theme script is a module, so it runs after paint"
        )
        assert i < html.index("<body"), (
            f"{p.relative_to(DIST)}: theme script is not in the head"
        )


def test_every_page_declares_a_favicon():
    for p in pages():
        assert 'rel="icon"' in p.read_text(), (
            f"{p.relative_to(DIST)} has no favicon"
        )


def test_every_declared_icon_exists():
    """A head referencing an icon that was never built is a broken link the link
    checker does not follow, because it is not an anchor."""
    for p in pages():
        for href in re.findall(r'rel="(?:icon|apple-touch-icon)"[^>]*href="([^"]+)"',
                               p.read_text()):
            assert (DIST / href.lstrip("/")).exists(), (
                f"{p.relative_to(DIST)} points at {href}, which was not built"
            )


def test_both_themes_have_an_icon():
    """The artwork has an opaque background rather than alpha, so one icon is a
    white tile in dark browser chrome or a black tile in light chrome."""
    html = pages()[0].read_text()
    assert "prefers-color-scheme: light" in html
    assert "prefers-color-scheme: dark" in html
    unqualified = re.findall(r'<link rel="icon"(?![^>]*media=)[^>]*>', html)
    assert unqualified, (
        "every icon is behind a media query, so a browser that ignores media on "
        "link elements gets no favicon at all"
    )


def test_every_page_has_a_title():
    for p in pages():
        m = re.search(r"<title>(.*?)</title>", p.read_text())
        assert m and m.group(1).strip(), f"{p.relative_to(DIST)} has no title"
