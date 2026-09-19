"""Proof that the falsifier falsifies.

A falsifier that has never failed is a script that prints a reassuring line. The
arena's version earned its place by exiting non-zero on real drift, and the only
way to know this one would is to drift it on purpose.

Each case copies the tree, breaks one thing, and asserts the run goes red. The
clean copy is checked first, so a green result below is not vacuous.
"""

from __future__ import annotations

import importlib.util
import json
import shutil
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _load_falsifier(root: Path):
    spec = importlib.util.spec_from_file_location(
        "probed_falsifier", root / "falsifier" / "verify.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    module.ROOT = root
    module.DB = root / "registry.db"
    module.EXPORT = root / "astro" / "src" / "data" / "registry.json"
    module.DIST = root / "astro" / "dist"
    module.failures = []
    return module


@pytest.fixture(scope="module")
def tree(tmp_path_factory):
    """A copy with a database, an export and a built site."""
    dest = tmp_path_factory.mktemp("falsify") / "repo"
    dest.mkdir()
    for part in ("falsifier", "fixtures", "schema", "src"):
        shutil.copytree(ROOT / part, dest / part)
    (dest / "astro" / "src" / "data").mkdir(parents=True)
    (dest / "astro" / "dist").mkdir(parents=True)

    subprocess.run(
        [sys.executable, str(dest / "fixtures" / "build.py"),
         "--db", str(dest / "registry.db")],
        check=True, capture_output=True,
    )
    subprocess.run(
        [sys.executable, "-m", "registry.export",
         "--db", str(dest / "registry.db"),
         "--out", str(dest / "astro" / "src" / "data" / "registry.json")],
        check=True, capture_output=True,
        env={"PYTHONPATH": str(dest / "src"), "PATH": "/usr/bin:/bin"},
        cwd=dest,
    )

    # A built page is needed for the rendered-number checks. One page carrying a
    # published figure and the synthetic marker is enough to exercise both.
    payload = json.loads((dest / "astro" / "src" / "data" / "registry.json").read_text())
    trait = payload["labels"][0]["claimants"][0]["trait_score"]
    page = dest / "astro" / "dist" / "probe"
    page.mkdir(parents=True)
    (page / "index.html").write_text(
        f"<html><body><p>Synthetic corpus. Trait {trait:.4f}</p></body></html>"
    )
    return dest


def run(root: Path) -> int:
    return _load_falsifier(root).main()


def test_the_clean_copy_passes(tree):
    assert run(tree) == 0, "copy is already failing, so nothing below proves anything"


def test_a_stored_norm_that_no_longer_matches_the_tensor(tree):
    db = tree / "registry.db"
    conn = sqlite3.connect(db)
    before = conn.execute(
        "SELECT id, l2_norm FROM intervention LIMIT 1"
    ).fetchone()
    conn.execute("UPDATE intervention SET l2_norm = 99.0 WHERE id = ?", (before[0],))
    conn.commit(); conn.close()
    try:
        assert run(tree) == 1, "a stored norm that contradicts the tensor must fail"
    finally:
        conn = sqlite3.connect(db)
        conn.execute("UPDATE intervention SET l2_norm = ? WHERE id = ?",
                     (before[1], before[0]))
        conn.commit(); conn.close()


def test_a_published_angle_that_does_not_recompute(tree):
    path = tree / "astro" / "src" / "data" / "registry.json"
    original = path.read_text()
    payload = json.loads(original)
    for entry in payload["labels"]:
        for pair in entry["pairs"]:
            if pair["angle_similarity"] is not None:
                pair["angle_similarity"] = 0.5
    path.write_text(json.dumps(payload))
    try:
        assert run(tree) == 1, "an angle that does not recompute must fail"
    finally:
        path.write_text(original)


def test_a_number_on_a_page_that_exists_nowhere_upstream(tree):
    """The check that matters: a figure nothing produced."""
    page = tree / "astro" / "dist" / "probe" / "index.html"
    original = page.read_text()
    page.write_text(original.replace("</p>", " Transfer 0.6180</p>"))
    try:
        assert run(tree) == 1, "a fabricated figure on a page must fail"
    finally:
        page.write_text(original)


def test_an_export_that_drifted_from_the_database(tree):
    path = tree / "astro" / "src" / "data" / "registry.json"
    original = path.read_text()
    payload = json.loads(original)
    for entry in payload["labels"]:
        for claimant in entry["claimants"]:
            if claimant["trait_score"] is not None:
                claimant["trait_score"] = 0.1234
    path.write_text(json.dumps(payload))
    try:
        assert run(tree) == 1, "an export that contradicts the database must fail"
    finally:
        path.write_text(original)


def test_a_fabricated_figure_published_without_its_marker(tree):
    page = tree / "astro" / "dist" / "probe" / "index.html"
    original = page.read_text()
    page.write_text(original.replace("Synthetic corpus. ", ""))
    try:
        assert run(tree) == 1, "synthetic figures with no marker must fail"
    finally:
        page.write_text(original)


def test_a_reason_beside_an_absence_that_renders_unmarked(tree):
    """The marking guard covers the other kind of authored prose too.

    A reason names the file and the line where somebody looked for a value, so
    it carries numerals the same way a definition quoting its own measurements
    does. Rendered outside a `data-authored` region it goes under the number
    scan as a figure this registry derived, which is the reading the 2026-09-19
    decision exists to stop.

    The reason here is a sentence this test wrote about a fixture, which is why
    it says so: `fixtures/SYNTHETIC.md` covers invented prose as much as
    invented numbers.
    """
    path = tree / "astro" / "src" / "data" / "registry.json"
    original = path.read_text()
    payload = json.loads(original)
    claimant = payload["labels"][0]["claimants"][0]
    reason = ("Written by the test suite about a fixture. Nothing hashed a "
              "chat template here because nothing generated any text.")
    claimant["absences"] = {"chat_template_hash": reason}
    path.write_text(json.dumps(payload))

    page = tree / "astro" / "dist" / "probe" / "index.html"
    was = page.read_text()
    try:
        page.write_text(was.replace("</p>", f"</p><p>{reason}</p>"))
        assert run(tree) == 1, (
            "a reason rendered with no `data-authored` on it passed, so the "
            "exclusion in `text_of` is worth less than the marking it assumes"
        )
        # Padded with ordinary page copy, because the other half of this guard
        # fails a page that is more quoted prose than page and this stand-in
        # page is one sentence long.
        filler = " ".join(["The registry never designates and a consumer pins."] * 8)
        page.write_text(was.replace(
            "</p>", f"</p><p>{filler}</p><p data-authored>{reason}</p>"))
        assert run(tree) == 0, (
            "the same reason inside a marked region failed, so the guard is "
            "refusing the prose rather than checking where it sits"
        )
    finally:
        page.write_text(was)
        path.write_text(original)


def test_a_missing_artifact_is_not_silently_skipped(tree):
    held = tree / "fixtures" / "alice_kindness_v1.safetensors"
    moved = held.with_suffix(".held")
    held.rename(moved)
    try:
        assert run(tree) == 1, "a missing raw artifact must fail, not pass quietly"
    finally:
        moved.rename(held)
