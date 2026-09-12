"""Executable invariants.

Prose principles get pattern-matched away; checkable ones do not. Each test here
corresponds to a line in the invariants list in CLAUDE.md. If you settle a new
invariant, add it there and add a test here. An invariant that is only in prose is
not an invariant.

Four of these read the SQL and bite today. The rest scan source and templates for
banned constructs; they currently scan a small codebase and will bite as it grows.
That is the intended shape, not a gap: they are lint, and lint is worth having
before the code it lints exists.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MIGRATIONS = sorted((ROOT / "schema" / "migrations").glob("*.sql"))
# Every directory holding code that can render or order a multi-submission view.
# Adding a frontend without adding it here makes four of the nine invariants go
# silently inert, which is worse than not having them: the suite stays green
# while checking nothing.
SOURCE_DIRS = [ROOT / "src", ROOT / "web", ROOT / "astro" / "src"]

SCANNED_SUFFIXES = {
    ".py", ".sql",                      # backend
    ".html", ".jinja",                  # jinja view layer
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


def source_files() -> list[Path]:
    out: list[Path] = []
    for d in SOURCE_DIRS:
        if d.exists():
            out += [p for p in d.rglob("*") if p.suffix in SCANNED_SUFFIXES]
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


def test_scanner_covers_every_source_directory_that_exists():
    """A frontend that the scanner cannot read is a frontend with no invariants.

    This is the failure mode that bit already: a regex that matched nothing while
    reporting success. Silence from a scan is only meaningful if the scan looked.
    """
    unread = []
    for d in SOURCE_DIRS:
        if not d.exists():
            continue
        files = [p for p in d.rglob("*") if p.is_file()]
        if not files:
            continue  # an empty directory is scaffolding, not a blind spot
        if not any(p.suffix in SCANNED_SUFFIXES for p in files):
            unread.append(d.name)
    assert not unread, (
        "a source directory exists but nothing in it has a scanned suffix:\n  "
        + "\n  ".join(unread)
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
        if p.suffix not in {".html", ".jinja", ".astro"}:
            continue
        text = p.read_text()
        if "trait_score" in text and "coherence" not in text:
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
    offenders = scan(r"(disagree|diverg|differ|conflict)\w*.*cos(ine)?_?sim")
    offenders += scan(r"sort\w*.*cos(ine)?_?sim")
    assert not offenders, (
        "Behaviorally indistinguishable vectors can sit far apart in angle "
        "(arXiv:2602.06801). Low cosine similarity is not by itself a finding:\n"
        + "\n".join(offenders)
    )
