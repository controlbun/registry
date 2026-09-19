"""The supersession markers have to point both ways.

`CLAUDE.md` tells every reader, human or otherwise, to check an entry for a
`**Superseded by:**` line before acting on it. That instruction is only safe if the
markers are complete, and they were not: the 2026-09-12 ordering entry named "No
ranking by default, sorting is user-chosen" in its `**Supersedes:**` line, and that
entry carried no pointer back. It read as live for a day. Anyone following the
instruction would have acted on a rule that had been replaced, and the replaced
rule said there is no default sort, which the site now has.

`CLAUDE.md` also used to state the count. It went stale the moment an entry was
superseded without someone editing that paragraph, which is the same failure one
level up: a fact about the file, written somewhere the file cannot reach.

So the count is gone and this checks the property instead. The doc says what is
true; the test keeps it true.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DECISIONS = ROOT / "DECISIONS.md"
CLAUDE = ROOT / "CLAUDE.md"

# The file documents its own shape at the top with a fill-in-the-blanks example.
TEMPLATE = "YYYY-MM-DD Short title"


def entries() -> list[dict]:
    text = DECISIONS.read_text()
    out = []
    for block in re.split(r"\n(?=## )", text):
        m = re.match(r"## (.+)", block)
        if not m or TEMPLATE in m.group(1):
            continue
        out.append({
            "title": m.group(1).strip(),
            "body": block,
            "supersedes": [
                s.strip().rstrip(".")
                for s in re.findall(r"\*\*Supersedes:\*\*\s*(.+)", block)
            ],
            "marked": bool(re.search(r"\*\*(Superseded by|Amended by):\*\*", block)),
        })
    return out


def claims_nothing(claim: str) -> bool:
    """An entry that says it supersedes nothing is naming no entry."""
    return bool(re.match(r"nothing\b", claim.strip(), re.I))


def test_there_are_entries_to_check():
    assert len(entries()) > 20, "the parse found almost nothing, so it is broken"


def test_a_claim_of_nothing_resolves_to_nothing():
    """The bite, and the reason it is here.

    The match below is a substring one, so a claim short enough to appear
    inside somebody else's title resolves to it. "nothing" is the short claim
    this file actually contains, sixteen times, and it stayed harmless only
    while no title used the word. The first one that did made all sixteen
    entries claim to supersede it at once.
    """
    for said in ("nothing", "nothing.", "Nothing; sharpens X", "nothing. Refines Y"):
        assert claims_nothing(said), f"{said!r} names no entry and has to be dropped"
    # And a real claim is still a claim, including the ones that are a bare
    # title with no date in front of them.
    for said in ("No ranking by default, sorting is user-chosen",
                 "Submissions are versioned and immutable",
                 "2026-09-17 \"No dual-use policy yet\""):
        assert not claims_nothing(said), f"{said!r} is a real supersession"


def test_every_superseded_entry_carries_the_pointer_back():
    """A one-directional supersession is worse than none.

    The new entry knows it replaced something. The old entry does not know it was
    replaced, and the old entry is the one a reader lands on when they search for
    the rule.
    """
    all_entries = entries()
    titles = {e["title"] for e in all_entries}
    unmarked = []

    for e in all_entries:
        for claim in e["supersedes"]:
            # Some Supersedes lines name a passage in another document, or say
            # "nothing" and then explain what they sharpen. Only entry-to-entry
            # claims are checkable here.
            #
            # "nothing" is dropped before the substring match rather than left
            # to fall through it. Sixteen entries say it, the match is a
            # substring one, and the first entry whose title contained the word
            # made every one of those sixteen claim to supersede it. The line
            # says the entry supersedes nothing; taking it at its word is the
            # fix, and `test_a_claim_of_nothing_resolves_to_nothing` keeps it.
            if claims_nothing(claim):
                continue
            match = next(
                (t for t in titles if claim and claim.lower() in t.lower()), None
            )
            if match is None:
                continue
            target = next(x for x in all_entries if x["title"] == match)
            if not target["marked"]:
                unmarked.append((match, e["title"]))

    assert not unmarked, "superseded entries with no pointer back:\n" + "\n".join(
        f"  {old!r}\n      was superseded by {new!r} and does not say so"
        for old, new in unmarked
    )


def test_claude_does_not_hardcode_a_count_of_them():
    """It did, and the number went stale.

    A fact about a file, written in a different file that nothing updates, is a
    fact with a shelf life. The named list stays, because naming which entries are
    traps is the useful part and it changes far less often than the count.
    """
    para = re.search(
        r"\*\*`DECISIONS\.md` keeps superseded entries on purpose\.\*\*(.+?)\n\n",
        CLAUDE.read_text(), re.S,
    )
    assert para, "the paragraph that warns about superseded entries is gone"
    assert not re.search(
        r"\b(one|two|three|four|five|six|seven|eight|nine|ten|\d+)\s+carry\b",
        para.group(1), re.I,
    ), "CLAUDE.md hardcodes how many entries are superseded; that number goes stale"


def test_claude_still_names_which_entries_are_traps():
    """Only that the warning exists, not what is in it.

    The first draft of this parsed the prose list and matched each name against
    DECISIONS.md. It split "ranking by precision and attack survival" in half on
    the word "and" and reported a failure that was entirely its own. Parsing an
    English list is brittle in a way no amount of patching fixes, and the check
    that caught the real bug is the structural one above.

    So this only asserts the warning is still there. Which entries it names is a
    judgment for whoever edits the file.
    """
    text = CLAUDE.read_text()
    assert "read as live rules when they are not:" in text, (
        "CLAUDE.md no longer warns that some superseded entries look live, which "
        "is the sentence that makes the markers worth checking"
    )
