"""A sign-in capture becomes a namespace claim, with nobody retyping a subject id.

Premise, restated because a premise stated in one document gets violated in every
other one: **plurality is the product; the registry never designates, consumers
pin, visibly.** A claim records that an account was bound to a namespace on a
date, with dated evidence beside it. It is never an ordering, never a filter and
never a condition on publishing, and a namespace with no claim is not a namespace
missing one. `tests/test_invariants.py` fails the build on the sort, the
comparator, the column header and the filter, so that property is executable
rather than asserted in this paragraph.

## The gap this closes

`/signed-in/` writes a dated capture of what Hugging Face said about one account
and hands it to the person who signed in, as a file they download.
`schema/migrations/009` defines the three tables a claim is made of. Nothing
joined them, so the one real claim in this corpus was made by a person reading a
capture on screen and typing its values into `artifacts/seed.py`. Every other
real value here is derived from a file by a script, and transcription is what
this project refuses everywhere else: a fact that was typed in is a fact that
can be typed in wrong, and the row is what every later check reads.

**The capture used to come from a loopback tool and now comes from the browser.**
`artifacts/signin.py` was deleted on 2026-09-20 with the work that made signing
in work on the published site, for the reason `DECISIONS.md` gives: two paths
producing the same object is the failure this repository has hit more than any
other. Nothing about the shape changed. A capture is still one JSON object with
the same keys, `orgs` still has the same three states, and this file still reads
it without knowing which half of the project wrote it.

## Three files, and the line between them is deliberate

    artifacts/memberships.jsonl   the capture. Gitignored, and stays that way.
                                  Either the downloaded file itself or a file
                                  the downloads were appended to; both read.
    artifacts/claims.jsonl        the record. Tracked, append-only, this file's.
    registry.db                   rebuilt from the record on every `make site`.

The capture is a dated statement about a real person, including whatever the
provider chose to return, and this repository is public. The record carries the
same dated facts the row carries and not one field more: namespace, provider,
subject, handle, the dates, the organization and the role. Publishing a capture
would be a decision to take on purpose rather than a side effect of signing in,
so the two files are separate and only one of them is tracked.

**The record is durable because the database is not.** `make site` drops
`registry.db` and rebuilds it, so a claim written only into a column is gone on
the next build. `artifacts/published.json` and `artifacts/intake.jsonl` are the
two precedents, and `publish.apply_pins` is the precedent for the shape: one
function turns the record into rows, and both the rebuild and the recording step
call it, so the two cannot come apart.

## What is derived and what is authored

Derived from the capture, every time: `provider`, `subject`, `handle`,
`claimed_at`, and one observation per organization with its role, its date and
the endpoint that answered. None of it is typed and none of it is defaulted.

Given by the person claiming: the namespace, because a namespace is not in a
capture. `soham` and `sohampadia` are different strings on purpose, and which
namespace an account is claiming is the one thing the provider has no opinion
about.

Authored: the evidence detail, which is prose somebody can disagree with. That
is what evidence is here, including for `repo`: the sentence is an argument that
a repository and an account are the same person, and an argument is written
rather than computed. It renders inside a `data-authored` region for that reason.

## The binding is `sub`, and a membership is a look rather than a status

A claim is keyed on the provider's opaque subject. The handle is carried beside
it as what the provider said on the day, and nothing here keys, joins, looks up
or matches by it, because handles are renameable and a claim bound to one either
breaks on a rename or follows the name to whoever registers it next.

An observation is what an endpoint answered at a moment. Looking again appends a
second line beside the first, which becomes a second row, because `observed_at`
is part of what makes a row unique. There is no column saying somebody is a
member of anything now, and this file writes no `UPDATE` at all.

Each row's primary key is derived from exactly the columns its `UNIQUE`
constraint is made of, so a duplicate is refused by both rather than by one, and
no id is ever typed.

## Nothing here writes a token

A capture written by `/signed-in/` carries none, by construction. This
refuses one anyway: every key in the capture is walked, and a name that reads
like a credential stops the whole run before anything is appended or inserted.
A capture is read in order to make a tracked row, and the cost of being wrong in
that direction is a secret in a public repository. That matters more now, not
less: a capture arrives as a file somebody else downloaded from a browser and
handed over, rather than as a file this machine wrote.

## No closed enum, anywhere

`provider`, the evidence `kind` and the membership `role` are carried through as
strings and compared against nothing. A shape this file cannot read is refused
with the reason, which is that there is no reader for it here, and not with a
claim that the shape is illegitimate. Refuse what cannot be verified, and say
that instead.

## What this makes impossible to express

A claim for an account nobody can sign in as. There is no `--subject` flag and
no way to hand-write a capture that this will read, so an author whose identity
is real and unprovable through a configured provider cannot be claimed by this
path. `adopt` is not that door: it reads rows that already exist and cannot
invent an account. That absence is deliberate for the machine-read half of a
claim: `/signed-in/` has no way to write a capture by hand either, and the same
gap sits one object earlier there. The authored half stays open, which is where
an entry for somebody else's published direction goes.

Also impossible: a claim somebody makes without the author. Claiming is still a
command run on this machine against a capture somebody handed over, because a
claim is a row in a corpus that is a file in git. `/signed-in/` produces the
evidence and persists nothing, and there is no table behind it that would.

Also impossible: a claim made at a moment other than a capture. `claimed_at` is
the capture's own timestamp and there is no way to give it another, so a claim
dated later than the evidence that produced it cannot be written down.

    .venv/bin/python artifacts/claim.py record --namespace soham \\
        --evidence repo=@some-file.txt
    .venv/bin/python artifacts/claim.py observe
    .venv/bin/python artifacts/claim.py replay
    .venv/bin/python artifacts/claim.py show
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "src"))

from controlbun import db  # noqa: E402

# The capture, downloaded from `/signed-in/` and gitignored. Read here and never
# copied: what leaves this file is the projection below, field by field. Point
# `--captures` straight at the downloaded file, or append downloads to this one.
CAPTURES = HERE / "memberships.jsonl"

# The record. Tracked, because it is the only durable copy of a claim.
RECORD = HERE / "claims.jsonl"

# Two shapes, namespaced and versioned, in one append-only file. A claim and an
# observation are separate lines because they are separate statements: an
# observation is true of the account whether or not it claimed anything, and a
# second look writes observations with no second claim.
CLAIM = "controlbun.registry/namespace-claim@1"
OBSERVATION = "controlbun.registry/membership-observation@1"

# Substrings, matched against key names and not against values. A capture from
# `/signed-in/` can contain none of these; a file that does was written by
# something else and is not going to be turned into a tracked row.
CREDENTIAL_WORDS = (
    "token", "secret", "password", "credential", "authorization",
    "apikey", "api_key", "private_key", "bearer", "verifier",
)


class Refused(ValueError):
    """Something this tool will not do, with the reason already in the message.

    One class for every refusal, because the reader is the person who just
    signed in rather than somebody debugging this module, and a sentence they
    can act on is the entire product of the error path.
    """


# --------------------------------------------------------------------------- #
# The durable record. Same two functions as the intake tool's, same reasons.


# `path=None` rather than `path=RECORD`, because a default argument binds at
# definition and the module constant is what a test repoints. The version with
# the constant in the signature read better and quietly wrote to the tracked
# file from a temp tree.
def read_record(path: Path | None = None) -> list[dict]:
    """Every entry, oldest first. Absent is empty, not an error."""
    path = path or RECORD
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines()
            if line.strip()]


def append_record(entry: dict, path: Path | None = None) -> None:
    """Append one entry. Never rewrites, never reorders, never deletes.

    A claim is dated and an observation is a moment, so editing either would be
    editing what happened rather than recording that it happened again.
    Recording again is a new line, which is the whole point of the dates.
    """
    path = path or RECORD
    with path.open("a") as handle:
        handle.write(json.dumps(entry, sort_keys=True) + "\n")


def read_captures(path: Path | None = None) -> list[dict]:
    """Every capture, oldest first. Absent names where one comes from.

    **Two spellings of the same thing, because the browser writes one of them.**
    A download from `/signed-in/` is one JSON object in a file. A file somebody
    has been appending downloads to is one object per line. Both are read, and
    neither is the correct one: what this cares about is the objects, and a
    version that took only the line-per-object form would make a person reformat
    a file before a tool would look at it, which is a transcription step with a
    text editor in it.

    An array is read too, for the person who concatenated several.
    """
    path = path or CAPTURES
    if not path.exists():
        raise Refused(
            f"no {path} to read. A capture is the file `/signed-in/` hands you "
            "after Hugging Face sends you back, and it is gitignored, so a "
            "fresh checkout has none and a claim starts with a sign-in rather "
            "than with this command. Point --captures at the download, or "
            f"move it to {path}."
        )
    text = path.read_text().strip()
    if not text:
        return []
    if text.startswith("["):
        loaded = json.loads(text)
    elif text.startswith("{") and "\n" in text.strip("{} \n"):
        # Pretty-printed, so it is one object across many lines rather than
        # many objects one to a line. Parsed whole; a file holding two
        # pretty-printed objects back to back raises here rather than being
        # guessed at, which is the right answer to bytes nobody can read
        # unambiguously.
        loaded = json.loads(text)
    else:
        loaded = [json.loads(line) for line in text.splitlines() if line.strip()]
    entries = loaded if isinstance(loaded, list) else [loaded]
    for entry in entries:
        if not isinstance(entry, dict):
            raise Refused(
                f"{path} holds a {type(entry).__name__} where a capture should "
                "be. A capture is a JSON object, and there is no reader here "
                "for anything else. Nothing was written."
            )
    return entries


# --------------------------------------------------------------------------- #
# Reading one capture, and refusing one that carries something it should not.


def refuse_credentials(value, *, where: str) -> None:
    """Walk every key. A name that reads like a credential stops the run.

    Belt and braces: the projection below copies named fields and never the
    capture itself, so a stray key could not reach a row anyway. This refuses
    before that, because the failure being guarded against is a secret in a
    public repository and the cheap check is the one that runs first.
    """
    if isinstance(value, dict):
        for key, inner in value.items():
            low = str(key).lower()
            if any(word in low for word in CREDENTIAL_WORDS):
                raise Refused(
                    f"{where} carries a key named {key!r}. A capture is read "
                    "here to make a tracked row in a public repository, and "
                    "nothing that reads like a credential is going into one. "
                    "`/signed-in/` writes no token, so a capture that "
                    "holds one came from somewhere else. Nothing was written."
                )
            refuse_credentials(inner, where=where)
    elif isinstance(value, list):
        for inner in value:
            refuse_credentials(inner, where=where)


def pick(captures: list[dict], *, at: str | None = None,
         subject: str | None = None) -> dict:
    """One capture out of the file. The most recent, unless told otherwise.

    Ambiguity is refused rather than resolved. Picking the first of several
    matches would silently claim a namespace for whichever account happened to
    sign in first, and the person running this would have no way to notice.
    """
    if not captures:
        raise Refused(
            "the capture file is empty, so there is nothing to claim from. "
            "Sign in at /signed-in/ and keep the file it hands you."
        )
    found = [c for c in captures
             if (at is None or c.get("captured_at") == at)
             and (subject is None or c.get("sub") == subject)]
    if not found:
        asked = ", ".join(filter(None, [
            f"captured_at {at}" if at else "",
            f"sub {subject}" if subject else "",
        ]))
        raise Refused(f"no capture matches {asked}. Nothing was written.")
    if (at or subject) and len(found) > 1:
        raise Refused(
            f"{len(found)} captures match, taken at "
            + ", ".join(c.get("captured_at", "?") for c in found)
            + ". Name one with --at, because picking one here would bind a "
            "namespace to whichever account this file happened to list first."
        )
    return found[-1]


def org_name(org) -> str | None:
    """What the provider called the organization, in whichever key it used.

    `schema/migrations/009` gives the row one `org` column, so a capture entry
    has to be projected onto it. The projection reads the keys the provider has
    been seen to use and takes the first that answers; it does not require a
    shape, and an entry that is a bare string is a name.
    """
    if isinstance(org, str):
        return org or None
    if isinstance(org, dict):
        for key in ("name", "preferred_username", "sub"):
            said = org.get(key)
            if isinstance(said, str) and said:
                return said
    return None


def org_role(org) -> str | None:
    """`roleInOrg` where the provider gives one, and None where it did not.

    Carried through as the string it was. A role this project has never met
    stores and renders, because a list of the roles we happen to have seen is a
    list of the ones that count.
    """
    if not isinstance(org, dict):
        return None
    for key in ("roleInOrg", "role"):
        said = org.get(key)
        if isinstance(said, str) and said:
            return said
    return None


# --------------------------------------------------------------------------- #
# The entries, which are pure functions of one capture.


def evidence_entry(kind: str, detail: str, recorded_at: str) -> dict:
    kind, detail = kind.strip(), detail.strip()
    if not kind or not detail:
        raise Refused(
            "evidence needs a kind and a detail, and this one is missing "
            "one of them. The detail is the argument somebody can disagree "
            "with, so an empty one is a claim with nothing behind it."
        )
    return {"kind": kind, "detail": detail, "recorded_at": recorded_at}


def claim_from(capture: dict, *, namespace: str, evidence: list[dict],
               is_synthetic: bool = False) -> dict:
    """One record line, built from one capture and one namespace.

    Pure, and separated from the file and the database for that reason:
    everything about the shape of a claim can be exercised without a browser,
    a provider or a person.
    """
    refuse_credentials(capture, where="the capture")
    subject = capture.get("sub")
    if not subject:
        raise Refused(
            "the capture carries no `sub`, so there is nothing to bind a claim "
            "to. Binding it to the handle instead is the one thing this must "
            "not do: handles are renameable, so the claim would either break on "
            "a rename or follow the name to whoever registers it next. Nothing "
            "was written."
        )
    when = capture.get("captured_at")
    if not when:
        raise Refused(
            "the capture carries no `captured_at`. A claim with no date is a "
            "standing rather than dated evidence, which is the one thing a "
            "claim here is not. Nothing was written."
        )
    namespace = (namespace or "").strip()
    if not namespace:
        raise Refused(
            "no namespace given. A capture says who signed in and says nothing "
            "about which namespace they are claiming, and the two are different "
            "strings on purpose."
        )
    return {
        "shape": CLAIM,
        "namespace": namespace,
        "provider": capture.get("provider"),
        "subject": subject,
        "handle": capture.get("preferred_username"),
        "claimed_at": when,
        "evidence": list(evidence),
        "derived_from": "capture",
        "is_synthetic": bool(is_synthetic),
    }


def observations_from(capture: dict, *, is_synthetic: bool = False) -> list[dict]:
    """One record line per organization the capture reported.

    **Three states, and they are three different facts**, the same three
    `/signed-in/` writes and `schema/migrations/008` describes. A list
    is what the provider said. An empty list is a real answer, that the account
    was in no organization at that moment, and it produces no rows because
    there is no observation to record. A null is that the provider said nothing
    about organizations at all, which is not the same as membership of none and
    also produces no rows.

    An entry the provider named nothing at all stops the run rather than being
    dropped: `org` is NOT NULL, so there is no row to write, and skipping it
    would lose an organization quietly.
    """
    refuse_credentials(capture, where="the capture")
    orgs = capture.get("orgs")
    if not isinstance(orgs, list):
        return []
    subject = capture.get("sub")
    if not subject:
        raise Refused(
            "the capture carries no `sub`, so an observation has no account to "
            "attach to. Nothing was written."
        )
    when = capture.get("captured_at")
    source = capture.get("userinfo_endpoint")
    if not when or not source:
        raise Refused(
            "an observation needs the moment it was taken and the endpoint that "
            "answered, and this capture is missing one of them. An observation "
            "with no account of where it came from is a stored fact again, "
            "which is what `schema/migrations/009` refuses. Nothing was written."
        )
    out = []
    for index, org in enumerate(orgs):
        name = org_name(org)
        if not name:
            raise Refused(
                f"entry {index} of the capture's `orgs` carries no name this "
                "file can read, and `org` is NOT NULL, so there is no row to "
                "write for it. Dropping it would lose an organization quietly. "
                "Nothing was written."
            )
        out.append({
            "shape": OBSERVATION,
            "provider": capture.get("provider"),
            "subject": subject,
            "org": name,
            "role": org_role(org),
            "observed_at": when,
            "source": source,
            "derived_from": "capture",
            "is_synthetic": bool(is_synthetic),
        })
    return out


# --------------------------------------------------------------------------- #
# The one function that turns an entry into rows.


def _identifier(prefix: str, *parts: str) -> str:
    """A primary key made of exactly the columns the UNIQUE is made of.

    So a duplicate is refused by both constraints rather than by one, and no id
    is ever typed by anybody. The digest is truncated because these are row
    identifiers inside one file and not commitments to anything.
    """
    digest = hashlib.sha256("\x1f".join(parts).encode()).hexdigest()
    return f"{prefix}_{digest[:24]}"


def claim_id(entry: dict) -> str:
    return _identifier("nc", CLAIM, entry["provider"], entry["subject"],
                       entry["namespace"])


def observation_id(entry: dict) -> str:
    return _identifier("nm", OBSERVATION, entry["provider"], entry["subject"],
                       entry["org"], entry["observed_at"])


def insert(conn: sqlite3.Connection, entry: dict) -> str:
    """Write one entry's rows. Returns a line describing what it wrote.

    The only place any of these three tables is written from a capture, called
    by the recording commands and by `replay` against a database that was just
    rebuilt. `artifacts/publish.py` learned this the expensive way about two
    columns and `artifacts/intake.py` about twenty; the argument is the same
    and it does not get weaker for a smaller row.

    An `UPDATE` appears nowhere in this file. A membership is a look, so a
    second look is a second row, and the way that property gets lost is
    somebody writing the convenient version of this function.
    """
    shape = entry.get("shape")
    synthetic = 1 if entry.get("is_synthetic") else 0
    if shape == CLAIM:
        row = claim_id(entry)
        conn.execute(
            "INSERT INTO namespace_claim (id,namespace,provider,subject,handle,"
            "claimed_at,is_synthetic) VALUES (?,?,?,?,?,?,?)",
            (row, entry["namespace"], entry["provider"], entry["subject"],
             entry.get("handle"), entry["claimed_at"], synthetic),
        )
        conn.executemany(
            "INSERT INTO namespace_claim_evidence (claim_id,kind,detail,"
            "recorded_at) VALUES (?,?,?,?)",
            [(row, e["kind"], e["detail"], e["recorded_at"])
             for e in entry.get("evidence") or []],
        )
        conn.commit()
        return (f"{entry['namespace']} claimed by {entry['provider']}:"
                f"{entry['subject']} on {entry['claimed_at']}")
    if shape == OBSERVATION:
        conn.execute(
            "INSERT INTO namespace_membership_observation (id,provider,subject,"
            "org,role,observed_at,source,is_synthetic) VALUES (?,?,?,?,?,?,?,?)",
            (observation_id(entry), entry["provider"], entry["subject"],
             entry["org"], entry.get("role"), entry["observed_at"],
             entry["source"], synthetic),
        )
        conn.commit()
        return (f"{entry['org']} observed for {entry['provider']}:"
                f"{entry['subject']} at {entry['observed_at']}")
    raise Refused(
        f"a record line carries shape {shape!r}, and there is no reader for it "
        "here, so it cannot be turned into rows and nothing was written. That "
        "is a refusal to write what cannot be verified rather than a statement "
        "that the shape is illegitimate: a newer shape needs a reader in this "
        f"file. The two this version reads are {CLAIM} and {OBSERVATION}."
    )


def replay(conn: sqlite3.Connection, path: Path | None = None) -> list[str]:
    """Reinsert every recorded entry. Returns a line per row written.

    For the rebuild: `make site` drops the database, and none of this is in
    either seed script any more. An entry already present is a stop rather than
    a skip, because a database holding some of the record and not the rest is
    the state worth finding out about.
    """
    path = path or RECORD
    written = []
    for entry in read_record(path):
        try:
            written.append(insert(conn, entry))
        except sqlite3.IntegrityError as clash:
            raise Refused(
                f"a line in {path.name} is already in the database ({clash}). "
                "The record is append-only and both the id and the unique "
                "constraint are made of the same columns, so this is a database "
                "that was seeded twice rather than a record that is wrong."
            ) from clash
    return written


# --------------------------------------------------------------------------- #
# The commands.


def parse_evidence(given: list[str] | None) -> list[tuple[str, str]]:
    """`kind=detail`, or `kind=@file` when the detail is a paragraph.

    The file form exists because evidence is prose and a paragraph typed into a
    shell invocation is a paragraph with the line breaks eaten. Nothing about
    which kinds are allowed: the left side is carried through as written.
    """
    out = []
    for raw in given or []:
        if "=" not in raw:
            raise Refused(
                f"--evidence {raw!r} is not `kind=detail`. The kind is any "
                "string; `repo`, `doi` and `human-decision` are what this "
                "project has used and nothing enforces a set."
            )
        kind, detail = raw.split("=", 1)
        if detail.startswith("@"):
            source = Path(detail[1:])
            if not source.exists():
                raise Refused(f"--evidence {kind}=@{source} names no file")
            detail = source.read_text()
        out.append((kind, detail))
    return out


def cmd_record(args, conn) -> int:
    """One capture plus one namespace, into the record and into the rows."""
    capture = pick(read_captures(args.captures), at=args.at,
                   subject=args.subject)
    when = capture["captured_at"]
    entries = [claim_from(
        capture,
        namespace=args.namespace,
        evidence=[evidence_entry(kind, detail, args.recorded_at or when)
                  for kind, detail in parse_evidence(args.evidence)],
    )]
    if not args.claim_only:
        entries += observations_from(capture)

    for line in write(conn, entries, args.record):
        print(f"  {line}")
    print()
    print("the record is tracked and the capture is not. Commit the record.")
    return 0


def cmd_observe(args, conn) -> int:
    """A second look at the same account, beside the last one rather than over it."""
    capture = pick(read_captures(args.captures), at=args.at,
                   subject=args.subject)
    entries = observations_from(capture)
    if not entries:
        print("the capture reported no organization, so there is nothing to "
              "observe. That is an answer rather than a failure: see the three "
              "states in `schema/migrations/008_absence_reason.sql`.")
        return 0
    for line in write(conn, entries, args.record):
        print(f"  {line}")
    return 0


def write(conn: sqlite3.Connection, entries: list[dict],
          path: Path | None) -> list[str]:
    """Insert each entry, then append it, in that order and one at a time.

    **The row goes in first, and the order is the whole argument.** A row with
    no record line is lost on the next `make site`, which is a rerun of one
    command. A record line the database refuses is permanent: the record is
    append-only, `replay` stops on a duplicate, and every build from then on
    stops with it. So the failure that is recoverable is the one this takes.

    One at a time rather than all the inserts then all the appends, so a stop
    halfway leaves the record and the database agreeing about everything before
    it.
    """
    written = []
    for entry in entries:
        try:
            written.append(insert(conn, entry))
        except sqlite3.IntegrityError as clash:
            raise Refused(
                f"the database already holds this one ({clash}), so nothing "
                "was appended to the record for it. An account claims one "
                "namespace once and an observation is keyed on its own "
                "timestamp, so this is a repeat rather than a second look."
            ) from clash
        append_record(entry, path)
    return written


def cmd_replay(args, conn) -> int:
    for line in replay(conn, args.record):
        print(f"  {line}")
    return 0


def cmd_show(args, _conn) -> int:
    """Read the record back. Entries are dated, so they are listed as written."""
    entries = read_record(args.record)
    if not entries:
        print("no claims recorded")
        return 0
    for entry in entries:
        if entry.get("shape") == CLAIM:
            print(f"{entry['claimed_at']}  claim  {entry['namespace']}"
                  f"  <- {entry['provider']}:{entry['subject']}"
                  f"  ({entry.get('handle') or 'no handle recorded'})")
            for e in entry.get("evidence") or []:
                print(f"    {e['kind']}  {e['detail'][:70]}")
        elif entry.get("shape") == OBSERVATION:
            print(f"{entry['observed_at']}  member of {entry['org']}"
                  f"  as {entry.get('role') or 'a role the provider did not state'}"
                  f"  per {entry['source']}")
        else:
            print(f"?  a line with shape {entry.get('shape')!r}, which this "
                  "version has no reader for")
    return 0


def cmd_adopt(args, conn) -> int:
    """Lift rows that already exist into the record, once.

    **This is not how a claim is made.** It exists because the rows came first:
    the real claim in this corpus was typed into `artifacts/seed.py` before
    there was a record for it to come from, and the capture behind it is
    gitignored and no longer in the tree, so re-deriving it from the capture is
    not available and signing in again would date the claim to today rather
    than to when it was made.

    So this derives the record from the file that holds the rows, which is still
    a script reading a file rather than a person reading a screen, and marks
    every entry `derived_from: database-row` so the record says which of the two
    it was. Synthetic rows are left alone: a fabricated claim in the real
    record would be one that survives a rebuild and reads as somebody's account.
    """
    conn.row_factory = sqlite3.Row
    already = read_record(args.record)
    have = {json.dumps(_key_of(e), sort_keys=True) for e in already}
    new: list[dict] = []

    for row in conn.execute(
        "SELECT * FROM namespace_claim WHERE is_synthetic = 0"
    ).fetchall():
        entry = {
            "shape": CLAIM,
            "namespace": row["namespace"],
            "provider": row["provider"],
            "subject": row["subject"],
            "handle": row["handle"],
            "claimed_at": row["claimed_at"],
            "evidence": [
                {"kind": e["kind"], "detail": e["detail"],
                 "recorded_at": e["recorded_at"]}
                for e in conn.execute(
                    "SELECT kind, detail, recorded_at FROM "
                    "namespace_claim_evidence WHERE claim_id = ?", (row["id"],)
                ).fetchall()
            ],
            "derived_from": "database-row",
            "is_synthetic": False,
        }
        if json.dumps(_key_of(entry), sort_keys=True) not in have:
            new.append(entry)

    for row in conn.execute(
        "SELECT * FROM namespace_membership_observation WHERE is_synthetic = 0"
    ).fetchall():
        entry = {
            "shape": OBSERVATION,
            "provider": row["provider"],
            "subject": row["subject"],
            "org": row["org"],
            "role": row["role"],
            "observed_at": row["observed_at"],
            "source": row["source"],
            "derived_from": "database-row",
            "is_synthetic": False,
        }
        if json.dumps(_key_of(entry), sort_keys=True) not in have:
            new.append(entry)

    if not new:
        print("the record already holds every real row in this database")
        return 0
    for entry in new:
        append_record(entry, args.record)
        print(f"  adopted  {entry['shape'].rsplit('/', 1)[-1]}  "
              f"{entry.get('namespace') or entry.get('org')}")
    print()
    print("nothing was written to the database: these rows were already in it. "
          "Drop it and rebuild to check that the record reproduces them.")
    return 0


def _key_of(entry: dict) -> list[str]:
    """What makes an entry the same entry, which is what its id is made of."""
    if entry.get("shape") == CLAIM:
        return [CLAIM, entry["provider"], entry["subject"], entry["namespace"]]
    if entry.get("shape") == OBSERVATION:
        return [OBSERVATION, entry["provider"], entry["subject"], entry["org"],
                entry["observed_at"]]
    return [str(entry.get("shape"))]


# --------------------------------------------------------------------------- #


def main(argv: list[str] | None = None) -> int:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--db", default=str(ROOT / "registry.db"))
    common.add_argument("--record", type=Path, default=None,
                        help=f"default {RECORD.relative_to(ROOT)}, which is tracked")

    from_capture = argparse.ArgumentParser(add_help=False)
    from_capture.add_argument(
        "--captures", type=Path, default=None,
        help=f"default {CAPTURES.relative_to(ROOT)}, which is gitignored")
    from_capture.add_argument(
        "--at", help="the `captured_at` of the capture to read. Default is the "
                     "most recent line in the file.")
    from_capture.add_argument(
        "--subject", help="the `sub` of the capture to read, when the file "
                          "holds sign-ins by more than one account")

    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="command", required=True)

    record = sub.add_parser("record", parents=[common, from_capture],
                            help="a capture plus a namespace becomes a claim")
    record.add_argument("--namespace", required=True,
                        help="the `author` string being claimed. Not in the "
                             "capture, because the provider has no opinion "
                             "about it.")
    record.add_argument("--evidence", action="append",
                        help="kind=detail, or kind=@file. Repeatable. Any kind.")
    record.add_argument("--recorded-at", dest="recorded_at",
                        help="when the evidence was recorded. Defaults to the "
                             "capture's own timestamp.")
    record.add_argument("--claim-only", action="store_true",
                        help="write the claim and not the memberships the "
                             "capture reported")
    record.set_defaults(fn=cmd_record, needs_db=True)

    observe = sub.add_parser("observe", parents=[common, from_capture],
                             help="a later look, appended beside the last one")
    observe.set_defaults(fn=cmd_observe, needs_db=True)

    replay_cmd = sub.add_parser("replay", parents=[common],
                                help="write the whole record into a database")
    replay_cmd.set_defaults(fn=cmd_replay, needs_db=True)

    show = sub.add_parser("show", parents=[common], help="read the record back")
    # No database. Reading the record back is a question about a file, and a
    # `show` that opens sqlite creates an empty database on a machine that has
    # none, which is a build artifact conjured by a read.
    show.set_defaults(fn=cmd_show, needs_db=False)

    adopt = sub.add_parser("adopt", parents=[common],
                           help="lift real rows that predate the record into it")
    adopt.set_defaults(fn=cmd_adopt, needs_db=True)

    args = ap.parse_args(argv)
    try:
        return args.fn(args, opened(Path(args.db)) if args.needs_db else None)
    except Refused as refused:
        raise SystemExit(str(refused)) from refused


def opened(path: Path) -> sqlite3.Connection:
    """A database that already has the schema, or a sentence saying it does not.

    Migrating here instead would let a mistyped `--db` conjure a database and
    then report success at having written a claim into it, which is a worse
    answer than the traceback this replaces.
    """
    conn = db.connect(path)
    got = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        ("namespace_claim",),
    ).fetchone()
    if not got:
        raise Refused(
            f"{path} has no `namespace_claim` table, so there is nowhere to "
            "write. Build the corpus first with `artifacts/seed.py`, "
            "or point --db at the one you meant. Nothing "
            "was written, here or to the record."
        )
    return conn


if __name__ == "__main__":
    raise SystemExit(main())
