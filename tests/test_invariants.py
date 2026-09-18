"""Executable invariants.

Prose principles get pattern-matched away; checkable ones do not. Each test here
corresponds to a line in the invariants list in CLAUDE.md. If you settle a new
invariant, add it there and add a test here. An invariant that is only in prose is
not an invariant.

Some of these read the SQL. The rest scan source and templates for
banned constructs; they currently scan a small codebase and will bite as it grows.
That is the intended shape, not a gap: they are lint, and lint is worth having
before the code it lints exists.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MIGRATIONS = sorted((ROOT / "schema" / "migrations").glob("*.sql"))
# Code is discovered, not listed. This used to be a list of two directories, and
# the list is what failed: `artifacts/` was added on 2026-09-14 carrying the only
# code in the repo that writes real submission and intervention rows, and no
# invariant looked at it for a day. The guard beside it could not notice, because
# it only asked whether each *listed* directory was readable and had no way to ask
# whether every code directory was listed.
#
# So the default is inverted. Anything holding a scanned suffix is scanned unless
# it is named below with a reason. A new directory is covered the moment it
# exists, and the failure mode of getting this wrong is a false positive, which is
# loud, rather than an inert scanner, which is silent and has now bitten three
# times.
NOT_SCANNED = {
    # Tests write the forbidden spellings on purpose, to prove the scanners bite.
    "tests",
    # Not authored here: dependencies, build output, caches, local tooling.
    ".venv", "node_modules", "dist", ".astro", ".git", ".claude", ".cache",
    "__pycache__", ".pytest_cache", ".ruff_cache", "_local",
    # Notarized manifests and brand assets. No code, and `_attest` is append-only.
    "_attest", "brand",
}

SCANNED_SUFFIXES = {
    ".py", ".sql",                      # backend
    # .html stays scanned though the Jinja frontend is retired: Astro emits and
    # accepts plain HTML, and a view smuggled back in as a raw .html file would
    # otherwise be invisible to all of this.
    ".html",
    ".astro", ".ts", ".tsx", ".js", ".jsx", ".mjs",   # astro view layer
}

# --------------------------------------------------------------------------- #
# helpers


def sql_text() -> str:
    assert MIGRATIONS, "no migrations found; the schema is the thing under test"
    return "\n".join(p.read_text() for p in MIGRATIONS)


def strip_sql_comments(sql: str) -> str:
    """Comments document common values on purpose. Only real DDL is under test."""
    return "\n".join(line.split("--")[0] for line in sql.splitlines())


def source_dirs() -> list[Path]:
    """Every directory under ROOT holding a scanned file, minus NOT_SCANNED."""
    found = {p.parent for p in source_files()}
    return sorted(found)


def source_files() -> list[Path]:
    out: list[Path] = []
    for p in ROOT.rglob("*"):
        if p.suffix not in SCANNED_SUFFIXES or not p.is_file():
            continue
        if NOT_SCANNED & set(p.relative_to(ROOT).parts):
            continue
        out.append(p)
    return out


def scan(pattern: str) -> list[str]:
    """Return 'path:line: text' for every source line matching pattern."""
    rx = re.compile(pattern, re.I)
    hits = []
    for p in source_files():
        for n, line in enumerate(p.read_text().splitlines(), 1):
            if line.lstrip().startswith("#") or line.lstrip().startswith("//"):
                continue
            if rx.search(line):
                hits.append(f"{p.relative_to(ROOT)}:{n}: {line.strip()}")
    return hits


# --------------------------------------------------------------------------- #
# 0. The scanner actually reaches the code it claims to check.


# The directories that must be reached, named so the scan cannot quietly stop
# reaching one. This is the opposite of the old SOURCE_DIRS list: that one decided
# what got scanned, so forgetting an entry made a scanner inert. This one only
# asserts, so forgetting an entry costs an assertion and never coverage.
MUST_REACH = {
    "src/registry":  "the library",
    "astro/src":     "the view layer, where a default sort would appear",
    "fixtures":      "writes the synthetic corpus",
    "artifacts":     "writes the real corpus",
    "falsifier":     "re-derives every published number",
}


def test_scanner_reaches_every_place_rows_and_views_are_made():
    """Silence from a scan means nothing unless the scan looked.

    Three times now a scanner here has been green while checking nothing:
    `\\bbest\\b` never matched `best_submission`, the cosine scan kept looking for
    `cosine_sim` after the field became `angle_similarity`, and `artifacts/` was
    added carrying the only code that writes real rows while `SOURCE_DIRS` still
    named two directories.
    """
    reached = {str(d.relative_to(ROOT)) for d in source_dirs()}
    missing = {
        name: why for name, why in MUST_REACH.items()
        if (ROOT / name).exists()
        and not any(r == name or r.startswith(name + "/") for r in reached)
    }
    assert not missing, (
        "the scanner does not reach code it has to read:\n  "
        + "\n  ".join(f"{k}: {v}" for k, v in sorted(missing.items()))
    )


# Suffixes that mean somebody wrote code, deliberately wider than
# SCANNED_SUFFIXES. The delta between the two sets is the blind spot, and the test
# below asserts it is empty. Discovery keys on suffix, so a directory holding a
# file type nobody added here is found by neither the scan nor the guard above:
# that is the one hole inverting the default did not close, and it is the exact
# hole named when the view layer moved to Astro.
CODE_SUFFIXES = SCANNED_SUFFIXES | {
    ".cjs", ".mts", ".cts",                          # other JS module flavors
    ".svelte", ".vue",                               # other component formats
    ".jinja", ".jinja2", ".j2", ".hbs", ".ejs",      # template languages
    ".erb", ".twig", ".liquid", ".njk",
    ".rs", ".go", ".rb", ".php", ".java", ".kt",     # other backends
}


def test_no_code_file_type_escapes_the_scanner():
    """Adding a view in a file type nobody listed makes the scanners inert.

    Not hypothetical. The Jinja frontend was retired for Astro, and if `.astro`
    had not been added to the scanned set at the same time, four invariants would
    have gone quiet on the one layer where a default sort or a bare trait score
    appears. The suite would have stayed green.
    """
    outside = sorted({
        p.suffix for p in ROOT.rglob("*")
        if p.is_file() and p.suffix in CODE_SUFFIXES
        and not (NOT_SCANNED & set(p.relative_to(ROOT).parts))
    } - SCANNED_SUFFIXES)
    assert not outside, (
        "source files exist in types the scanner ignores, so every invariant "
        f"below is blind to them: {outside}"
    )


def test_view_layer_suffixes_are_covered():
    """If an Astro app is present, its file types must be in the scanned set."""
    astro = ROOT / "astro" / "src"
    if not astro.exists():
        return
    present = {p.suffix for p in astro.rglob("*") if p.suffix}
    renderable = {s for s in present if s in {".astro", ".ts", ".tsx", ".js",
                                              ".jsx", ".mjs", ".html", ".svelte",
                                              ".vue"}}
    missed = renderable - SCANNED_SUFFIXES
    assert not missed, (
        f"the astro app contains file types the scanner ignores: {sorted(missed)}"
    )


# --------------------------------------------------------------------------- #
# 1. No schema field is both an eval result and NOT NULL.


def test_no_eval_result_is_not_null():
    offenders = [
        f"{p.name}:{n}: {line.strip()}"
        for p in MIGRATIONS
        for n, line in enumerate(p.read_text().splitlines(), 1)
        if "-- eval-result" in line and re.search(r"\bNOT\s+NULL\b", line, re.I)
    ]
    assert not offenders, (
        "An eval result that cannot be absent forces authors to invent one. "
        "Absence is a state, not an error:\n" + "\n".join(offenders)
    )


def test_eval_results_are_actually_marked():
    """Guards the marker convention the test above depends on."""
    ddl = sql_text()
    for column in ("trait_score", "coherence_score", "cosine_to_original"):
        line = next((l for l in ddl.splitlines() if re.search(rf"^\s*{column}\b", l)), None)
        assert line is not None, f"{column} missing from schema"
        assert "-- eval-result" in line, f"{column} is a measurement and must carry the marker"


# --------------------------------------------------------------------------- #
# 7. No closed enum on any user-supplied field.


def test_no_check_constraint_enumerates_strings():
    ddl = strip_sql_comments(sql_text())
    offenders = []
    for n, line in enumerate(ddl.splitlines(), 1):
        if re.search(r"\bCHECK\b", line, re.I) and re.search(r"'[^']*'", line):
            offenders.append(f"line {n}: {line.strip()}")
        if re.search(r"\bIN\s*\(\s*'", line, re.I):
            offenders.append(f"line {n}: {line.strip()}")
        if re.search(r"\bAS\s+ENUM\b", line, re.I):
            offenders.append(f"line {n}: {line.strip()}")
    # A closed enum in application code rejects exactly as hard as a CHECK does.
    offenders += scan(r"\b(ALLOWED|PERMITTED|VALID|SUPPORTED)_\w+\s*=")
    offenders += scan(r"\.includes\([^)]*\)\s*\)?\s*(\|\||\?|:)?\s*(throw|raise)")
    # `format` joined this list when `registry.ingest` arrived, because a file
    # format is the same kind of thing `kind` is: nobody here decides which ways
    # of packing a tensor are legitimate. What ingest may decide is which bytes
    # it can read without executing them, and a refusal that says so reads
    # nothing like one that says the format is not on the list. Tightened rather
    # than relaxed: no line in the tree matched this when the word was added.
    offenders += scan(r"(throw|raise)[^\n]*\b(unknown|unsupported|invalid)\s+(kind|hook|profile|method|format)")
    assert not offenders, (
        "A closed enumeration declares which ways of doing the thing are legitimate, "
        "and whoever invents the next one has nowhere to put it. Document common "
        "values; enforce none:\n" + "\n".join(offenders)
    )


# --------------------------------------------------------------------------- #
# 5. Any label namespace permits an unlimited number of claimants.


def test_label_is_never_unique_on_its_own():
    ddl = strip_sql_comments(sql_text())
    offenders = []
    for kind in ("PRIMARY KEY", "UNIQUE"):
        for m in re.finditer(rf"{kind}\s*\(([^)]*)\)", ddl, re.I):
            cols = [c.strip().strip('"') for c in m.group(1).split(",")]
            if "label" in cols and not ("author" in cols and "version" in cols):
                offenders.append(f"{kind} ({m.group(1).strip()})")
    assert not offenders, (
        "Constraining a label to one claimant is designation by index. Ten people "
        "claiming kindness is the content:\n" + "\n".join(offenders)
    )


# --------------------------------------------------------------------------- #
# 3. Every pin records who pinned it, when, and what alternatives existed.


def test_pin_records_who_when_and_alternatives():
    ddl = strip_sql_comments(sql_text())
    m = re.search(r"CREATE TABLE pin\s*\((.*?)\n\);", ddl, re.S | re.I)
    assert m, "no pin table; pinning without provenance is designation"
    body = m.group(1)
    for column in ("pinned_by", "pinned_at", "alternatives_json"):
        line = next((l for l in body.splitlines() if re.search(rf"^\s*{column}\b", l)), None)
        assert line is not None, f"pin.{column} missing"
        assert re.search(r"\bNOT\s+NULL\b", line, re.I), (
            f"pin.{column} must be NOT NULL. An unattributed pin, or one that hides "
            "what it was picked over, is a designation wearing a different hat."
        )


# --------------------------------------------------------------------------- #
# 2. No endpoint returns a single best submission; a bare label never resolves
#    to one artifact.


def test_nothing_resolves_a_label_to_one_artifact():
    # Two things this has to get right at once.
    #
    # No trailing \b: `_` is a word character, so \bbest\b misses best_submission,
    # which left this invariant inert once already.
    #
    # But templates now carry prose explaining the premise, and that prose has to
    # be able to say the registry "does not pick a winner". So a match only counts
    # when the word is being used as an identifier: continuing into a longer name
    # and then hitting a call, an assignment, a member access or an index. English
    # is followed by a space or punctuation and does not match.
    # A dot only counts when a word follows it, so member access matches and a
    # sentence ending in "the best." does not.
    offenders = scan(r"\b(best|winner|canonical|official|top_submission|"
                     r"resolve_label|pick_submission)[\w$]*(?:\s*[(=\[]|\.\w)")
    # Indexing a claimant list down to one is the same failure under any name.
    offenders += scan(r"(claimants|submissions|_submissions\([^)]*\))\s*\[0\]")
    offenders += scan(r"def \w+\([^)]*\blabel\b[^)]*\):[^\n]*\[0\]")
    assert not offenders, (
        "A bare label is a view across claimants, computed on demand, owned by "
        "nobody. Nothing may answer 'give me kindness' with one artifact:\n"
        + "\n".join(offenders)
    )


# --------------------------------------------------------------------------- #
# 4. A default ordering is allowed, but no ordering derives from an eval result.


EVAL_RESULT_COLUMNS = (
    "trait_score", "coherence_score", "transfer_score", "necessity_score",
)


def test_no_ordering_is_derived_from_an_eval_result():
    offenders = []
    for col in EVAL_RESULT_COLUMNS:
        offenders += scan(rf"ORDER\s+BY[^;]*\b{col}\b")
        offenders += scan(rf"sorted\s*\([^)]*\b{col}\b")
        offenders += scan(rf"key\s*=\s*[^,)]*\b{col}\b")
        offenders += scan(rf"\b(sort|rank|order)\w*\s*[=(][^)]*\b{col}\b")
        # A JS comparator: .sort((a, b) => b.trait_score - a.trait_score). The
        # pattern above stops at the first ")", which lands inside the arrow
        # function's parameters, so the column never gets seen.
        offenders += scan(rf"\.sort\([^;]*\b{col}\b")
    assert not offenders, (
        "A direction that also moves sentiment and verbosity feels more effective "
        "in use, because more is happening. Ordering on measured effect favors the "
        "confounded submission and placement compounds it:\n" + "\n".join(offenders)
    )


# --------------------------------------------------------------------------- #
# 6. Absence of an eval renders as its own state, not as an error.


def test_absent_eval_is_not_an_error():
    offenders = scan(r"raise\s+\w*(NotFound|Missing|ValueError).*(eval|score|coherence)")
    offenders += scan(r"(eval|score)\w*\s+or\s+0\b")
    assert not offenders, (
        "A submission that did not measure something says so. It is not an error "
        "and it is not zero:\n" + "\n".join(offenders)
    )


# --------------------------------------------------------------------------- #
# 8. A judged score renders with a coherence measure beside it or renders as
#    uninterpretable, never as a bare number.


def test_trait_score_never_renders_without_coherence():
    offenders = []
    for p in source_files():
        if p.suffix not in {".html", ".astro"}:
            continue
        text = p.read_text()
        # Any spelling of the trait measure, not just the column name. SweepChart
        # draws `p.trait` and ConfoundChart draws `r.value`; both passed vacuously
        # under a literal `trait_score` check.
        draws_trait = re.search(r"\b\w*trait\w*\b", text) is not None
        if draws_trait and "coherence" not in text:
            offenders.append(str(p.relative_to(ROOT)))
    assert not offenders, (
        "Judge-human agreement ran 81% on coherent text against 42% on degenerate "
        "text, worse than chance, and one arm inverted sign entirely. A score "
        "measured on degenerate output is a broken instrument, not a small effect:\n"
        + "\n".join(offenders)
    )


# --------------------------------------------------------------------------- #
# 9. Cosine similarity is a displayed fact, never evidence of disagreement and
#    never a sort key.


def test_cosine_is_never_evidence_of_disagreement():
    # Every name this project has used or might use for the same quantity. The
    # previous version matched only `cosine_sim`; the field was renamed to
    # `angle_similarity` and the test went blind to the code in front of it while
    # staying green. Match the concept.
    similarity = r"(cos(ine)?_?sim\w*|angle_similarity|similarity|cosine)"
    offenders = scan(rf"(disagree|diverg|differ|conflict)\w*.*{similarity}")
    offenders += scan(rf"sort\w*\s*[=(].*{similarity}")
    offenders += scan(rf"\.sort\(.*{similarity}")
    offenders += scan(rf"{similarity}.*\b(desc|descending|rank)\b")
    # A clickable column header is a sort control whatever the handler is called.
    # The header itself is allowed to exist: what is banned is making it operable,
    # so match a button or a header carrying a sort affordance, not plain text.
    offenders += scan(rf"<button[^>]*>\s*[^<]*(similarity|cosine)")
    offenders += scan(rf"<th[^>]*data-(col|sort)[^>]*>[^<]*(similarity|cosine)")
    offenders += scan(rf"data-(col|sort)[^>]*>\s*[^<]*(similarity|cosine)")
    assert not offenders, (
        "Behaviorally indistinguishable vectors can sit far apart in angle "
        "(arXiv:2602.06801). Low cosine similarity is not by itself a finding:\n"
        + "\n".join(offenders)
    )
