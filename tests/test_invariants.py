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
    # Tests write the forbidden spellings on purpose, to prove the scanners
    # bite. `tests/probe.py` is here for a second reason that arrived with it:
    # it builds a fabricated corpus for the checks that need states the real
    # one does not have, so it writes repeated-digit decimals and
    # `is_synthetic = 1` deliberately. Nothing it writes reaches the registry.
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
#
# `fixtures` was here, reading "writes the synthetic corpus", until that corpus
# was removed on 2026-09-19. It came out rather than being left to rot, because
# the entry below is guarded by an existence check: a name in here that no
# longer exists asserts nothing and says nothing about asserting nothing, which
# is the silent-inertness failure this whole file is about, arriving in the
# guard rather than in a scan.
MUST_REACH = {
    "src/controlbun":  "the library",
    "astro/src":     "the view layer, where a default sort would appear",
    "artifacts":     "writes the corpus",
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
    # `format` joined this list when `controlbun.ingest` arrived, because a file
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


def test_no_column_pairs_an_explanation_to_one_named_field():
    """The same closed set, arriving as a column rather than as a CHECK.

    `schema/migrations/008` records why a field is absent, keyed by field name.
    The version that reads as obvious is a column beside each field,
    `chat_template_hash_reason` next to `chat_template_hash`, and it is the
    trip-wire case wearing a schema hat: the set of fields allowed an
    explanation becomes whatever somebody thought of, and the next person with
    an absence worth explaining has to ask for a migration.

    The generic association has no such set, and this is what keeps the next
    convenient column from quietly reintroducing one. A bare `reason` is the
    association's own and does not match.
    """
    ddl = strip_sql_comments(sql_text())
    offenders = [
        line.strip() for line in ddl.splitlines()
        if re.match(r"\s*\w+_(reason|absence|absent|why)\b", line, re.I)
    ]
    assert not offenders, (
        "An explanation bound to one named field enumerates which fields may "
        "carry one. Key it by field name instead:\n" + "\n".join(offenders)
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
# 5. No ordering derives from whether an artifact is published anywhere.


# The four columns that together are the pin, plus the two names the export and
# the page know it by. `artifact_sha256` is not here: it is a fact about the
# bytes rather than about where they are, and a row can record one with no pin.
PIN_COLUMNS = (
    "artifact_repo", "artifact_commit", "artifact_host", "artifact_url_template",
    "artifact_url", "published",
)


def _orders_a_distinct_value_list(hit: str, col: str) -> bool:
    """Whether a matched `ORDER BY` sorts that column's own distinct values.

    `scan` is line-based and a SQL string in this codebase spans several
    adjacent Python literals, so the `SELECT DISTINCT` is never on the line the
    `ORDER BY` is on. Reading a short window above the hit is what makes the
    exemption checkable rather than a name on a list.
    """
    path, line, _ = hit.split(":", 2)
    lines = (ROOT / path).read_text().splitlines()
    window = " ".join(lines[max(0, int(line) - 8): int(line)])
    return bool(re.search(rf"SELECT\s+DISTINCT\s+{col}\b", window))


def test_no_ordering_is_derived_from_whether_an_artifact_is_published():
    """Fetchable is not a rank.

    Four of the five rows in this corpus record no repo, and every one of the
    five is a real direction. Sorting a pinned row up, or an unpinned row down,
    would turn "the author put these bytes somewhere with a URL" into a quality
    score, and the step after a quality score is a default that reads as the
    registry's own judgment.

    The plurality this protects is specific: an author who publishes a vector
    from a paper, a cluster or a lab share, with no public URL anywhere, can be
    argued about here on the same footing as one who pushed to a Hub repo this
    morning.

    **What the constraint makes impossible to express** is a view whose order
    tells a reader which submissions they can actually get. That is a real thing
    somebody will want, and it is a filter rather than an order: `published` is
    on every claimant in the export and a reader can select on it without the
    page having decided for them.

    The `ORDER BY` scan skips a query that is a `SELECT DISTINCT` of the same
    column, which is `artifacts/intake.py` listing the hosts and templates
    already in use so the form can offer them. Alphabetizing a list of strings
    is not ordering submissions, and refusing it would push that query into
    building its own sort somewhere this scan cannot see. The exemption is
    narrow on purpose: it is the same column, distinct, and nothing else in the
    select, so `ORDER BY artifact_host` over a row set is still a finding.
    """
    offenders = []
    for col in PIN_COLUMNS:
        offenders += [
            hit for hit in scan(rf"ORDER\s+BY[^;]*\b{col}\b")
            if not _orders_a_distinct_value_list(hit, col)
        ]
        offenders += scan(rf"sorted\s*\([^)]*\b{col}\b")
        offenders += scan(rf"key\s*=\s*[^,)]*\b{col}\b")
        offenders += scan(rf"\b(sort|rank|order)\w*\s*[=(][^)]*\b{col}\b")
        offenders += scan(rf"\.sort\([^;]*\b{col}\b")
    assert not offenders, (
        "Ordering on whether an artifact is published makes having a URL into a "
        "quality. It is a fact about what the author did with the bytes and not "
        "about the submission:\n" + "\n".join(offenders)
    )


# --------------------------------------------------------------------------- #
# 5b. The model is part of a submission's identity, and nothing else.


def test_no_ordering_is_derived_from_the_model():
    """A model is what a submission is about, never where it ranks.

    `schema/migrations/010` put `model_id` into the primary key. Widening an
    identity is the whole of that change, and the way it stops being the whole
    of it is one sort: `ORDER BY model_id` puts `allenai/...` above
    `meta-llama/...` with nothing on screen saying why, and a reader sees a
    league table of model families that nobody decided to publish. The step
    after that is a default, and a default reads as the registry's own judgment.

    **What the constraint makes impossible to express** is a list whose order
    groups submissions by model. That is a real want and it is grouping rather
    than ordering: `/models/<model>/` already is the grouped view, reached by
    naming the model, and every claimant in the export carries `model_id` for a
    reader to select on.

    Same `SELECT DISTINCT` exemption as the pin columns, and for the same
    reason: `artifacts/intake.py` alphabetizes the model ids already in use so
    the form can offer them, which is sorting a list of strings rather than
    ordering submissions.
    """
    offenders = [
        hit for hit in scan(r"ORDER\s+BY[^;]*\bmodel_id\b")
        if not _orders_a_distinct_value_list(hit, "model_id")
    ]
    offenders += scan(r"sorted\s*\([^)]*\bmodel_id\b")
    offenders += scan(r"key\s*=\s*[^,)]*\bmodel_id\b")
    offenders += scan(r"\b(sort|rank|order)\w*\s*[=(][^)]*\bmodel_id\b")
    offenders += scan(r"\.sort\([^;]*\bmodel_id\b")
    assert not offenders, (
        "Ordering on the model turns an identity into a ranking of model "
        "families. The same label on two models is two submissions that both "
        "stand:\n" + "\n".join(offenders)
    )


def test_the_submission_key_names_the_model():
    """Four columns, or `author/model_id/label@version` is not an identity.

    The failure this stops is a later migration rebuilding `submission` and
    dropping `model_id` back out of the key, which reads as a tidy-up and makes
    one author's two models collide again.

    Read off the last `CREATE TABLE submission...` in migration order, because
    the migrations are the schema and the current shape is whatever the last one
    that rebuilt the table declared.
    """
    ddl = strip_sql_comments(sql_text())
    keys = []
    for table in re.finditer(
        r"CREATE TABLE submission\w*\s*\((.*?)\n\);", ddl, re.S | re.I
    ):
        key = re.search(r"PRIMARY KEY\s*\(([^)]*)\)", table.group(1), re.I)
        if key:
            keys.append([c.strip().strip('"') for c in key.group(1).split(",")])

    assert keys, "no submission table declares a primary key"
    assert keys[-1] == ["author", "model_id", "label", "version"], (
        "the submission key is " + ", ".join(keys[-1]) + ". It has to name the "
        "model: a direction is a tensor in one model's residual basis, so a "
        "submission that does not name the model is not identified, and one "
        "author's takes on two models collide."
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


def _without_comments(text: str) -> str:
    """A template with its comments taken out, because a comment renders nothing.

    This scan asks whether a file draws a trait measure. It read the whole file,
    so a component whose comment explained that a definition contains "a
    bulleted list of what the trait is not" was accused of rendering a trait
    score without a coherence measure beside it.

    That is the third time in one day a rule here has caught a sentence instead
    of the thing the sentence is about: `CLAUDE.md` records banning "best" and
    catching the founding sentence, an ordinal scan matched "1st-person
    retrospective reports" inside an author's methodology, and now this.
    Stripping comments is not a loosening. It narrows the scan to the only part
    of a file that can put a number on a page.
    """
    text = re.sub(r"/\*.*?\*/", " ", text, flags=re.S)
    text = re.sub(r"<!--.*?-->", " ", text, flags=re.S)
    return re.sub(r"(?m)^\s*//.*$", " ", text)


def test_trait_score_never_renders_without_coherence():
    offenders = []
    for p in source_files():
        if p.suffix not in {".html", ".astro"}:
            continue
        text = _without_comments(p.read_text())
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


# --------------------------------------------------------------------------- #
# 10. A namespace claim is never a rank, a filter, or a condition on publishing.


# Every spelling of "does this namespace have an account behind it". Matched as
# a concept rather than as today's column name, because the cosine scan went
# blind for exactly one rename and stayed green while it did.
#
# `claimed_at` is deliberately not in here. Ordering one namespace's own claims
# by when each was made is a statement about sequence, which `views.namespace_view`
# does and should; the scans below that take a sort key add it back, because
# ordering *namespaces* by a claim date is the thing that reads as a rank.
CLAIM_STATUS = r"(is_claimed|claim_status|has_claim|unclaimed|claimed|claims)"


def test_no_ordering_is_derived_from_a_namespace_claim():
    """Nothing puts a claimed namespace above an unclaimed one.

    Claimed and unclaimed are not two tiers with most things in the upper one.
    They are one exception and the normal case, and which of the two is the
    exception depends on nothing but who has happened to sign in: this corpus
    holds one namespace and it is claimed, and the next author to publish here
    will not be. Sort by it and one of those two goes to the bottom of every
    list with nothing on screen saying why.

    The same argument the eval-result ordering rule makes, one object over. An
    order derived from something other than what somebody did to the work is the
    registry asserting a preference and calling it a default.
    """
    offenders = scan(rf"ORDER\s+BY[^;]*\b{CLAIM_STATUS}\b")
    for term in (CLAIM_STATUS, r"claimed_at"):
        offenders += scan(rf"sorted\s*\([^)]*\b{term}\b")
        offenders += scan(rf"key\s*=\s*[^,)]*\b{term}\b")
        offenders += scan(rf"\b(sort|rank)\w*\s*[=(][^)]*\b{term}\b")
        offenders += scan(rf"\.sort\([^;]*\b{term}\b")
    # A clickable column header is a sort control whatever the handler is
    # called, and a claim column in a table of namespaces is a rank whether or
    # not anybody clicks it.
    #
    # Matched on what the header starts with, and `claim` is three different
    # words on this site. "Claimants" counts the people claiming one label and
    # has been a sort control since the model page existed. "Labels claimed"
    # counts what an owner has published under. Only a header that leads with
    # the namespace sense is the one being banned, and this is the third time
    # this project has had to separate a word from its senses rather than ban
    # the substring: `CLAUDE.md` records the other two.
    header = r"(namespace\s+claim|claim(?!ant)|held\s+by|account)"
    offenders += scan(rf"<button[^>]*>\s*{header}")
    offenders += scan(rf"data-(col|sort)[^>]*>\s*{header}")
    # Filtering to the claimed ones is the same designation with the ordering
    # step skipped: it answers "which of these is the real one" by deletion.
    offenders += scan(rf"\.filter\([^;]*\b{CLAIM_STATUS}\b")
    offenders += scan(rf"WHERE[^;]*\b{CLAIM_STATUS}\b\s*(=\s*1|=\s*true|IS\s+NOT\s+NULL)")
    assert not offenders, (
        "A claim says who holds a namespace and nothing about the work published "
        "under it. Ordering or filtering by it turns an account into a quality "
        "signal, which is the designation this registry does not make:\n"
        + "\n".join(offenders)
    )


def test_a_claim_is_bound_to_a_subject_and_never_to_a_handle():
    """The binding is the provider's opaque id, because handles move.

    A claim bound to `preferred_username` breaks the day somebody renames, or
    worse follows the handle to whoever registers it next, which is squatting
    with the registry's help. `handle` is kept as what the provider said on the
    day and is display only, so nothing may key, join or look up by it.
    """
    ddl = strip_sql_comments(sql_text())
    # Every declaration, not the first one found. A migration that redeclares a
    # table is how the convenient version arrives, and a check that stops at the
    # first match would read the careful one forever.
    bodies = [
        m.group(1) for m in
        re.finditer(r"CREATE TABLE namespace_claim\s*\((.*?)\n\);", ddl, re.S | re.I)
    ]
    assert bodies, "no namespace_claim table; a claim with no record is not contestable"

    offenders = []
    for body in bodies:
        line = next(
            (l for l in body.splitlines() if re.search(r"^\s*subject\b", l)), None
        )
        if line is None or not re.search(r"\bNOT\s+NULL\b", line, re.I):
            offenders.append(
                "namespace_claim.subject is missing or nullable. A claim with no "
                "subject is bound to whatever else is on the row, and the only "
                "other candidate is the handle."
            )
        for kind in ("PRIMARY KEY", "UNIQUE"):
            for mm in re.finditer(rf"{kind}\s*\(([^)]*)\)", body, re.I):
                cols = [c.strip().strip('"') for c in mm.group(1).split(",")]
                if {"handle", "preferred_username"} & set(cols):
                    offenders.append(f"{kind} ({mm.group(1).strip()})")
    offenders += scan(r"(WHERE|AND)\s+\w*(handle|preferred_username)\s*=")
    offenders += scan(r"claim\w*\[[\"']?(handle|preferred_username)[\"']?\]\s*==")
    assert not offenders, (
        "A handle is renameable, so a claim keyed on one either breaks on a "
        "rename or follows the name to whoever takes it next:\n" + "\n".join(offenders)
    )


def test_org_membership_is_an_observation_and_never_a_stored_fact():
    """What the provider said, and when. Never what is true now.

    People join and leave organisations, so a membership checked once and held
    forever is stale silently and carries nothing saying it might be. The same
    rule the history audit and the attestations already follow: the result is
    dated, not permanent.
    """
    ddl = strip_sql_comments(sql_text())
    bodies = [
        m.group(1) for m in re.finditer(
            r"CREATE TABLE namespace_membership_observation\s*\((.*?)\n\);",
            ddl, re.S | re.I,
        )
    ]
    assert bodies, (
        "no namespace_membership_observation table; a membership with no "
        "observation date is a badge"
    )

    offenders = []
    for body in bodies:
        line = next(
            (l for l in body.splitlines() if re.search(r"^\s*observed_at\b", l)), None
        )
        if line is None or not re.search(r"\bNOT\s+NULL\b", line, re.I):
            offenders.append(
                "observed_at must exist and be NOT NULL. An undated observation "
                "is a stored fact wearing a different column name."
            )
        keys = re.findall(r"(?:PRIMARY KEY|UNIQUE)\s*\(([^)]*)\)", body, re.I)
        if not any("observed_at" in k for k in keys):
            offenders.append(
                "observed_at has to be part of what makes a row unique, or "
                "looking again overwrites what was seen last time and the "
                "history stops existing"
            )

    # A column asserting a standing membership, anywhere in the schema.
    offenders += [
        line.strip() for line in ddl.splitlines()
        if re.match(r"\s*(is_member|member_of|membership|is_verified|verified)\b",
                    line, re.I)
    ]
    # And anything that edits an observation instead of writing a new one.
    offenders += scan(r"UPDATE\s+namespace_membership_observation")
    offenders += scan(r"INSERT\s+OR\s+REPLACE\s+INTO\s+namespace_membership_observation")
    assert not offenders, (
        "A membership is what a provider answered on a date. Caching it as a "
        "current fact, or overwriting the last answer with a new one, deletes the "
        "only thing that made it honest:\n" + "\n".join(offenders)
    )


def test_a_namespace_permits_more_than_one_claimant():
    """Two accounts claiming one namespace is a state, not a conflict to resolve.

    Making `namespace` unique on its own would make the index the thing that
    decides a contested claim. Both rows stand, both carry their evidence, and a
    reader adjudicates. This is the label rule one object over.
    """
    ddl = strip_sql_comments(sql_text())
    offenders = []
    for kind in ("PRIMARY KEY", "UNIQUE"):
        for m in re.finditer(rf"{kind}\s*\(([^)]*)\)", ddl, re.I):
            cols = [c.strip().strip('"') for c in m.group(1).split(",")]
            if "namespace" in cols and not {"provider", "subject"} <= set(cols):
                offenders.append(f"{kind} ({m.group(1).strip()})")
    assert not offenders, (
        "Constraining a namespace to one claimant makes the schema settle who "
        "holds a contested name:\n" + "\n".join(offenders)
    )


def test_publishing_never_requires_a_claim():
    """No row anywhere needs an account behind it to exist.

    The strongest version of the erosion is not a sort key, it is a foreign key:
    a submission that cannot be written without a claim makes the indexed corpus
    unrepresentable and turns an account into the price of having a voice.
    """
    ddl = strip_sql_comments(sql_text())
    offenders = []
    for table in ("submission", "intervention", "recipe", "eval_suite",
                  "eval_report", "attack", "support_card", "pin",
                  "label_relation", "reproduction"):
        # Every declaration of the table, for the reason the claim check gives:
        # the convenient version arrives as a later migration, not as an edit to
        # the careful one.
        for m in re.finditer(rf"CREATE TABLE {table}\s*\((.*?)\n\);", ddl, re.S | re.I):
            if re.search(r"namespace_claim", m.group(1), re.I):
                offenders.append(f"{table} references namespace_claim")
    assert not offenders, (
        "An author here is a free string somebody wrote down. Requiring a claim "
        "to publish forecloses the indexed corpus and prices a voice at an "
        "account:\n" + "\n".join(offenders)
    )
