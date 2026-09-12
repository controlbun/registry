"""What a reader is actually shown.

The invariant tests catch banned constructs in the templates. These check the
rendered output, which is the only place the rules finally bind: a template can be
clean and still print a number it should not.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from registry import db, render  # noqa: E402


def build_db(tmp_path: Path) -> Path:
    path = tmp_path / "fixture.db"
    subprocess.run(
        [sys.executable, str(ROOT / "fixtures" / "build.py"), "--db", str(path)],
        check=True, capture_output=True,
    )
    return path


def text_of(html: str) -> str:
    """Reader-visible copy only.

    Script and style contents survive naive tag-stripping and are not text a reader
    sees. Leaving CSS in produced a false positive once already: the hex colour
    #1a1a1a contains "#1" and read as a ranking marker.
    """
    for tag in ("script", "style"):
        html = re.sub(rf"<{tag}.*?</{tag}>", "", html, flags=re.S)
    return re.sub(r"<[^>]+>", " ", html)


@pytest.fixture
def page(tmp_path):
    conn = db.connect(build_db(tmp_path))
    return render.render_label(conn, "kindness", tmp_path / "site").read_text()


def test_every_claimant_appears(page):
    assert "alice/kindness@v1" in page
    assert "bob/kindness@v1" in page


def test_page_says_it_does_not_resolve(page):
    assert "does not resolve to an artifact" in text_of(page)


def test_absent_transfer_reads_as_absent_not_zero(page):
    body = text_of(page)
    assert "not measured" in body, "bob measured no transfer and the page must say so"
    assert "0.0000" not in body, "an unmeasured value must never print as a zero"


def test_synthetic_corpus_is_announced(page):
    assert "Synthetic corpus" in text_of(page)


def test_cosine_carries_its_caveat(page):
    body = text_of(page)
    assert "Angle similarity" in body
    assert "not evidence that" in body and "disagree" in body, (
        "the number may be shown, but never without the caveat that makes it honest"
    )


def test_nothing_is_ranked(page):
    body = text_of(page).lower()
    # The word "rank" appears once, in the caption saying nothing is ranked. What
    # must be absent is an actual ordering: positions, ordinals, a composite.
    for marker in ("#1", "#2", "1st", "2nd", "winner", "overall score",
                   "composite", "top pick", "ranked #"):
        assert marker not in body, f"page implies an ordering via {marker!r}"
    # A default ordering now exists, so the claim is no longer that nothing is
    # ordered. It is that the ordering is disclosed and changeable, which is what
    # separates a starting point from a verdict.
    assert "ordered by" in body, "the active ordering must be named on screen"


def test_ordering_is_switchable(page):
    body = text_of(page)
    assert "Recently added" in body or "Trending" in body
    assert 'data-order=' in page, "a reader must be able to change the ordering"


def test_ordering_explains_itself(page):
    body = text_of(page).lower()
    assert "newest first" in body or "decayed by age" in body, (
        "an ordering the reader cannot interrogate is a verdict wearing a label"
    )


def test_score_without_coherence_renders_as_uninterpretable(tmp_path):
    """The fixtures both report coherence, so construct the case that matters."""
    conn = db.connect(build_db(tmp_path))
    # 0.1357 is deliberately not a repeated-digit decimal, so it cannot collide
    # with any fixture value and a hit below is unambiguously the suppressed score.
    conn.execute(
        "UPDATE eval_report SET coherence_score = NULL, trait_score = 0.1357"
        " WHERE intervention_id = 'iv_alice'"
    )
    conn.commit()

    body = text_of(render.render_label(conn, "kindness", tmp_path / "s2").read_text())
    assert "uninterpretable" in body
    assert "0.1357" not in body, (
        "a trait score with no coherence measure beside it must not print as a "
        "number; judge agreement collapses on degenerate text and an unpaired "
        "score is a broken instrument rather than a small effect"
    )
