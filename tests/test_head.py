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


def test_the_favicon_has_an_alpha_channel():
    """This is what lets one icon set serve both themes.

    The artwork used to ship with an opaque background, so a single file was a
    white tile in dark browser chrome or a black tile in light. The workaround was
    two sets behind `prefers-color-scheme` media queries on the link elements,
    which Chrome ignores.

    Cutting the background out replaced that with something simpler and better:
    the outlined mark reads on white, on near-black and on mid gray because the
    outline draws every edge regardless of what is behind it. That only holds
    while the icons actually carry alpha. Regenerate them from a flattened export
    and the favicon silently becomes a tile again, on a surface nobody tests.
    """
    import struct

    icons = sorted(DIST.glob("icon-*.png"))
    assert icons, "no icons in the build"
    for path in icons:
        data = path.read_bytes()
        assert data[:8] == b"\x89PNG\r\n\x1a\n", f"{path.name} is not a png"
        w, h, depth, ctype = struct.unpack(">IIBB", data[16:26])
        assert ctype in (4, 6), (
            f"{path.name} is color type {ctype}, which has no alpha channel. "
            "On a dark browser tab this renders as a light tile."
        )
        assert w == h, f"{path.name} is {w}x{h}, not square"


def test_every_page_has_a_title():
    for p in pages():
        m = re.search(r"<title>(.*?)</title>", p.read_text())
        assert m and m.group(1).strip(), f"{p.relative_to(DIST)} has no title"


def test_the_cname_reaches_the_build():
    """Pages reads this out of the published output to answer on the domain.

    In `astro/public/` rather than a hosting dashboard, so the domain is in
    version control and a rebuild cannot drop it silently.
    """
    if not DIST.exists():
        pytest.skip("site not built; run `make site`")
    cname = DIST / "CNAME"
    assert cname.exists(), "no CNAME in the build; Pages would serve the default domain"
    assert cname.read_text().strip() == "controlbun.com"


def test_every_page_carries_an_absolute_canonical_matching_its_own_path():
    """A relative canonical is not a canonical, and a wrong one is worse.

    Checked per page rather than once, because the URL is derived from
    `Astro.url.pathname` and a layout that built its own head would get a
    different answer. Two heads drifting is what this component exists to stop.
    """
    for path in pages():
        html = path.read_text()
        m = re.search(r'<link rel="canonical" href="([^"]+)"', html)
        assert m, f"{path.relative_to(DIST)} has no canonical"
        href = m.group(1)
        assert href.startswith("https://controlbun.com/"), (
            f"{path.relative_to(DIST)} canonical is not absolute: {href}"
        )
        rel = path.relative_to(DIST).as_posix()
        expected = "/" + rel[: -len("index.html")] if rel.endswith("index.html") else "/" + rel
        assert href == "https://controlbun.com" + expected, (
            f"{path.relative_to(DIST)} claims to be {href}"
        )


def test_link_previews_are_present_and_the_title_is_the_page_title():
    """The unfurled card is the only part of this many people will read."""
    home = (DIST / "index.html").read_text() if (DIST / "index.html").exists() \
        else pytest.skip("home page not built")
    for name in ("og:type", "og:site_name", "og:description", "og:url", "og:image"):
        assert f'property="{name}"' in home, f"{name} missing"
    assert 'name="twitter:card"' in home

    # Per page, not site-wide, or every shared link says the same thing.
    deep = DIST / "soham/allenai/Olmo-3-1125-32B/pro-human/meandiff/index.html"
    if not deep.exists():
        pytest.skip("submission page not built")
    m = re.search(r'<meta property="og:title" content="([^"]+)"', deep.read_text())
    assert m and "pro-human@meandiff" in m.group(1), (
        "og:title is not the page's own title"
    )
