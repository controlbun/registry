"""Proof that the falsifier falsifies.

A falsifier that has never failed is a script that prints a reassuring line. The
arena's version earned its place by exiting non-zero on real drift, and the only
way to know this one would is to drift it on purpose.

Each case copies the tree, breaks one thing, and asserts the run goes red. The
clean copy is checked first, so a green result below is not vacuous.

**The tree is built from `tests/probe.py` rather than from the corpus.** Until
2026-09-19 it was built from `fixtures/build.py`, which is gone: a public site
whose corpus is half fabricated invites "is this real", so the fabricated half
left. What the bites need is not that half specifically, it is a corpus holding
the states a falsifier has to be able to see, and several of those states the
real corpus has never been in. Two claimants on one label give the angle check
something to recompute. An author who reported a trait score gives the transport
check something to drift. An absence with a reason beside it gives the marking
guard something to unmark. The probe supplies all of them, in a temporary
directory, marked synthetic in every row, reachable by no page.

Where a bite is stronger against the real vendored artifacts it lives in
`tests/test_artifact_digest_bite.py` instead, which seeds from `artifacts/` and
holds the one case that can only be made there: a digest checked against a
second, independent record rather than against the bytes it was derived from.
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
    module.EXPORT = root / "astro" / "src" / "data" / "controlbun.json"
    module.DIST = root / "astro" / "dist"
    module.failures = []
    return module


@pytest.fixture(scope="module")
def tree(tmp_path_factory):
    """A copy with a probe database, an export and a built site.

    `tests/probe.py` is run from this repository and pointed at the copy with
    `--root`, so the tensors land under `dest/tests/_probe/` and every row
    records the path that resolves to them there. The falsifier module loaded
    below has its own `ROOT` set to the copy, so nothing it reads or hashes
    comes from the working tree.
    """
    dest = tmp_path_factory.mktemp("falsify") / "repo"
    dest.mkdir()
    for part in ("falsifier", "schema", "src"):
        shutil.copytree(ROOT / part, dest / part,
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    (dest / "astro" / "src" / "data").mkdir(parents=True)
    (dest / "astro" / "dist").mkdir(parents=True)

    subprocess.run(
        [sys.executable, str(ROOT / "tests" / "probe.py"),
         "--db", str(dest / "registry.db"), "--root", str(dest)],
        check=True, capture_output=True,
    )
    subprocess.run(
        [sys.executable, "-m", "controlbun.export",
         "--db", str(dest / "registry.db"),
         "--out", str(dest / "astro" / "src" / "data" / "controlbun.json")],
        check=True, capture_output=True,
        env={"PYTHONPATH": str(dest / "src"), "PATH": "/usr/bin:/bin"},
        cwd=dest,
    )

    # A built page is needed for the rendered-number checks. One page carrying a
    # published figure and the synthetic marker is enough to exercise both.
    payload = json.loads((dest / "astro" / "src" / "data" / "controlbun.json").read_text())
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
    path = tree / "astro" / "src" / "data" / "controlbun.json"
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
    path = tree / "astro" / "src" / "data" / "controlbun.json"
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
    """The half of the marker rule the real corpus can no longer reach.

    Every row in `registry.db` is real now, so `only_synthetic` is empty there
    and nothing on the site can be convicted of publishing a fabricated figure
    unmarked. Here it is not empty: every probe row is marked synthetic, so the
    page above is carrying figures that trace to nothing else, and taking the
    banner off it has to turn the run red. This is the end-to-end version of
    what `falsifier.verify.check_the_marker_rule_still_bites` proves on every
    run with two strings, through the real export, the real page reader and the
    real number scan.
    """
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

    The reason here is a sentence this test wrote about a probe row, which is
    why it says so: invented prose is invented the same way an invented number
    is, and `tests/probe.py` covers both.
    """
    path = tree / "astro" / "src" / "data" / "controlbun.json"
    original = path.read_text()
    payload = json.loads(original)
    claimant = payload["labels"][0]["claimants"][0]
    reason = ("Written by the test suite about a probe row. Nothing hashed a "
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
    """A row claiming bytes this checkout should hold, with no bytes there.

    Held back rather than deleted, so the copy is the same afterwards. The row
    this touches records no remote of any kind, which is what makes the absence
    a finding: a pinned row whose bytes live at somebody else's commit is
    skipped by design, and `_pinned` is the distinction.
    """
    held = tree / "tests" / "_probe" / "probe_a.safetensors"
    assert held.exists(), (
        "the probe tensor is not where the rows say it is, so holding it back "
        "would prove nothing"
    )
    moved = held.with_suffix(".held")
    held.rename(moved)
    try:
        assert run(tree) == 1, "a missing raw artifact must fail, not pass quietly"
    finally:
        moved.rename(held)


def test_claim_evidence_that_renders_unmarked(tree):
    """The third kind of authored prose, added with `schema/migrations/009`.

    A claim made on a human decision records the reasoning behind it, which is
    somebody's own words and can carry names, dates and figures the same way a
    definition and an absence reason do. It renders on the namespace's page, so
    the guard reads it off the owner index rather than off the claimants, and
    this is the proof that half of `_authored_texts` is wired to anything.

    The detail below is a sentence this test wrote about an account that does
    not exist and says so, for the reason the absence-reason case gives.
    """
    path = tree / "astro" / "src" / "data" / "controlbun.json"
    original = path.read_text()
    payload = json.loads(original)
    owner = payload["owner_index"][0]
    detail = ("Written by the test suite about an account that does not exist. "
              "Nobody decided anything and there was nothing to decide.")
    owner["claims"] = [{
        "namespace": owner["owner"],
        "provider": "test-provider-does-not-exist",
        "subject": "SYNTHETIC-SUBJECT-probe",
        "handle": None,
        "claimed_at": "2026-01-01T00:00:00Z",
        "evidence": [{"kind": "human-decision", "detail": detail,
                      "recorded_at": "2026-01-01T00:00:00Z"}],
        "memberships": [],
        "is_synthetic": True,
    }]
    path.write_text(json.dumps(payload))

    page = tree / "astro" / "dist" / "probe" / "index.html"
    was = page.read_text()
    try:
        page.write_text(was.replace("</p>", f"</p><p>{detail}</p>"))
        assert run(tree) == 1, (
            "claim evidence rendered with no `data-authored` on it passed, so "
            "the marking guard never learned about the third kind of prose"
        )
        filler = " ".join(["The registry never designates and a consumer pins."] * 8)
        page.write_text(was.replace(
            "</p>", f"</p><p>{filler}</p><p data-authored>{detail}</p>"))
        assert run(tree) == 0, (
            "the same detail inside a marked region failed, so the guard is "
            "refusing the prose rather than checking where it sits"
        )
    finally:
        page.write_text(was)
        path.write_text(original)
