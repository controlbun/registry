"""Proof that the invariant tests actually fail when violated.

A green suite is only worth something if red is reachable. Twice now an invariant
here has been silently inert: `\\bbest\\b` never matched `best_submission`, and the
cosine scan kept looking for `cosine_sim` after the field was renamed to
`angle_similarity`, so it went blind to a live violation while staying green.

Both were found by a human noticing, which does not scale and did not work. So
each scanner is checked here the only way that means anything: copy the tree,
inject a violation, and assert the test goes red. If a scanner stops biting, this
file fails and says which one.

The injected snippets deliberately use spellings the codebase does *not* currently
use. A scanner that only catches today's spelling is one rename away from inert.
"""

from __future__ import annotations

import importlib.util
import shutil
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

# name -> (relative path to write, file contents, test function to run)
VIOLATIONS = {
    "eval result made NOT NULL": (
        "schema/migrations/900_probe.sql",
        "CREATE TABLE probe (\n    trait_score REAL NOT NULL,   -- eval-result\n);\n",
        "test_no_eval_result_is_not_null",
    ),
    "closed enum in SQL": (
        "schema/migrations/900_probe.sql",
        "CREATE TABLE probe (\n    kind TEXT CHECK (kind IN ('diffmean','caa'))\n);\n",
        "test_no_check_constraint_enumerates_strings",
    ),
    "closed enum in application code": (
        "astro/src/probe.ts",
        "const ALLOWED_KINDS = ['direction'];\n",
        "test_no_check_constraint_enumerates_strings",
    ),
    "rejecting an unrecognized kind": (
        "astro/src/probe.ts",
        "if (!kinds.includes(kind)) throw new Error('bad');\n",
        "test_no_check_constraint_enumerates_strings",
    ),
    "label unique on its own": (
        "schema/migrations/900_probe.sql",
        "CREATE TABLE probe (\n    label TEXT,\n    UNIQUE (label)\n);\n",
        "test_label_is_never_unique_on_its_own",
    ),
    "resolving a label by name": (
        "astro/src/probe.ts",
        "export function canonicalFor(label) { return label; }\n",
        "test_nothing_resolves_a_label_to_one_artifact",
    ),
    "resolving a label by indexing": (
        "src/registry/probe.py",
        "def only(conn, label):\n    return _submissions(conn, label)[0]\n",
        "test_nothing_resolves_a_label_to_one_artifact",
    ),
    "ordering on an eval result in SQL": (
        "astro/src/probe.ts",
        'const q = "SELECT * FROM submission ORDER BY trait_score DESC";\n',
        "test_no_ordering_is_derived_from_an_eval_result",
    ),
    "ordering on an eval result in JS": (
        "astro/src/probe.ts",
        "rows.sort((a, b) => b.coherence_score - a.coherence_score);\n",
        "test_no_ordering_is_derived_from_an_eval_result",
    ),
    "absent eval coerced to zero": (
        "src/registry/probe.py",
        "value = report.trait_score or 0\n",
        "test_absent_eval_is_not_an_error",
    ),
    "trait rendered with no coherence": (
        "astro/src/probe.astro",
        "<span>{row.trait.toFixed(4)}</span>\n",
        "test_trait_score_never_renders_without_coherence",
    ),
    "similarity made a sort control": (
        "astro/src/probe.astro",
        '<th><button data-col="1">Angle similarity</button></th>\n',
        "test_cosine_is_never_evidence_of_disagreement",
    ),
    "similarity read as disagreement": (
        "src/registry/probe.py",
        "disagreement = angle_similarity(a, b)\n",
        "test_cosine_is_never_evidence_of_disagreement",
    ),
}


def _load_invariants(root: Path):
    """Load tests/test_invariants.py rebased onto a copied tree."""
    spec = importlib.util.spec_from_file_location(
        "probed_invariants", root / "tests" / "test_invariants.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    module.ROOT = root
    module.MIGRATIONS = sorted((root / "schema" / "migrations").glob("*.sql"))
    module.SOURCE_DIRS = [root / "src", root / "astro" / "src"]
    return module


@pytest.fixture(scope="module")
def tree(tmp_path_factory):
    dest = tmp_path_factory.mktemp("probe") / "repo"
    dest.mkdir()
    for part in ("schema", "src", "tests"):
        shutil.copytree(ROOT / part, dest / part)
    (dest / "astro").mkdir()
    shutil.copytree(ROOT / "astro" / "src", dest / "astro" / "src")
    return dest


def test_the_clean_tree_passes(tree):
    """If the copy is already red, every result below is meaningless."""
    module = _load_invariants(tree)
    failed = []
    for name, fn in vars(module).items():
        if name.startswith("test_") and callable(fn):
            try:
                fn()
            except AssertionError:
                failed.append(name)
    assert not failed, f"copied tree is not clean, so nothing below proves anything: {failed}"


@pytest.mark.parametrize("label", list(VIOLATIONS))
def test_each_violation_is_caught(tree, label):
    rel, body, test_name = VIOLATIONS[label]
    target = tree / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(body)
    try:
        module = _load_invariants(tree)
        with pytest.raises(AssertionError):
            getattr(module, test_name)()
    finally:
        target.unlink()
