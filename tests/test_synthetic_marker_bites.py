"""Reintroduce the defects the synthetic-marker check exists to catch.

A check that passes on a healthy tree proves nothing about what it would catch.
Each case below mutates the built site, runs the falsifier, and restores the file,
and the mutation is asserted to have landed before the result is believed. That
guard is not decoration: three bite tests in this repo have passed while changing
nothing, and a bite that mutates nothing is indistinguishable from a check that
works.

The second case is the one that did not exist before. The marker used to be a
single corpus-wide flag, so the only failure it could see was a fabricated page
missing its banner. The opposite failure, a real measurement rendered under a
banner saying every figure on the page is invented, was unreachable while the
corpus was entirely fabricated and arrived the day it was not.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "astro" / "dist"

SYNTHETIC_PAGE = DIST / "alice/placeholder/does-not-resolve-1b/kindness/v1/index.html"
REAL_PAGE = DIST / "soham/allenai/Olmo-3-1125-32B/pro-human/meandiff/index.html"


def falsifier() -> str:
    result = subprocess.run(
        [sys.executable, str(ROOT / "falsifier" / "verify.py")],
        capture_output=True, text=True,
    )
    return result.stdout + result.stderr


def bite(path: Path, mutate) -> str:
    """Apply a mutation, run the falsifier, put the file back."""
    if not path.exists():
        pytest.skip(f"{path.relative_to(ROOT)} not built; run `make site`")
    original = path.read_text()
    mutated = mutate(original)
    assert mutated != original, (
        "the mutation changed nothing, so this test would pass whatever the "
        "falsifier does"
    )
    path.write_text(mutated)
    try:
        return falsifier()
    finally:
        path.write_text(original)


def test_the_built_site_is_clean_first():
    """If the tree is already red, neither result below means anything."""
    assert "re-derives or traces to its source" in falsifier()


def test_a_fabricated_page_without_its_marker_fails():
    out = bite(SYNTHETIC_PAGE, lambda s: s.replace("Synthetic corpus", "Corpus", 1))
    assert "with no marker on the page" in out


def test_a_real_page_carrying_the_marker_fails():
    out = bite(REAL_PAGE, lambda s: s.replace("<main>", "<main><p>Synthetic corpus.</p>", 1))
    assert "carries the synthetic marker but every figure on it traces to a real" in out
