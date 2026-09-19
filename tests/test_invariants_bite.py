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
    # `registry.ingest` has a dict of converters, which is one rename away from
    # being a list of the formats an author is allowed to publish in. The
    # refusal it writes today says nothing can read these bytes and where a
    # converter goes. This is the sentence it must not start saying instead.
    "refusing a format for not being on the list": (
        "src/registry/probe.py",
        "def read(blob):\n    raise ValueError('unsupported format')\n",
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
    "ordering on whether an artifact is published, in SQL": (
        "astro/src/probe.ts",
        'const q = "SELECT * FROM intervention ORDER BY artifact_repo IS NULL";\n',
        "test_no_ordering_is_derived_from_whether_an_artifact_is_published",
    ),
    "ordering on whether an artifact is published, in JS": (
        "astro/src/probe.ts",
        "rows.sort((a, b) => Number(!!b.published) - Number(!!a.published));\n",
        "test_no_ordering_is_derived_from_whether_an_artifact_is_published",
    ),
    "ordering on whether an artifact is published, in Python": (
        "src/registry/probe.py",
        "rows = sorted(rows, key=lambda r: r['artifact_url'] is None)\n",
        "test_no_ordering_is_derived_from_whether_an_artifact_is_published",
    ),
    # The exemption in that scan is for a `SELECT DISTINCT` of the same column,
    # which is a value vocabulary rather than a row order. This proves the
    # exemption does not cover a row set: same column, same ORDER BY, no
    # DISTINCT, and it has to go red.
    "ordering rows by host under cover of the vocabulary exemption": (
        "artifacts/probe.py",
        'q = ("SELECT author, label FROM intervention"\n'
        '     " ORDER BY artifact_host")\n',
        "test_no_ordering_is_derived_from_whether_an_artifact_is_published",
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

    # The directory that carried the only code writing real rows and that no
    # invariant read for a day. These probe it specifically: a scanner that bites
    # in `src/` and not here is the bug, not the fix.
    "ordering on an eval result where real rows are written": (
        "artifacts/probe.py",
        'rows = ex("SELECT * FROM submission ORDER BY necessity_score DESC")\n',
        "test_no_ordering_is_derived_from_an_eval_result",
    ),
    "closed enum where real rows are written": (
        "artifacts/probe.py",
        "PERMITTED_KINDS = ['direction', 'probe']\n",
        "test_no_check_constraint_enumerates_strings",
    ),
    "absent eval coerced to zero in the falsifier": (
        "falsifier/probe.py",
        "value = row.transfer_score or 0\n",
        "test_absent_eval_is_not_an_error",
    ),
    "label resolved to one artifact in the fixture builder": (
        "fixtures/probe.py",
        "def only(conn, label):\n    return _submissions(conn, label)[0]\n",
        "test_nothing_resolves_a_label_to_one_artifact",
    ),

    # Namespace claims. Every one of these is a step somebody would take for a
    # good local reason, which is why each has to go red rather than be
    # remembered. The spellings are ones the tree does not use, so a scanner
    # that only catches today's wording is caught here rather than in a year.
    "ordering namespaces by claim status in SQL": (
        "src/registry/probe.py",
        'q = "SELECT * FROM owner ORDER BY is_claimed DESC"\n',
        "test_no_ordering_is_derived_from_a_namespace_claim",
    ),
    "ordering namespaces by claim status in JS": (
        "astro/src/probe.ts",
        "rows.sort((a, b) => b.claims.length - a.claims.length);\n",
        "test_no_ordering_is_derived_from_a_namespace_claim",
    ),
    "ordering namespaces by when they were claimed": (
        "src/registry/probe.py",
        "ranked = sorted(owners, key=lambda o: o.claimed_at)\n",
        "test_no_ordering_is_derived_from_a_namespace_claim",
    ),
    "a claim column made a sort control": (
        "astro/src/probe.astro",
        '<th><button data-col="2">Claimed</button></th>\n',
        "test_no_ordering_is_derived_from_a_namespace_claim",
    ),
    "filtering a list down to the claimed ones": (
        "astro/src/probe.ts",
        "const shown = owners.filter((o) => o.claimed);\n",
        "test_no_ordering_is_derived_from_a_namespace_claim",
    ),
    # The schema half. Each lands as an extra migration beside the real one
    # rather than replacing it, which is why the checks they probe read every
    # declaration in the tree and not the first one they find: a second table
    # with the same name is exactly how a convenient version arrives.
    "a claim bound to the handle instead of the subject": (
        "schema/migrations/910_probe.sql",
        "CREATE TABLE namespace_claim (\n    namespace TEXT NOT NULL,\n"
        "    subject TEXT,\n    handle TEXT NOT NULL,\n"
        "    UNIQUE (namespace, handle)\n);\n",
        "test_a_claim_is_bound_to_a_subject_and_never_to_a_handle",
    ),
    "a claim looked up by handle": (
        "src/registry/probe.py",
        'row = ex("SELECT * FROM namespace_claim WHERE handle = ?", (name,))\n',
        "test_a_claim_is_bound_to_a_subject_and_never_to_a_handle",
    ),
    "membership cached as a standing fact": (
        "schema/migrations/910_probe.sql",
        "CREATE TABLE account (\n    subject TEXT NOT NULL,\n"
        "    is_member INTEGER NOT NULL\n);\n",
        "test_org_membership_is_an_observation_and_never_a_stored_fact",
    ),
    "an observation overwritten instead of appended": (
        "src/registry/probe.py",
        'ex("UPDATE namespace_membership_observation SET org = ?", (org,))\n',
        "test_org_membership_is_an_observation_and_never_a_stored_fact",
    ),
    "a namespace constrained to one claimant": (
        "schema/migrations/910_probe.sql",
        "CREATE TABLE probe (\n    namespace TEXT,\n    UNIQUE (namespace)\n);\n",
        "test_a_namespace_permits_more_than_one_claimant",
    ),
    "publishing made conditional on a claim": (
        "schema/migrations/910_probe.sql",
        "CREATE TABLE submission (\n    author TEXT NOT NULL,\n"
        "    claim_id TEXT NOT NULL REFERENCES namespace_claim (id)\n);\n",
        "test_publishing_never_requires_a_claim",
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
    # Nothing else to rebase. This used to restate the directory list, which meant
    # widening the real scan would have left every probe below aimed at the old
    # one: the bite tests would have kept passing while testing a scanner the
    # repository no longer used. Discovery reads from ROOT, so moving ROOT is the
    # whole rebase.
    return module


@pytest.fixture(scope="module")
def tree(tmp_path_factory):
    dest = tmp_path_factory.mktemp("probe") / "repo"
    dest.mkdir()
    for part in ("schema", "src", "tests", "fixtures", "artifacts", "falsifier"):
        shutil.copytree(ROOT / part, dest / part,
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
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
