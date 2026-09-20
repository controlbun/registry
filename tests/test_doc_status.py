"""Every document says, at the top, whether it still instructs.

The doc set grew a failure that prose alone could not stop. `GO-LIVE.md` is a
ten-step runbook whose steps flip repository visibility and point DNS; it was
executed on 2026-09-19 and 2026-09-20, and nothing in the file said so. `V1.md`
is a plan that shipped. Both read as live instructions to anybody arriving cold,
and an agent that reads instructions executes them. The same drift in a quieter
form ran through the live documents: `CLAUDE.md` forbade an upload route the
project had already built, `V2.md` named two gates that no longer exist, and
`BRIEF.md` opened by saying the name was undecided.

The fix is a status block under the title, and the reason it is a test rather
than a convention is the rest of this repository: `minor_updates.md` 2026-09-13
records an anchor-file drift audit that found two stale `BRIEF.md` lines and
deliberately left them, which was right at the time and is exactly how a
convention rots. A checked one cannot.

**What this deliberately does not check.** Not the word after "Status", because a
fixed vocabulary of document states would be a closed enum on the one field here
that is prose, and "spent, and do not run it again" carries more than a token
from a list ever would. Not whether the claims underneath are true, which no test
can do. What it checks is that somebody stated a state on a date, which is the
property that was missing.

The date is when the status was last stated, not a certificate that every
sentence below it was re-verified. `WHAT-IT-DOES.md` is the document that carries
per-claim checks; this is a weaker and more honest thing.
"""

from __future__ import annotations

import datetime as dt
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Where documents that instruct somebody live. `astro/` is excluded because its
# markdown is page content rather than instruction, and `_attest/` because a
# manifest is a list of hashes.
DIRS = {".", "artifacts", "brand"}

# A status block: a blockquote, the word, an ISO date, a full stop.
STATUS = re.compile(r"^> \*\*Status (\d{4}-\d{2}-\d{2})[.,]")

# How far down the block may sit. `README.md` puts the lede above it, on purpose:
# the first thing a stranger reads should be what this is, not its bookkeeping.
WINDOW = 12


def _documents() -> list[Path]:
    out = subprocess.run(
        ["git", "ls-files", "*.md"], cwd=ROOT, capture_output=True, text=True,
        check=True,
    ).stdout.split()
    return [ROOT / rel for rel in out if Path(rel).parent.as_posix() in DIRS]


def _status_of(text: str) -> re.Match | None:
    for line in text.split("\n")[:WINDOW]:
        found = STATUS.match(line)
        if found:
            return found
    return None


def test_the_scan_finds_the_documents_it_is_for():
    """A control, because an empty glob passes every assertion below it.

    This repository has shipped four checks that were green for the wrong
    reason, including one whose file enumeration never saw the host it was
    written to catch. The named files are the ones whose staleness caused this
    test to exist, so if the discovery stops finding them it has stopped working
    rather than stopped having work to do.
    """
    found = {path.relative_to(ROOT).as_posix() for path in _documents()}
    assert len(found) >= 10, f"only found {len(found)} documents, so the glob broke"
    for required in ("CLAUDE.md", "DECISIONS.md", "BRIEF.md", "GO-LIVE.md",
                     "V1.md", "V2.md", "README.md", "artifacts/INTAKE.md"):
        assert required in found, f"{required} is tracked but the scan missed it"


def test_every_document_states_its_status_and_dates_it():
    missing = [
        path.relative_to(ROOT).as_posix() for path in _documents()
        if not _status_of(path.read_text())
    ]
    assert not missing, (
        "these documents do not say whether they still instruct:\n  "
        + "\n  ".join(missing)
        + f"\n\nPut a line matching {STATUS.pattern!r} in the first {WINDOW} "
        "lines, saying what the document is and whether it is still to be acted "
        "on. A spent runbook that does not say so gets run again."
    )


def test_no_status_is_dated_in_the_future():
    """A date that has not happened is a claim nobody made.

    The cheap way to satisfy the test above is to paste a block from another
    file, and the cheap way to satisfy it again next year is to leave the date
    alone. Neither is caught here. What is caught is the typo that puts a
    document's status in a year that has not arrived, which would otherwise read
    as freshly checked forever.
    """
    today = dt.date.today()
    ahead = []
    for path in _documents():
        found = _status_of(path.read_text())
        if found and dt.date.fromisoformat(found.group(1)) > today:
            ahead.append(f"{path.relative_to(ROOT).as_posix()}: {found.group(1)}")
    assert not ahead, "status dated in the future:\n  " + "\n  ".join(ahead)


def test_a_document_without_one_is_actually_caught(tmp_path):
    """Proves the rule bites, rather than trusting that it does.

    Every document in the tree passes, which is the state in which a check
    quietly stops doing anything. Three cases: nothing, a heading with no block,
    and a block pushed below the window by somebody adding front matter.
    """
    assert _status_of("") is None
    assert _status_of("# A title\n\nStraight into the prose.\n") is None
    assert _status_of("\n" * 20 + "> **Status 2026-09-20.** Live.\n") is None, (
        "a block below the window counts as absent; a reader does not scroll "
        "to find out whether a runbook is spent"
    )
    assert _status_of("# A title\n\n> **Status 2026-09-20.** Live.\n") is not None
