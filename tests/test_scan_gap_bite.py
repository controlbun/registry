"""Proof that widening the scan is what closed the gap, not a coincidence.

`tests/test_invariants_bite.py` gained four probes that write violations into
`artifacts/` and `falsifier/`. Those probes pass now. The question this file
answers is whether they pass *because* the scan was widened, or whether they
would have passed anyway, which is the failure mode that has already produced
three inert checks in this repository and, on three separate occasions, a bite test
that mutated nothing and proved nothing.

So the scanner is narrowed back to what it was before 2026-09-14, the same
violations are injected, and each one is asserted to go *unnoticed*. If a probe
still bites under the narrow scan, it was never testing the gap.
"""

from __future__ import annotations

import importlib.util
import shutil
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

# What SOURCE_DIRS held before discovery replaced it. `artifacts/` had existed for
# a day at that point, carrying the only code in the repo that writes real
# submission and intervention rows.
OLD_SCOPE = ("src", "astro/src")

# The four probes added alongside the fix, and the invariant each one should
# trip. Four invariants, so a scan that widened for one reason and stayed narrow
# for the others is caught. The fourth sat at `fixtures/probe.py` until the
# synthetic corpus was removed on 2026-09-19; it moved to `falsifier/` and the
# subject is unchanged, because what it probes is the invariant rather than the
# directory. The two directories here are the ones outside OLD_SCOPE that hold
# code: `artifacts/` writes every row in the corpus and `falsifier/` re-derives
# every number on the site.
PROBES = {
    "artifacts/probe.py":
        ('rows = ex("SELECT * FROM submission ORDER BY necessity_score DESC")\n',
         "test_no_ordering_is_derived_from_an_eval_result"),
    "artifacts/probe2.py":
        ("PERMITTED_KINDS = ['direction', 'probe']\n",
         "test_no_check_constraint_enumerates_strings"),
    "falsifier/probe.py":
        ("value = row.transfer_score or 0\n",
         "test_absent_eval_is_not_an_error"),
    "falsifier/probe2.py":
        ("def only(conn, label):\n    return _submissions(conn, label)[0]\n",
         "test_nothing_resolves_a_label_to_one_artifact"),
}


@pytest.fixture(scope="module")
def tree(tmp_path_factory):
    dest = tmp_path_factory.mktemp("scangap") / "repo"
    dest.mkdir()
    # `fixtures` was in this list and is not a directory any more.
    for part in ("schema", "src", "tests", "artifacts", "falsifier"):
        shutil.copytree(ROOT / part, dest / part,
                        ignore=shutil.ignore_patterns(
                            "__pycache__", "*.pyc", "_probe"))
    (dest / "astro").mkdir()
    shutil.copytree(ROOT / "astro" / "src", dest / "astro" / "src")
    return dest


def _invariants(root: Path, narrow: bool):
    spec = importlib.util.spec_from_file_location(
        "gap_invariants", root / "tests" / "test_invariants.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.ROOT = root
    module.MIGRATIONS = sorted((root / "schema" / "migrations").glob("*.sql"))

    if narrow:
        def source_files():
            out = []
            for d in OLD_SCOPE:
                base = root / d
                if base.exists():
                    out += [p for p in base.rglob("*")
                            if p.suffix in module.SCANNED_SUFFIXES]
            return out
        module.source_files = source_files
        module.source_dirs = lambda: sorted({p.parent for p in source_files()})
    return module


def test_the_narrowing_is_real(tree):
    """If narrowing changed nothing, every result below is meaningless."""
    wide = len(_invariants(tree, narrow=False).source_files())
    narrow = len(_invariants(tree, narrow=True).source_files())
    # Both bounds matter. Equal counts mean the narrowing did nothing and every
    # probe below passes for the wrong reason. Zero means the narrow scan reads
    # nothing at all, in which case every invariant passes vacuously and the
    # probes prove the same nothing from the other direction.
    assert 0 < narrow < wide, (
        f"narrow scan read {narrow} files against {wide} wide; this file only "
        "proves something when the narrow scan is smaller and non-empty"
    )


@pytest.mark.parametrize("rel", list(PROBES))
def test_the_old_scan_would_have_missed_it(tree, rel):
    body, invariant = PROBES[rel]
    target = tree / rel
    target.write_text(body)
    try:
        # Wide: the violation is caught. This is the fix working.
        with pytest.raises(AssertionError):
            getattr(_invariants(tree, narrow=False), invariant)()

        # Narrow: nothing. This is the gap, reproduced.
        getattr(_invariants(tree, narrow=True), invariant)()
    finally:
        target.unlink()


def test_excluding_a_directory_that_writes_rows_is_caught(tree):
    """The one way to make this inert again is to excuse the directory."""
    module = _invariants(tree, narrow=False)
    module.test_scanner_reaches_every_place_rows_and_views_are_made()

    module.NOT_SCANNED = module.NOT_SCANNED | {"artifacts"}
    with pytest.raises(AssertionError, match="artifacts"):
        module.test_scanner_reaches_every_place_rows_and_views_are_made()


def test_a_view_in_an_unlisted_file_type_is_caught(tree):
    """Discovery keys on suffix, so a new file type is the remaining hole."""
    module = _invariants(tree, narrow=False)
    module.test_no_code_file_type_escapes_the_scanner()

    stray = tree / "astro" / "src" / "probe.svelte"
    stray.write_text("<script>const best = rows[0];</script>\n")
    try:
        with pytest.raises(AssertionError, match=r"\.svelte"):
            module.test_no_code_file_type_escapes_the_scanner()
    finally:
        stray.unlink()
