"""Reintroduce the defects the synthetic-marker check exists to catch.

A check that passes on a healthy tree proves nothing about what it would catch.
Each case below reintroduces one defect, runs the check, and asserts it is
named, and every mutation is asserted to have landed before the result is
believed. That guard is not decoration: three bite tests in this repo have
passed while changing nothing, and a bite that mutates nothing is
indistinguishable from a check that works.

**The two halves of the rule now live in two different corpora, and that is the
point of this file.** The marker has to describe the page in both directions:

  * A page showing a figure that traces only to a synthetic row must carry the
    marker.
  * A page showing no such figure must not carry it.

Until 2026-09-19 both halves were reachable on the built site, because half the
corpus was fabricated. That half is gone. The second half is still reachable
there and is exercised against the real build below. The first half is not
reachable there at all any more, and that is exactly the condition under which a
check goes quietly inert, so it is exercised two ways instead: end to end against
`tests/probe.py`, which is a corpus of fabricated rows that reaches no page, and
through `falsifier.verify.check_the_marker_rule_still_bites`, which runs the rule
against two strings on every falsifier run so that the rule cannot stop biting
without the gate saying so.

The last of those needs a bite of its own, or it is one more reassuring line.
Breaking `marker_findings` and asserting the probe notices is the test that
keeps the proof honest.
"""

from __future__ import annotations

import importlib.util
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "astro" / "dist"
EXPORT = ROOT / "astro" / "src" / "data" / "controlbun.json"


# Handed to a loaded falsifier whose `DIST` and `EXPORT` it will never read,
# because the function under test in that case touches neither. Named so a
# reader does not go looking for the directory.
NOWHERE = Path("/nonexistent")


def _load_falsifier(*, root: Path, dist: Path, export: Path):
    """A fresh copy of the falsifier, pointed wherever the caller wants.

    Loaded per call rather than imported once, because `failures` is a module
    global and a run that inherited the previous one's findings would report
    somebody else's defect as its own.
    """
    spec = importlib.util.spec_from_file_location(
        "marker_probed_falsifier", ROOT / "falsifier" / "verify.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.ROOT = root
    module.DB = root / "registry.db"
    module.EXPORT = export
    module.DIST = dist
    module.failures = []
    return module


def falsifier() -> str:
    """The real gate, run as the build runs it."""
    result = subprocess.run(
        [sys.executable, str(ROOT / "falsifier" / "verify.py")],
        capture_output=True, text=True,
    )
    return result.stdout + result.stderr


# --------------------------------------------------------------------------- #
# The tree is clean before anything below is believed.


def test_the_built_site_is_clean_first():
    """If the tree is already red, no result below means anything."""
    if not DIST.exists() or not EXPORT.exists():
        pytest.skip("site not built; run `make site`")
    assert "re-derives or traces to its source" in falsifier()


# --------------------------------------------------------------------------- #
# Half one: a fabricated figure published with no marker.
#
# Not reachable on the real site any more, because no row in the corpus is
# marked synthetic. Exercised end to end against a corpus where every row is.


@pytest.fixture(scope="module")
def probe_tree(tmp_path_factory):
    """A copy carrying the probe corpus, its export, and a place for pages.

    `tests/probe.py` is run from this repository and pointed at the copy with
    `--root`, so the tensors land under `dest/tests/_probe/` and the rows
    record the path that resolves to them there. Nothing in the working tree is
    read or written by anything below.
    """
    dest = tmp_path_factory.mktemp("markerprobe") / "repo"
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
    return dest


def _probe_payload(tree: Path) -> dict:
    return json.loads(
        (tree / "astro" / "src" / "data" / "controlbun.json").read_text()
    )


def _a_figure_only_a_probe_row_publishes(payload: dict) -> str:
    """One number the export attributes to a synthetic row and to nothing else.

    Taken off the export through the falsifier's own `_numbers_under` rather
    than typed here, so every figure in this file came out of `tests/probe.py`
    and none of it was invented at the point of use. A value that also appears
    under a real claimant is attributed to neither by the rule, which is the
    conservative reading, so the one picked has to be uniquely traceable or the
    bite is vacuous.
    """
    module = _load_falsifier(root=ROOT, dist=NOWHERE, export=NOWHERE)
    synthetic: set[str] = set()
    real: set[str] = set()
    for entry in payload["labels"]:
        for claimant in entry["claimants"]:
            module._numbers_under(
                claimant, synthetic if claimant["is_synthetic"] else real)
    only_synthetic = sorted(synthetic - real)
    assert only_synthetic, (
        "no figure in the probe export traces only to a synthetic row, so the "
        "check under test cannot convict a page and this file is inert"
    )
    return only_synthetic[0]


def _write_page(tree: Path, where: str, body: str) -> Path:
    page = tree / "astro" / "dist" / where
    page.mkdir(parents=True, exist_ok=True)
    out = page / "index.html"
    out.write_text(f"<html><body><p>{body}</p></body></html>")
    return out


def test_a_fabricated_page_without_its_marker_fails(probe_tree):
    payload = _probe_payload(probe_tree)
    figure = _a_figure_only_a_probe_row_publishes(payload)

    page = _write_page(probe_tree, "unmarked", f"Published figure {figure}")
    try:
        assert "Synthetic corpus" not in page.read_text(), (
            "the page under test carries the marker, so this proves nothing"
        )
        module = _load_falsifier(
            root=probe_tree,
            dist=probe_tree / "astro" / "dist",
            export=probe_tree / "astro" / "src" / "data" / "controlbun.json",
        )
        module.check_synthetic_marker_matches_the_page(payload)
        assert any("with no marker on the page" in line
                   for line in module.failures), (
            f"a fabricated figure published unmarked went unreported: "
            f"{module.failures}"
        )
        assert any(figure in line for line in module.failures), (
            "the failure does not name the figure, so a reader cannot find it"
        )
    finally:
        page.unlink()


def test_the_same_page_with_its_marker_passes(probe_tree):
    """The positive control the bite above needs.

    Without this, a check that failed every page whatever it said would pass
    the test above and nobody would know the marker was doing any work.
    """
    payload = _probe_payload(probe_tree)
    figure = _a_figure_only_a_probe_row_publishes(payload)

    page = _write_page(probe_tree, "marked",
                       f"Synthetic corpus. Published figure {figure}")
    try:
        module = _load_falsifier(
            root=probe_tree,
            dist=probe_tree / "astro" / "dist",
            export=probe_tree / "astro" / "src" / "data" / "controlbun.json",
        )
        module.check_synthetic_marker_matches_the_page(payload)
        assert module.failures == [], (
            f"a fabricated figure published with its marker was reported: "
            f"{module.failures}"
        )
    finally:
        page.unlink()


# --------------------------------------------------------------------------- #
# Half two: a real figure published under a marker calling it invented.
#
# Reachable on the real site, and exercised there. A marker that is sometimes
# false is not a marker, and this is the half that arrived the day the corpus
# stopped being entirely fabricated.


@pytest.fixture
def dist_copy(tmp_path):
    """The built site, copied, so a mutation cannot reach the working tree.

    This used to mutate `astro/dist` in place and put the file back. Copying is
    the same bite with none of the exposure: a failure between the write and the
    restore used to leave a doctored page on disk for whatever ran next.
    """
    if not DIST.exists():
        pytest.skip("site not built; run `make site`")
    dest = tmp_path / "dist"
    shutil.copytree(DIST, dest, ignore=shutil.ignore_patterns("pagefind"))
    return dest


def _a_page_showing_a_real_figure(module, payload: dict) -> Path:
    """A built page carrying a figure that traces only to a real claimant.

    Discovered rather than named, because naming a route makes this test go
    green the day that route stops existing and the reader has to work out
    whether it was deleted or renamed. What the rule needs is a page with a
    real-only figure on it, so that is what this looks for, and the absence of
    one is asserted rather than skipped: it would mean the built site publishes
    no figure attributable to anybody, which is a finding in itself.
    """
    synthetic: set[str] = set()
    real: set[str] = set()
    for entry in payload["labels"]:
        for claimant in entry["claimants"]:
            module._numbers_under(
                claimant, synthetic if claimant["is_synthetic"] else real)
    only_real = real - synthetic

    for where, shown, _marked in module._pages_as_read():
        if shown & only_real:
            return module.DIST / where.strip("/") / "index.html"
    raise AssertionError(
        "no built page shows a figure traceable only to a real claimant, so "
        "the half of the rule this test exercises cannot convict anything"
    )


def test_a_real_page_carrying_the_marker_fails(dist_copy):
    if not EXPORT.exists():
        pytest.skip("no export; run `make site`")
    payload = json.loads(EXPORT.read_text())

    module = _load_falsifier(root=ROOT, dist=dist_copy, export=EXPORT)
    page = _a_page_showing_a_real_figure(module, payload)
    original = page.read_text()
    mutated = original.replace("<main>", "<main><p>Synthetic corpus.</p>", 1)
    assert mutated != original, (
        "the mutation changed nothing, so this test would pass whatever the "
        "check does"
    )
    page.write_text(mutated)

    checker = _load_falsifier(root=ROOT, dist=dist_copy, export=EXPORT)
    checker.check_synthetic_marker_matches_the_page(payload)
    assert any(
        "carries the synthetic marker but every figure on it traces to a real"
        in line for line in checker.failures
    ), f"a real page under a fabrication notice went unreported: {checker.failures}"


def test_the_real_site_carries_no_marker_today(dist_copy):
    """The state, asserted rather than assumed.

    Nothing in the corpus is marked synthetic since 2026-09-19, so no page
    should carry the marker and the check should find nothing. If a page starts
    carrying it, either a synthetic row arrived and this is stale, or a banner
    is rendering on a page it does not describe.
    """
    if not EXPORT.exists():
        pytest.skip("no export; run `make site`")
    payload = json.loads(EXPORT.read_text())

    module = _load_falsifier(root=ROOT, dist=dist_copy, export=EXPORT)
    module.check_synthetic_marker_matches_the_page(payload)
    assert module.failures == [], (
        f"the built site does not satisfy the marker rule: {module.failures}"
    )

    marked = [where for where, _shown, is_marked in module._pages_as_read()
              if is_marked]
    if payload.get("any_synthetic"):
        assert marked, (
            "the corpus holds a synthetic row and no page says so anywhere"
        )
    else:
        assert not marked, (
            "no row in the corpus is synthetic and these pages carry the "
            f"marker anyway: {marked}"
        )


# --------------------------------------------------------------------------- #
# The proof itself. `check_the_marker_rule_still_bites` is what stands in for
# the corpus now that the corpus cannot exercise half the rule, so it needs the
# same treatment everything else here gets: break it and see that it is named.


def test_the_marker_rule_is_proved_on_every_run():
    """The positive control: the shipped rule catches both probe pages."""
    module = _load_falsifier(root=ROOT, dist=NOWHERE, export=NOWHERE)
    module.check_the_marker_rule_still_bites()
    assert module.failures == [], (
        f"the shipped rule failed its own probe: {module.failures}"
    )


def test_a_rule_that_stopped_biting_altogether_is_caught():
    """The check that keeps the proof from being a reassuring line.

    A `marker_findings` that returns nothing is what "the check went inert"
    looks like from the outside: every page passes, the gate is green, and
    nothing in the corpus can tell you otherwise because no row is fabricated.
    """
    module = _load_falsifier(root=ROOT, dist=NOWHERE, export=NOWHERE)
    module.marker_findings = lambda pages, only_synthetic, only_real: []
    module.check_the_marker_rule_still_bites()
    assert module.failures, "a rule that catches nothing passed its own probe"
    named = " ".join(module.failures)
    assert "fabricated-and-unmarked" in named and "real-and-marked" in named, (
        f"the failure does not name which half stopped biting: {module.failures}"
    )


def test_a_rule_that_only_catches_one_half_is_caught():
    """The realistic regression, which is worse than the total one.

    Half a rule is the shape this check was in before 2026-09-14: it asked
    whether a fabricated page was marked and never whether a real one was
    marked wrongly. A rule that answers one of its two questions passes every
    test written against the other, so the probe has to require both.
    """
    module = _load_falsifier(root=ROOT, dist=NOWHERE, export=NOWHERE)
    shipped = module.marker_findings
    module.marker_findings = (
        lambda pages, only_synthetic, only_real:
        shipped(pages, only_synthetic, set())
    )
    module.check_the_marker_rule_still_bites()
    assert module.failures, (
        "a rule that only catches the unmarked half passed its own probe"
    )
    named = " ".join(module.failures)
    assert "real-and-marked" in named, (
        f"the half that stopped biting is not the one named: {module.failures}"
    )
    assert "fabricated-and-unmarked" not in named, (
        "the half that still works was reported as broken, so the probe is not "
        f"distinguishing them: {module.failures}"
    )


def test_the_falsifiers_own_probe_reaches_no_page_and_no_export():
    """The probe is a probe, and stays one.

    `check_the_marker_rule_still_bites` uses two number-shaped strings. They are
    not measurements and they exist so the rule has something to catch, which
    holds only while they never leave the function. A probe value that turned up
    in the export or on a page would be a fabricated figure published by the
    thing whose job is to stop that.
    """
    if not DIST.exists() or not EXPORT.exists():
        pytest.skip("site not built; run `make site`")

    source = (ROOT / "falsifier" / "verify.py").read_text()
    body = source.split("def check_the_marker_rule_still_bites")[1]
    body = body.split("\ndef ")[0]
    strings = set(re.findall(r'"(\d\.\d{4})"', body))
    assert strings, (
        "no probe values found in check_the_marker_rule_still_bites, so this "
        "test is looking for the wrong thing"
    )

    export = EXPORT.read_text()
    for value in sorted(strings):
        assert value not in export, (
            f"{value} is a falsifier probe value and it is in the export"
        )
    for page in DIST.rglob("index.html"):
        text = page.read_text()
        for value in sorted(strings):
            assert value not in text, (
                f"{value} is a falsifier probe value and it renders on "
                f"/{page.relative_to(DIST).parent}/"
            )
