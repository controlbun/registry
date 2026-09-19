"""Re-derive every number the site publishes, and exit non-zero on drift.

Ported in spirit from the arena's `_falsifier/verify.py`. The premise there and
here: **a database row is not evidence.** A number that only exists because
something wrote it down is a claim, and the whole value proposition of this
registry is that its numbers are checkable.

What this can and cannot do, stated plainly, because a falsifier that overclaims
is worse than none:

**Derived quantities are recomputed from the raw artifact.** Shape, dtype, L2
norm, the sha256 of the file and the angle between two interventions are
recomputed from the safetensors files themselves and compared against what the
database stores and what the built pages render. If a tensor changes and a stored
norm does not, this fails. If the bytes change at all and the recorded digest does
not, this fails, which is the case the other three miss: a substituted tensor of
the same shape, dtype and norm satisfies every check that came before it.

**Reported quantities are traced, not recomputed.** Trait score, coherence,
transfer, the coefficient curve and the confound axes come from an evaluation this
registry did not run. Nothing here can recompute them, and no script can tell you
whether an author ran their own eval honestly. What it can do is prove the number
on the page is the number in the database, with no drift and nothing invented in
between. A figure that appears on a page and exists nowhere upstream is exactly
what this catches.

**Nothing here validates an author's claim.** Validity is a conversation the
registry hosts, not a property it certifies. This checks transport and
derivation. It does not check truth.

    .venv/bin/python falsifier/verify.py

Exits 0 when everything reconciles, 1 otherwise, with the failures named.
"""

from __future__ import annotations

import hashlib
import html
import json
import re
import sqlite3
import sys
from pathlib import Path

import numpy as np
from functools import lru_cache

from safetensors.numpy import load_file

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from registry import artifact  # noqa: E402
from registry.artifact import UnsafeArtifactPath, local_path  # noqa: E402


@lru_cache(maxsize=None)
def _vector(path: str):
    """Cached for the same reason comparison is: rechecking every published angle
    is quadratic in claimants, and the raw artifacts do not change mid-run."""
    return next(iter(load_file(path).values()))

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "registry.db"
EXPORT = ROOT / "astro" / "src" / "data" / "registry.json"
DIST = ROOT / "astro" / "dist"

# Every measurement on every page renders through .toFixed(4). Anything matching
# this shape in rendered copy is a published number and has to be accounted for.
PUBLISHED_NUMBER = re.compile(r"(?<![\d.])\d\.\d{4}(?![\d.])")

TOLERANCE = 1e-6

failures: list[str] = []


def fail(check: str, detail: str) -> None:
    failures.append(f"[{check}] {detail}")


# A region the page attributes to an author rather than asserting itself: a
# definition, a theory, a support card's purpose, an attacker's response. The
# attribute is written by the components and checked below, so it is a contract
# and not an incidental class name.
AUTHORED = re.compile(r"<(\w+)[^>]*\sdata-authored[^>]*>.*?</\1>", re.S)


def text_of(page: Path, *, authored: bool = False) -> str:
    """Reader-visible copy only. Script and style content is not published
    prose, and SVG geometry is coordinates rather than measurements.

    **Authored prose comes out too, and that is a decision rather than a
    convenience.** A definition is one author's theory of their label in their
    own words, and a real one arrived quoting its own measurements: `F =
    0.9690`, `p = 0.0005`, a permutation null. Those are the author's claims
    about their own work and they trace to the submission rather than to
    anything this registry derived, so holding them to the export would call a
    true number fabricated. Scanning them as though the registry asserted them
    was worse in the other direction: one of them collided with a fixture value
    and convicted a real page of publishing figures that were invented.

    What keeps this from being a hole is `check_authored_regions_are_marked`.
    The exclusion is only as trustworthy as the marking, so the marking is
    checked: every claimant definition in the export has to appear inside one
    of these regions on the page that shows it, and a page cannot mark itself
    entirely and go unread.

    Pass `authored=True` to get only those regions, which is how the guard
    reads them.
    """
    raw = page.read_text()
    for tag in ("script", "style", "svg"):
        raw = re.sub(rf"<{tag}.*?</{tag}>", " ", raw, flags=re.S)
    if authored:
        raw = " ".join(m.group(0) for m in AUTHORED.finditer(raw))
    else:
        raw = AUTHORED.sub(" ", raw)
    return html.unescape(re.sub(r"<[^>]+>", " ", raw))


# --------------------------------------------------------------------------- #


def _pinned(row) -> bool:
    """Whether this row's bytes live somewhere other than this checkout.

    **A file that is not here is not the same as a file that is missing.** The
    whole point of a pin is that the artifact lives at somebody else's commit
    and this repository holds a pointer, so for a pinned row the absence of a
    local copy is the normal case and the designed one. Only a row that records
    no remote at all is claiming bytes this checkout should be holding, and for
    that one a missing file is a real finding.

    This distinction did not exist while every row was a vendored file, which
    is why the check was written without it. `artifacts/intake.py` writes rows
    of the other kind, and the first real submission was one.

    The falsifier does not fetch. Rechecking a pinned artifact means pulling it
    over the network, which would make the gate depend on somebody else's host
    being up and on this machine having a connection, and `make verify` never
    needs the network by design. What that costs is named in the summary rather
    than hidden: these rows are recorded, not rechecked.
    """
    return bool(row["artifact_repo"] or row["served_repo"])


def check_artifacts_match_their_metadata(conn: sqlite3.Connection) -> None:
    """Shape, dtype and L2 norm recomputed from the tensor on disk.

    The comparison itself is `registry.artifact.disagreements`, which is also
    what the client applies to bytes it fetched and what both seed scripts apply
    before they write a row. Three callers, one rule, one tolerance on the norm:
    this used to hold its own copy, and a gate that disagrees with the write
    path about what counts as a mismatch either passes rows it should stop or
    stops rows it should have let through.

    What stays here is everything only a falsifier does: report instead of
    raising, skip a row with no bytes in this repository, and name the row.
    """
    rows = conn.execute(
        "SELECT id, artifact_path, shape, dtype, l2_norm,"
        " artifact_repo, served_repo FROM intervention"
    ).fetchall()
    if not rows:
        fail("artifacts", "no interventions to check; the falsifier is inert")

    for row in rows:
        if not row["artifact_path"]:
            continue
        # Refuses a path that escapes the repository rather than reading
        # whatever is there. Report, never raise, like every other check here.
        try:
            path = local_path(row["artifact_path"], root=ROOT)
        except UnsafeArtifactPath as exc:
            fail("artifacts", f"{row['id']}: {exc}")
            continue
        if not path.exists():
            if _pinned(row):
                continue
            fail("artifacts", f"{row['id']}: {row['artifact_path']} is missing")
            continue

        try:
            vector = _vector(str(path))
        except (OSError, ValueError) as exc:
            fail("artifacts", f"{row['id']}: {row['artifact_path']} is unreadable "
                              f"({exc})")
            continue

        # A stored NULL arrives as a `None` on the claim and is skipped there,
        # so the three `is not None` branches this used to carry are one rule in
        # one place now: absence is not a mismatch.
        for line in artifact.disagreements(
            artifact.Claim(shape=row["shape"], dtype=row["dtype"],
                           l2_norm=row["l2_norm"]),
            artifact.facts_of(vector),
        ):
            fail("artifacts", f"{row['id']}: {line}")


def check_artifact_digests_match_the_record(conn: sqlite3.Connection) -> None:
    """The sha256 of the file on disk against the digest its row records.

    Shape, dtype and norm are three facts about a tensor and a great many tensors
    satisfy all three. The check above is what a substituted artifact passes; this
    is the one it does not.

    **What this cannot reach, said plainly.** Only rows whose bytes are in this
    repository. A row that records a digest and points at someone else's repo is
    exactly the row the column exists for, and nothing offline can fetch it. The
    client checks that one at the moment it fetches, which is the only moment it
    can be checked, and this gate stays runnable from a clean checkout with no
    network.

    **A row with no recorded digest is skipped rather than failed.** Most
    artifacts are pointed at rather than held and nobody hashed their bytes;
    absence is its own state here as everywhere. What is failed is a run in which
    no digest was rechecked at all, because a check that looked at nothing is the
    failure mode this repository has shipped six times.

    **The synthetic rows are the weak half and say so.** `fixtures/build.py`
    writes those files and hashes what it just wrote, in one run, so the two
    cannot disagree by the time this reads them. The vendored rows are the real
    test: `artifacts/soham/` is committed rather than regenerated, and its digest
    reaches the database only by matching what `artifacts/source.py` recorded at
    ingest.
    """
    rows = conn.execute(
        "SELECT id, artifact_path, artifact_sha256,"
        " artifact_repo, served_repo FROM intervention"
    ).fetchall()

    checked = 0
    for row in rows:
        if not row["artifact_sha256"]:
            continue
        if not row["artifact_path"]:
            fail("digests", f"{row['id']}: a digest is recorded and no path is, "
                            "so there is nothing here to check it against")
            continue
        # Report, never raise, and refuse a path that escapes the repository
        # rather than hashing whatever is at the other end of it.
        try:
            path = local_path(row["artifact_path"], root=ROOT)
        except UnsafeArtifactPath as exc:
            fail("digests", f"{row['id']}: {exc}")
            continue
        if not path.exists():
            if _pinned(row):
                continue
            fail("digests", f"{row['id']}: {row['artifact_path']} is missing, so "
                            "the recorded digest describes bytes nobody has")
            continue

        # Hashed without parsing, so the derived facts are a digest and a byte
        # count and nothing else. `disagreements` compares only what both sides
        # hold, which is what lets the same function serve this check and the
        # one above without either of them growing a mode.
        blob = path.read_bytes()
        for line in artifact.disagreements(
            artifact.Claim(sha256=row["artifact_sha256"]),
            artifact.Facts(sha256=hashlib.sha256(blob).hexdigest(),
                           size=len(blob)),
        ):
            fail("digests", f"{row['id']}: {row['artifact_path']} is {line}")
        checked += 1

    if checked == 0:
        fail("digests", "no recorded digest was rechecked against a file on "
                        "disk; this check is inert")


def check_angles_recompute(payload: dict) -> None:
    """The angle between two interventions, recomputed from both tensors.

    This is the one published number that is genuinely derived rather than
    reported, so it is the one a falsifier can actually falsify.
    """
    paths: dict[str, str] = {}
    for entry in payload["labels"]:
        for claimant in entry["claimants"]:
            # The exported `ref`, not a fourth spelling of the format. A
            # falsifier that builds the key itself checks the pairs against a
            # dictionary keyed the way the falsifier writes refs rather than
            # the way the site does, which is a lookup that silently misses.
            paths[claimant["ref"]] = claimant.get("artifact_path")

    checked = 0
    for entry in payload["labels"]:
        for pair in entry["pairs"]:
            if pair["angle_similarity"] is None:
                continue
            a, b = paths.get(pair["a"]), paths.get(pair["b"])
            if not a or not b:
                fail("angles", f"{pair['a']} vs {pair['b']}: an artifact path is "
                               "missing, so the published angle cannot be rechecked")
                continue

            # Report, never raise. An unreadable artifact is drift to be named, and
            # a falsifier that crashes is indistinguishable in CI from one that is
            # broken; neither tells you which number stopped reconciling.
            try:
                va = _vector(str(local_path(a, root=ROOT)))
                vb = _vector(str(local_path(b, root=ROOT)))
            except (OSError, FileNotFoundError, ValueError,
                    UnsafeArtifactPath) as exc:
                fail("angles", f"{pair['a']} vs {pair['b']}: cannot read a raw "
                               f"artifact to recheck the published angle ({exc})")
                continue
            actual = float(np.dot(va, vb) / (np.linalg.norm(va) * np.linalg.norm(vb)))

            if abs(actual - pair["angle_similarity"]) > TOLERANCE:
                fail("angles", f"{pair['a']} vs {pair['b']}: recomputes to "
                               f"{actual:.6f} but published {pair['angle_similarity']}")
            checked += 1

    if checked == 0:
        fail("angles", "no published angle was rechecked; this check is inert")


def check_published_numbers_are_accounted_for(payload: dict) -> None:
    """Every number rendered on a page must exist upstream.

    The check that matters. A figure that appears in the built site and traces to
    nothing in the export is fabricated, whether by a template bug or by hand.
    """
    known: set[str] = set()

    def remember(value) -> None:
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            known.add(f"{float(value):.4f}")
        elif isinstance(value, dict):
            for v in value.values():
                remember(v)
        elif isinstance(value, list):
            for v in value:
                remember(v)

    remember(payload)

    pages = sorted(DIST.rglob("index.html"))
    if not pages:
        fail("published", "no built pages found; run `make site` before verifying")
        return

    for page in pages:
        where = page.relative_to(DIST).parent or Path(".")
        for number in set(PUBLISHED_NUMBER.findall(text_of(page))):
            if number not in known:
                fail("published", f"/{where}/ shows {number}, which appears nowhere "
                                  "in the exported data")


def _authored_texts(payload: dict) -> list[tuple[dict, str]]:
    """Every run of prose the site attributes to a person, with whose it is.

    Definitions, the reasons beside an absence, and the detail recorded with a
    namespace claim's evidence. All three are somebody's own words and all
    three carry numerals: a definition quotes its own measurements, a reason
    names the file and line where the value was looked for, and a claim made on
    a human decision records the reasoning behind it. The second kind joined
    this list with `schema/migrations/008`, which is when the first one
    existed; the third with 009.

    Keyed off the export rather than off the page, so a region that stopped
    being marked is found by its absence from the marked side rather than by
    somebody remembering to look for it.
    """
    out: list[tuple[dict, str]] = []
    for entry in payload["labels"]:
        for claimant in entry["claimants"]:
            out.append((claimant, " ".join((claimant.get("definition") or "").split())))
            for reason in (claimant.get("absences") or {}).values():
                out.append((claimant, " ".join((reason or "").split())))
    # A claim lives on the namespace's own page rather than on a submission, so
    # it is read off the owner index. The subject reported in a failure is the
    # namespace, shaped to the same three keys the message below formats.
    for owner in payload.get("owner_index", []):
        subject = {
            "author": owner["owner"], "label": "namespace", "version": "claim",
        }
        for claim in owner.get("claims", []):
            for item in claim.get("evidence", []):
                out.append((subject, " ".join((item.get("detail") or "").split())))
    return [(c, t) for c, t in out if t]


def check_authored_regions_are_marked(payload: dict) -> None:
    """The exclusion in `text_of` is only as good as the marking, so: is it marked.

    Two ways this goes wrong and both are checked.

    **Authored prose rendered without the attribute** puts the author's numbers
    back under the registry's own assertion, which is the thing the marking
    exists to prevent. So every claimant definition in the export, and every
    reason recorded beside an absence, has to turn up inside a marked region on
    some built page.

    **A page that marks everything** reads as entirely quoted and is scanned
    for nothing, which would let a template bug publish any figure it liked.
    So a page whose unmarked copy is shorter than its marked copy is a finding,
    on the reasoning that a page is a registry's page with the author quoted in
    it, never the reverse.

    Neither is hypothetical in the way the rest of this file's checks are. The
    marking arrived the same day as the first definition containing numerals,
    which is to say the day the question could first be got wrong.

    **An absence with no reason is nothing here.** Most absences have none and
    never will, and there is nothing to mark for those, so they neither pass
    nor fail this. A missing reason is not a finding anywhere in this project.
    """
    pages = sorted(DIST.rglob("index.html"))
    if not pages:
        fail("authored", "no built pages found; run `make site` before verifying")
        return

    authored = _authored_texts(payload)

    # The question is not whether a definition is marked somewhere. It is
    # whether one is **rendered outside** a marked region, which is the state
    # that puts an author's numbers under the registry's own assertion. A
    # definition that appears on no page is not rendered and there is nothing
    # to mark, which is the ordinary case for a corpus whose pages are a
    # fixture rather than a build.
    #
    # Matched on a distinctive run rather than the whole string, because a page
    # wraps and collapses whitespace and this is asking where the text sits,
    # not whether it survived character for character.
    unmarked = " ".join(" ".join(text_of(page).split()) for page in pages)
    for claimant, text in authored:
        if text[:60] in unmarked:
            # The exported `ref` where there is one. The namespace subjects
            # below are not submissions and carry none, so they fall back to
            # the three parts they do have.
            named = claimant.get("ref") or (
                f"{claimant['author']}/{claimant['label']}@{claimant['version']}")
            fail("authored",
                 f"{named}: {text[:60]!r} renders outside any "
                 "`data-authored` region, so its numbers are scanned as the "
                 "registry's own and a figure the author is quoting reads as "
                 "one this registry derived")

    for page in pages:
        where = f"/{page.relative_to(DIST).parent}/"
        own = len(text_of(page).split())
        theirs = len(text_of(page, authored=True).split())
        if theirs > own:
            fail("authored", f"{where} is more quoted prose than page. A marked "
                             "region is not scanned, so a page that is mostly "
                             "marked is a page that is mostly unchecked")


def check_export_matches_the_database(conn: sqlite3.Connection, payload: dict) -> None:
    """Reported numbers are transported without drift."""
    # Keyed on the submission, not on an id convention. This used to look the row
    # up as `iv_<author>`, which held only while every author had published once:
    # three takes by one person on one label all hashed to the same key, so two of
    # them were never checked and the third was checked against whichever row the
    # dict happened to keep. An identity the schema does not promise is not an
    # identity, which is the same argument `schema/migrations/010` makes one step
    # further out: the key here is all four columns because the schema's is.
    stored = {
        (row["author"], row["model_id"], row["label"], row["version"]): row
        for row in conn.execute(
            "SELECT i.author, i.model_id, i.label, i.version, r.trait_score,"
            " r.coherence_score, r.transfer_score FROM eval_report r"
            " JOIN eval_suite s ON s.id = r.eval_suite_id"
            " JOIN intervention i ON i.id = r.intervention_id"
            " WHERE s.author = i.author"
        )
    }

    checked = 0
    for entry in payload["labels"]:
        for claimant in entry["claimants"]:
            key = (claimant["author"], claimant["model_id"],
                   claimant["label"], claimant["version"])
            row = stored.get(key)
            if row is None:
                continue
            checked += 1
            for field, column in (
                ("trait_score", "trait_score"),
                ("coherence_score", "coherence_score"),
                ("transfer_score", "transfer_score"),
            ):
                published, recorded = claimant[field], row[column]
                if published is None and recorded is None:
                    continue
                if published is None or recorded is None or \
                        abs(published - recorded) > TOLERANCE:
                    ref = f"{key[0]}/{key[1]}@{key[2]}"
                    fail("transport", f"{ref}.{field}: database has {recorded!r} "
                                      f"but the export publishes {published!r}")

    if checked != len(stored):
        fail("transport", f"{len(stored)} self-reported eval rows exist but only "
                          f"{checked} were matched to a published claimant")


def _numbers_under(value, into: set[str]) -> None:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        into.add(f"{float(value):.4f}")
    elif isinstance(value, dict):
        for v in value.values():
            _numbers_under(v, into)
    elif isinstance(value, list):
        for v in value:
            _numbers_under(v, into)


def check_synthetic_marker_matches_the_page(payload: dict) -> None:
    """The marker has to describe the page, in both directions.

    This used to be one question: is anything in the corpus fabricated, and if so
    does every page say so. That was right while everything was a fixture and
    became wrong the moment one submission was not, because it demanded the
    sentence "every figure here is fabricated" on a page showing a real
    measurement. A marker that is sometimes false is not a marker.

    So it is two questions now, and the second is the one that was missing:

      * A page showing a figure that traces only to a synthetic row must carry
        the marker.
      * A page showing no such figure must not carry it.

    Numbers are attributed rather than pages, so nothing here needs to know how
    routes are built. A value that appears under both a synthetic and a real
    claimant is attributed to neither, which is the conservative reading: 1.0000
    is a fixture's L2 norm and also a real one's, and it cannot convict a page.
    """
    synthetic: set[str] = set()
    real: set[str] = set()
    for entry in payload["labels"]:
        for claimant in entry["claimants"]:
            _numbers_under(claimant, synthetic if claimant["is_synthetic"] else real)

    only_synthetic = synthetic - real
    only_real = real - synthetic
    if not only_synthetic and payload.get("any_synthetic"):
        fail("synthetic", "no figure is uniquely traceable to a fixture, so this "
                          "check cannot catch an unmarked page; it is inert")

    for page in sorted(DIST.rglob("index.html")):
        where = f"/{page.relative_to(DIST).parent}/"
        body = text_of(page)
        shown = set(PUBLISHED_NUMBER.findall(body))
        marked = "Synthetic corpus" in body

        if shown & only_synthetic and not marked:
            fail("synthetic", f"{where} publishes fabricated figures "
                              f"({', '.join(sorted(shown & only_synthetic))}) "
                              "with no marker on the page")
        if marked and not (shown & only_synthetic):
            if shown & only_real:
                fail("synthetic", f"{where} carries the synthetic marker but every "
                                  "figure on it traces to a real submission")


# --------------------------------------------------------------------------- #


def main() -> int:
    if not DB.exists():
        print("no registry.db; run fixtures/build.py first", file=sys.stderr)
        return 1
    if not EXPORT.exists():
        print("no export; run registry.export first", file=sys.stderr)
        return 1

    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    payload = json.loads(EXPORT.read_text())

    check_artifacts_match_their_metadata(conn)
    check_artifact_digests_match_the_record(conn)
    check_angles_recompute(payload)
    check_export_matches_the_database(conn, payload)
    check_published_numbers_are_accounted_for(payload)
    check_synthetic_marker_matches_the_page(payload)
    check_authored_regions_are_marked(payload)

    if failures:
        print(f"falsifier: {len(failures)} failure(s)\n", file=sys.stderr)
        for line in failures:
            print(f"  {line}", file=sys.stderr)
        print("\nA published number that does not re-derive is not evidence.",
              file=sys.stderr)
        return 1

    # Said out loud rather than left implicit. A row whose bytes are at
    # somebody else's commit is not rechecked here, because the gate does not
    # reach the network, so a green falsifier covers fewer rows than the corpus
    # holds. A number that nobody counted is how a check goes quietly inert,
    # which is the failure this file exists to make impossible.
    elsewhere = conn.execute(
        "SELECT COUNT(*) FROM intervention"
        " WHERE artifact_repo IS NOT NULL OR served_repo IS NOT NULL"
    ).fetchone()[0]
    print("falsifier: every published number re-derives or traces to its source")
    if elsewhere:
        print(f"falsifier: {elsewhere} row(s) pinned to bytes outside this "
              "checkout, recorded rather than rechecked; `registry.fetch` "
              "verifies those against their digest when anybody loads one")
    return 0


if __name__ == "__main__":
    sys.exit(main())
