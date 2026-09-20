"""Contrast is computed, not reasoned about.

`--faint` sat at 2.90:1 for months, below AA and below the large-text floor,
while the palette comment above it argued carefully about two other colors. It
is the token carrying every "not measured" and "not recorded" on this site, so
the states this project treats as load-bearing were the hardest text on it to
read.

A hand-written table of ratios goes stale the first time somebody nudges a hex
value, and nothing recomputes it. This does.

**Measured against `--wash` and not against white.** White is the lightest
surface and therefore the easiest one, and `a { color: var(--accent) }` is
global while table rows, panel headers and the hover state all set
`background: var(--wash)`. A color tuned on white and used on #fafafa is tuned
against a surface it is rarely on.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSS = ROOT / "astro" / "src" / "styles" / "app.css"

AA = 4.5


def _luminance(hex_color: str) -> float:
    h = hex_color.lstrip("#")
    parts = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    lin = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
           for c in parts]
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]


def ratio(fg: str, bg: str) -> float:
    a, b = _luminance(fg), _luminance(bg)
    hi, lo = max(a, b), min(a, b)
    return (hi + 0.05) / (lo + 0.05)


def token(name: str) -> str:
    """The first declared value of a custom property, from the light theme."""
    m = re.search(rf"--{name}:\s*(#[0-9a-fA-F]{{6}})", CSS.read_text())
    assert m, f"--{name} is not declared in app.css"
    return m.group(1)


def test_the_ratio_function_is_right_before_anything_leans_on_it():
    """Two known values. A checker nobody checked is worth nothing."""
    assert round(ratio("#000000", "#ffffff"), 2) == 21.0
    assert round(ratio("#ffffff", "#ffffff"), 2) == 1.0


def test_every_text_token_clears_aa_on_the_surface_it_sits_on():
    """Against `--wash`, which is the worst light surface text lands on."""
    wash = token("wash")
    offenders = []
    for name in ("ink", "dim", "faint", "accent", "status"):
        r = ratio(token(name), wash)
        if r < AA:
            offenders.append(f"--{name} {token(name)} on {wash} is {r:.2f}:1")
    assert not offenders, (
        "text below WCAG AA on the surface it actually sits on:\n  "
        + "\n  ".join(offenders)
    )


def test_it_bites_on_the_value_that_shipped():
    """`#356AFF` cleared AA on white at 4.51:1 and failed on --wash at 4.32:1,
    and it was live on a public site. The check has to catch that exact case."""
    assert ratio("#356AFF", "#ffffff") >= AA, "it did clear AA on white"
    assert ratio("#356AFF", "#fafafa") < AA, "and failed on the real surface"
