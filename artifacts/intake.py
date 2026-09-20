"""A form on 127.0.0.1 that gets one artifact into the corpus, and its rows with it.

Premise, restated because a premise stated in one document gets violated in every
other one: **plurality is the product; the registry never designates, consumers
pin, visibly.** Nothing here ranks, scores, approves or filters a submission. Every
field it collects is open, the suggestions beside them are read out of what this
corpus already holds, and the only things this refuses are bytes it cannot read
without running them and rows the schema will not take.

**The form is not the submission route, and the binding is what makes that
true.** It listens on 127.0.0.1 and on nothing else. There is no `--host`. There
is a submission route now, and it is the published page plus the table it posts
to rather than anything in this process; what must not exist here is a listener
anybody but the operator can reach, because this one writes the tracked record
directly and answers to no session. `astro.config.mjs` stays `output: "static"`
for a related reason in a different register, and its comment says it: "a build
that emits files cannot drift into being a public surface the way a running
process can". This is a running process, so it carries the constraint in code
rather than in a build flag: the loopback bind, a per-run token in the URL, a
`Host` header check and an `Origin` check, because a browser on this machine
will happily post to 127.0.0.1 on behalf of a page the operator did not open.
`tests/test_intake.py` holds all four.

**Two modes, one end state.** Both finish as a row pointing at a pinned remote,
and neither writes `served_repo`.

    link    paste a repo, a commit and a path, on any host. The bytes are
            fetched into a throwaway cache, checked, and dropped. What is kept
            is the pointer.
    bytes   drop a file. It is converted to safetensors and checked outside this
            repository, pushed to the author's own namespace through
            `artifacts/publish.py upload`, and the pin is recorded. The staged
            file is deleted. Bytes never rest here.

Above `BYTES_CAP` the second mode refuses, and the refusal says what it is: a cap
on this form, on this machine, because it holds the whole file in memory to check
it before anything is written. It is not a statement about the artifact, and link
mode takes any size.

**Nothing in this file decides what an artifact may be.** `controlbun.ingest` owns
the question of which bytes can be read without executing them and answers it with
an open converter set. `controlbun.artifact` owns the comparison between a claim and
the bytes. `controlbun.fetch` owns the rule that a pin is a commit. This file owns a
form, a socket and two INSERTs, and every rule it appears to apply is one of those
three being called.

**`artifacts/intake.jsonl` is the durable record, and the reason is the reason
`published.json` exists.** `make site` deletes `registry.db` and rebuilds it from
`artifacts/seed.py`, so a row written only into the
database is gone on the next build. The record is append-only and tracked; `insert`
is the one function that turns an entry into rows, and both the live write and
`replay` call it, so the two cannot come apart. Nothing in the `Makefile` calls
`replay` yet: the falsifier fails a row whose `artifact_path` has no file on disk,
and every row this writes is one of those, so wiring the replay into the build
needs that check to learn that a pinned remote with no local copy is a state.
That is a decision for the author, not something to slip in here.

**A third way in, since 2026-09-20: a submission built in a browser and sent.**
Somebody signs in at `/signed-in/`, goes to `/submit/`, and either fills in the
same contract fields this form collects or pastes what their coding agent
produced. The record lands in `pending_submission` on the Supabase project, over
their own session, with `account`, `subject` and `handle` stamped by Postgres
out of the verified session; `schema/supabase/001` carries that argument and the
policy that enforces it. `pull` reads those rows with the secret key and hands
each one to `take`, which goes down the link path: the bytes are fetched at the
pin and handed to `controlbun.artifact` here, so nothing the submitter says
about the tensor is taken on trust and nothing about it was computed in their
browser. `take` is also what reads a file somebody mailed, so there is one
function that writes a submission and not two.

**The paste is parsed here and nowhere else.** `agent_handoff.parse` is the one
implementation of it, in Python, and `/submit/` posts the text as it arrived
rather than checking any part of it first. What that costs is a real difference
from the field route and the page says it plainly: a mistake in a paste is not
found as somebody types, it is found when the author pulls. What it buys is that
there is no second parser to drift from this one, which is the failure this
repository has hit most often.

**On a pull, the stamped identity is the one that counts.** The row's `subject`
and `handle` came through the insert policy; the record's copies came from a
browser. `stamped` substitutes the first for the second and returns the
disagreement rather than swallowing it, because a handle renamed between the
capture and the session is a real fact about a real person and preferring one
copy silently would hide it.

**`pending_submission` is not a queue.** Nothing is approved, rejected, ranked,
counted or ordered, and `taken_at` means read in rather than accepted. There is
no review step and nothing to approve: the namespace is the handle the provider
reported, so there is no question for a reviewer to answer, and `DECISIONS.md`
2026-09-17 records why a review step with no stated rule fills with the
reviewer's taste. What `take` refuses is what this file already refuses: a shape
with no reader, bytes that do not resolve, a field given both a value and a
reason for having none. A refused row keeps `taken_at` null and stays where it
is.

    .venv/bin/python artifacts/intake.py serve
    .venv/bin/python artifacts/intake.py prompt
    .venv/bin/python artifacts/intake.py take submission-someone-label-....json
    SUPABASE_SECRET_KEY=... .venv/bin/python artifacts/intake.py pull --dry-run
    SUPABASE_SECRET_KEY=... .venv/bin/python artifacts/intake.py pull
    .venv/bin/python artifacts/intake.py replay
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import os
import secrets
import shutil
import sqlite3
import sys
import tempfile
import threading
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
from dataclasses import dataclass
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(HERE))

from controlbun import artifact, db, fetch, ingest  # noqa: E402
# Aliased because `ref` is a local name all over this module, for the string one
# entry resolves to. This is the module that knows how to build it.
from controlbun import ref as registry_ref  # noqa: E402
import agent_handoff  # noqa: E402
import publish  # noqa: E402
import source  # noqa: E402

# Loopback, and not a default. There is no flag that changes this and adding one
# would be the whole argument in the docstring, undone in a line.
HOST = "127.0.0.1"

# The whole file is held in memory while it is digested, sniffed, converted and
# rechecked, which is the order that makes the check worth anything. Half a
# gigabyte of that is a thing a laptop does without complaint and two is not.
BYTES_CAP = 500 * 1024 * 1024

RECORD = HERE / "intake.jsonl"

# Where the built site reads the agent prompt from. Generated by the `prompt`
# subcommand during `make site` and tracked, the same arrangement
# `astro/src/data/controlbun.json` has: the page renders what Python produced
# rather than carrying a second copy of a document that changes whenever a
# field does.
PROMPT_DATA = ROOT / "astro" / "src" / "data" / "agent-prompt.json"


class Refused(ValueError):
    """Something this form will not do, with the reason already in the message.

    One class for every refusal here, because the reader is an operator with a
    file in hand rather than somebody debugging this module, and a sentence they
    can act on is the entire product of the error path.
    """


# --------------------------------------------------------------------------- #
# The durable record, and the one function that turns an entry into rows.


# `path=None` rather than `path=RECORD` on all three, because a default
# argument binds at definition and the module constant is what a test, or a
# second corpus, repoints. The version with the constant in the signature read
# better and quietly wrote to the tracked file from a temp tree.
def read_record(path: Path | None = None) -> list[dict]:
    """Every entry, oldest first. Absent is empty, not an error."""
    path = path or RECORD
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def append_record(entry: dict, path: Path | None = None) -> None:
    """Append one entry. Never rewrites, never reorders, never deletes.

    A submission is immutable once written and this file is the record of the
    writing, so editing it would be editing history rather than the corpus.
    Correcting something means a new version, which is a new entry.
    """
    with (path or RECORD).open("a") as handle:
        handle.write(json.dumps(entry, sort_keys=True) + "\n")


def absences_of(entry: dict) -> dict[str, str]:
    """The declared absences on one entry, keyed by the column each is about.

    Absent from an entry written before `schema/migrations/008`, and empty on
    most of the ones written after it. Neither is a lesser record: an absence
    with nobody's account of it is the ordinary case and renders exactly as it
    rendered before the column existed.

    Read through one function because three callers ask the same question of a
    key that is optional, and `entry["absent"]` on a 2026-09-18 line is a
    KeyError rather than an empty answer.
    """
    return {field: reason for field, reason in (entry.get("absent") or {}).items()
            if str(reason).strip()}


def contradictions(entry: dict) -> list[str]:
    """Fields this entry gives both a value and a reason for having none.

    Two claims by one author about one field, and nothing here can tell which
    was meant. Naming them is all this does; refusing is `insert`'s job and the
    refusal is the whole point, because either way of resolving it deletes one
    of somebody's two sentences without saying so.

    A reason whose field is not a column in the row cannot contradict anything,
    so it is not looked at. That is the open half: the field side of an absence
    takes any string, and this asks about the ones the row happens to hold
    rather than about a list of the ones it may hold.
    """
    iv = entry["intervention"]
    return sorted(
        field for field in absences_of(entry)
        if field in iv and iv[field] is not None and str(iv[field]).strip() != ""
    )


def insert(conn: sqlite3.Connection, entry: dict) -> None:
    """Write one entry's submission and intervention rows.

    The only place either row is made here, called by the live write and by
    `replay` against a database that was just rebuilt. `artifacts/publish.py`
    learned this the expensive way about the two pin columns; the same argument
    applies to the whole row, and harder, because there are twenty columns to
    get out of step rather than two.

    `artifact_repo` and `artifact_commit` go in the `INSERT` rather than through
    `apply_pins`, and the difference is that `seed.py` does not know the pin when
    it inserts and this does: the pin is what the form just checked, and it is
    the reason the row is being written at all.

    **A value and a reason for having none is refused here and nowhere else.**
    Here because this is where it is written, and both the live write and
    `replay` come through it, so a hand-corrected record cannot get a
    contradiction past the rebuild. Refused rather than resolved: preferring the
    value would drop the author's sentence and preferring the sentence would
    drop the author's value, and both happen silently while the entry still
    reads correct to whoever wrote it.
    """
    iv = entry["intervention"]
    both = contradictions(entry)
    if both:
        raise Refused(
            f"{', '.join(both)} came back with a value and a reason for having "
            "none. Those are two claims about one field and nothing here can "
            f"tell which was meant, so neither is written. Drop whichever is "
            "wrong from the record and replay."
        )
    # The model is part of what the submission is since `schema/migrations/010`,
    # and it is read off the intervention the form just filled in rather than
    # asked for twice. One field, one answer: the form has exactly one
    # `model_id` box and a second copy on the submission side would be a second
    # place for it to disagree with itself.
    conn.execute(
        "INSERT INTO submission (author,model_id,label,version,definition,"
        "created_at,is_synthetic) VALUES (?,?,?,?,?,?,0)",
        (entry["author"], iv.get("model_id"), entry["label"], entry["version"],
         entry["definition"], entry["created_at"]),
    )
    columns = (
        "id", "kind", "model_revision", "layer", "layer_convention",
        "hook_point", "chat_template_hash", "shape", "dtype", "l2_norm",
        "activation_norm", "coeff_low", "coeff_high", "steering_position",
        "license_status", "artifact_repo", "artifact_commit", "artifact_host",
        "artifact_url_template", "artifact_path", "artifact_sha256",
    )
    conn.execute(
        "INSERT INTO intervention (author,model_id,label,version,is_synthetic,"
        + ",".join(columns) + ") VALUES (?,?,?,?,0," + ",".join("?" * len(columns)) + ")",
        (entry["author"], iv.get("model_id"), entry["label"], entry["version"],
         *(iv.get(c) for c in columns)),
    )
    # One row per field somebody accounted for, and no rows at all is the
    # ordinary case. `executemany` over an empty sequence writes nothing, so
    # there is no branch here saying an entry with no reasons is different.
    conn.executemany(
        "INSERT INTO intervention_absence (intervention_id,field,reason)"
        " VALUES (?,?,?)",
        [(iv["id"], field, reason)
         for field, reason in sorted(absences_of(entry).items())],
    )
    conn.commit()


def replay(conn: sqlite3.Connection, path: Path | None = None) -> list[str]:
    """Reinsert every recorded entry. Returns the refs it wrote.

    For the rebuild: `make site` drops the database, and these rows are not in
    either seed script. An entry already present is a stop rather than a skip,
    because a database that holds some of the record and not the rest is the
    state worth finding out about.
    """
    path = path or RECORD
    written = []
    for entry in read_record(path):
        ref = registry_ref.format(
            entry["author"], entry["intervention"].get("model_id"),
            entry["label"], entry["version"],
        )
        try:
            insert(conn, entry)
        except sqlite3.IntegrityError as clash:
            raise Refused(
                f"{ref} is in {path.name} and the database already holds it "
                f"({clash}). The record is append-only and a submission is "
                "immutable, so this is a database that was seeded twice rather "
                "than a record that is wrong."
            ) from clash
        written.append(ref)
    return written


# --------------------------------------------------------------------------- #
# What was actually read out of the bytes.


@dataclass(frozen=True)
class Checked:
    """The verification, kept so the page can show it rather than summarize it.

    `staged` is the converted file for bytes mode and `None` for link mode, which
    is the whole structural difference between the two: one has bytes in hand that
    have to go somewhere, and the other has a pointer at bytes that are already
    somewhere. Everything below it is the same in both.
    """

    mode: str
    where: str
    facts: artifact.Facts
    tensor_name: str | None
    header: dict[str, str]
    stated: dict[str, str]
    staged: Path | None = None
    # The directory to delete afterwards, and not `staged.parent`, which is a
    # subdirectory of it whenever the artifact path has one. That spelling left
    # a staging tree per upload behind and the test that noticed was the one
    # counting temporary directories rather than the one about bytes.
    staging_root: Path | None = None
    repo: str | None = None
    commit: str | None = None
    path: str | None = None
    # Which host that repo is on and how the four fields become a URL. Both
    # empty is the ordinary case and means the Hub, which is where a row that
    # records neither has always resolved. See `schema/migrations/007`.
    host: str | None = None
    url_template: str | None = None

    def display(self) -> list[tuple[str, str]]:
        """Pairs for the page. Absent is a sentence, never a blank and never a 0."""
        f = self.facts
        return [
            ("came from", self.where),
            ("bytes", f"{f.size}" if f.size is not None else "not counted"),
            ("sha256", f.sha256 or "not derived"),
            ("tensor", self.tensor_name or "unnamed"),
            ("shape", f.shape or "not derived"),
            ("dtype", f.dtype or "not derived"),
            ("L2 norm", repr(f.l2_norm) if f.l2_norm is not None else "not derived"),
            ("header in the file",
             ", ".join(f"{k}={v}" for k, v in sorted(self.header.items()))
             or "the file carries no header"),
            ("what you stated",
             ", ".join(f"{k}={v}" for k, v in sorted(self.stated.items()))
             + (" and the bytes agree with all of it" if self.stated else "")
             or "nothing, so nothing was contradicted; the values above are "
                "derived from the bytes"),
        ]


def _claim(stated: dict[str, str]) -> artifact.Claim:
    """What the operator said about the bytes, as the one type that gets compared.

    Every field optional, which is `controlbun.artifact.Claim`'s design and not a
    concession: somebody who says nothing about a norm has not made a wrong claim
    about it, and the row records what the bytes say instead.
    """
    return artifact.Claim(
        shape=stated.get("shape") or None,
        dtype=stated.get("dtype") or None,
        l2_norm=_number("l2_norm", stated.get("l2_norm")),
        sha256=stated.get("sha256") or None,
    )


def check_link(repo: str, commit: str, path: str, stated: dict[str, str],
               host: str = "", url_template: str = "") -> Checked:
    """Fetch a pinned file, check it, keep the pointer and drop the bytes.

    Through `fetch.resolve`, which is the consumer path verbatim: what an
    operator wants confirmed is that `client.load` will get these bytes on a
    machine with no checkout, and the way to confirm that is to take the same
    branch it takes. The cache is swapped for a throwaway first, so this is a
    real download rather than a reread and so nothing is left behind. That is
    `artifacts/publish.py verify`'s trick and the reason is the same one.

    `host` and `url_template` are both optional and both empty is the ordinary
    case. Empty means the Hub, which is where a row recording neither has always
    resolved, and nothing here fills them in: a host written onto a row nobody
    stated one for would be a provenance claim that reads like a checked fact.
    Nothing here validates either, either. Which hosts exist and what their URLs
    look like is not this form's question, and the refusals that do apply are
    `controlbun.fetch`'s: forty hex characters, a commit that survives into the
    URL, and a scheme a fetch can happen over.
    """
    commit = fetch.commit_sha(commit)
    if not path:
        raise Refused(
            "no path inside the repo, so there is nothing at that commit to "
            "fetch. A repo and a commit name a tree, not a file."
        )
    # `local_path` on the repository root, only to refuse a traversal. The value
    # is going into `artifact_path`, which four other callers resolve against
    # disk, and a row is the wrong place to find out that one of them will not.
    artifact.local_path(path, root=ROOT)

    # The URL this is about to fetch, built by the same function `fetch` builds
    # it with rather than described a second time here. Worth computing before
    # the download for two reasons: a template that cannot be formatted, or that
    # loses the commit, is refused before a byte moves, and the operator gets
    # the exact URL on the page instead of a summary of it.
    default_host, default_template = fetch.hub_pin()
    fetched = fetch.pinned_url(
        host=host or default_host,
        repo=repo,
        commit=commit,
        path=path,
        url_template=url_template or default_template,
    )

    with tempfile.TemporaryDirectory(prefix="registry-intake-") as tmp:
        # Serialized by the caller's lock: this is a module global in
        # `controlbun.fetch` and two requests swapping it at once would restore
        # each other's value.
        was, fetch.CACHE = fetch.CACHE, Path(tmp)
        try:
            blob = fetch.resolve(artifact_path=path, artifact_repo=repo,
                                 artifact_commit=commit,
                                 artifact_host=host or None,
                                 artifact_url_template=url_template or None)
        finally:
            fetch.CACHE = was

    subject = f"{repo}@{commit[:12]}:{path}"
    try:
        facts = artifact.confirmed(blob, _claim(stated), subject=subject)
    except artifact.MismatchedArtifact:
        raise
    except Exception as unreadable:
        raise Refused(
            f"{subject} came back as {len(blob)} bytes that do not read as "
            f"safetensors ({unreadable}). Link mode records a pointer the "
            "client will fetch and parse for itself, so what sits at that "
            "commit has to be what the client reads. Nothing converts it here, "
            "because then the row would point at one file and describe another. "
            "Bytes mode converts, and publishes what it converted."
        ) from unreadable

    return Checked(
        mode="link",
        where=f"{host or fetch.hub_pin()[0]}/{repo} at {commit}, path {path}, "
              f"fetched from {fetched}. Checked and not kept: what this records "
              "is the pointer.",
        facts=facts,
        tensor_name=_tensor_name(blob),
        header=artifact.metadata_of(blob),
        stated={k: v for k, v in stated.items() if v},
        repo=repo, commit=commit, path=path,
        host=host or None, url_template=url_template or None,
    )


def _said_the_input_digest(apart: Exception, blob: bytes,
                           stated: dict[str, str]) -> Exception:
    """The digest disagreement that is a header rewrite, told apart from the rest.

    `artifact.disagreements` is right for the read path it was written for: a
    pinned artifact whose bytes no longer hash to the record means one of the
    two moved, and that is alarming. On this path it is almost never that. The
    author states the digest of the file they exported, `ingest` rewrites the
    header with its keys sorted so the bytes reproduce, and the file it writes
    therefore hashes to something else. Same tensor, different byte order.

    Detected rather than assumed: the claim is compared against the bytes that
    came in, and only a claim that matches those exactly gets this sentence.
    Anything else keeps the original, because a digest that matches neither
    side is the case the original message is about.
    """
    if hashlib.sha256(blob).hexdigest() != (stated.get("sha256") or ""):
        return apart
    return Refused(
        "that sha256 is the digest of the file you handed over, and this tool "
        "rewrites the header with its keys sorted before it records anything, "
        "so the file it wrote hashes to something else. safetensors seeds its "
        "header order per process, and a file that does not reproduce byte for "
        "byte would make every digest in this registry meaningless, which is "
        "why the rewrite happens rather than being skipped for a file that "
        "arrives already sorted.\n\n"
        "The tensor is the same. Only the byte order of the header moved.\n\n"
        "Clear the sha256 field and the row records what the written file "
        "hashes to, which is the digest anybody fetching it later will "
        "compute. Stating nothing here is not a wrong claim."
    )


def check_bytes(blob: bytes, filename: str, path: str,
                stated: dict[str, str], tensor: str = "") -> Checked:
    """Convert and check a dropped file, outside this repository.

    `root=` points `controlbun.ingest` at a temporary directory, so the checked
    safetensors lands there rather than in the tree. The containment rule still
    applies inside it, which is why the argument is a root and not a bypass: a
    `path` with a `..` in it is refused against the staging directory exactly as
    it would be against the repository.

    Everything about which bytes are readable is `controlbun.ingest`'s, including
    the refusals. Nothing is re-decided here.

    `tensor` is empty for a file holding one array, which is most of them. A
    file holding several is refused by `ingest.one_array` in a message that
    names them all, and naming one back here is how the author says which is
    the artifact. Empty stays the default rather than picking for them: a form
    that guessed would be a form that silently published whichever tensor the
    format happened to serialize first.
    """
    if not path:
        raise Refused(
            "no artifact path, so there is nowhere to put this in the repo it "
            "is going to. `fetch.resolve` hands one path field to the remote, "
            "so the path inside the Hub repo and the row's `artifact_path` are "
            "the same string or the fetch is a 404."
        )
    staging = Path(tempfile.mkdtemp(prefix="registry-intake-"))
    try:
        got = ingest.ingest(
            ingest.LocalBytes(
                blob,
                origin=f"{filename}, a local file dropped into the intake form",
            ),
            out=path,
            subject=f"{filename} -> {path}",
            claim=_claim(stated),
            payload=ingest.named_array(tensor) if tensor else None,
            root=staging,
        )
    except artifact.MismatchedArtifact as apart:
        shutil.rmtree(staging, ignore_errors=True)
        raise _said_the_input_digest(apart, blob, stated) from apart
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    return Checked(
        mode="bytes",
        where=f"{filename}, {len(blob)} bytes read from this machine, converted "
              f"to safetensors and checked in {staging}. Nothing was written "
              "into the repository and nothing has been uploaded yet.",
        facts=got.facts,
        tensor_name=_tensor_name(artifact.header_of(got.path)),
        header=got.header,
        stated={k: v for k, v in stated.items() if v},
        staged=got.path,
        staging_root=staging,
        path=path,
    )


def _tensor_name(blob: bytes) -> str | None:
    """Whatever the author called their tensor, off the header, for display only.

    `None` when the header will not read, because this is shown next to the
    facts and nothing turns on it. What does turn on the file being readable is
    `artifact.confirmed`, which has already run by the time this is called.
    """
    try:
        names = artifact.tensor_names(blob)
    except Exception:
        return None
    return names[0] if len(names) == 1 else None


# --------------------------------------------------------------------------- #
# Turning a form into an entry.


def _number(field: str, raw: str | None) -> float | None:
    if raw is None or str(raw).strip() == "":
        return None
    try:
        return float(raw)
    except ValueError:
        raise Refused(
            f"{field} is stored as a number and {raw!r} is not one. Leave it "
            "empty if it was never measured: the column is nullable and an "
            "absence records as an absence."
        ) from None


def _integer(field: str, raw: str | None) -> int:
    if raw is None or str(raw).strip() == "":
        raise Refused(
            f"{field} has no value and the schema stores it as an integer that "
            "cannot be absent. A hook that is not at a layer is a kind of "
            "artifact this column cannot describe, which is worth saying out "
            "loud rather than filling with a zero."
        )
    try:
        return int(str(raw).strip())
    except ValueError:
        raise Refused(f"{field} is stored as an integer and {raw!r} is not one.") from None


def _text(field: str, raw: str | None, *, why: str) -> str:
    value = (raw or "").strip()
    if not value:
        raise Refused(f"{field} is empty. {why}")
    return value


def entry_from(form: dict[str, str], checked: Checked, *,
               repo: str, commit: str,
               host: str | None = None, url_template: str | None = None,
               absent: dict[str, str] | None = None) -> dict:
    """One form submission as the record line that will be replayed forever.

    The tensor facts come off `checked` and never off the form, because they are
    what the bytes say. Where the operator stated one, `artifact.confirmed` has
    already kept the stated value and proved the bytes agree with it, which is
    `_keep_the_claim`'s whole argument: a citation the bytes confirm is worth
    more than a number derived from the bytes it is compared against.

    `absent` is the other half of that: what was looked for and is not there,
    with the account of why. It sits beside `intervention` rather than inside
    it because the columns it names are the intervention's and a key that is
    both a column and a map of columns is a shape nobody reads twice the same
    way. Empty is normal and is not a degraded record.
    """
    f = checked.facts
    author = _text("author", form.get("author"),
                   why="A namespace with nobody in it cannot be claimed against.")
    label = _text("label", form.get("label"),
                  why="The label is the thing other people will disagree with you "
                      "about, and a bare one is a view across everyone claiming it.")
    version = _text("version", form.get("version"),
                    why="`author/label@version` resolves to one frozen submission "
                        "forever, so there has to be a version to freeze.")
    return {
        "recorded_at": _now(),
        "mode": checked.mode,
        "author": author,
        "label": label,
        "version": version,
        # Whatever came back, with the blank ones dropped and nothing added.
        # No field name is checked against a list here, because there is no
        # list: a reason about a field this row does not hold is somebody
        # explaining something, and the only thing it cannot do is contradict a
        # value, which `contradictions` asks about rather than asserts.
        "absent": {field: str(reason).strip()
                   for field, reason in (absent or {}).items()
                   if str(reason).strip()},
        "definition": _text(
            "definition", form.get("definition"),
            why="It is load bearing twice: it feeds contrast-pair generation and "
                "it is the thing another author disagrees with. A submission "
                "without one is legible to nobody, which is why 001 made it "
                "NOT NULL and why nothing here will invent one.",
        ),
        "created_at": _text(
            "created_at", form.get("created_at"),
            why="When the work happened, which is not when it was typed in here.",
        ),
        "intervention": {
            "id": _text("intervention id", form.get("intervention_id"),
                        why="It is the primary key and the thing an eval report "
                            "or an attack points at."),
            "kind": _text("kind", form.get("kind"),
                          why="An open string. Whatever you call this."),
            "model_id": _text("model_id", form.get("model_id"),
                              why="A direction has no meaning apart from the "
                                  "model it was read out of."),
            "model_revision": form.get("model_revision", "").strip() or None,
            "layer": _integer("layer", form.get("layer")),
            "layer_convention": _text(
                "layer_convention", form.get("layer_convention"),
                why="Getting this wrong is silent. `block-0indexed` is a common "
                    "value and not the only one.",
            ),
            "hook_point": _text("hook_point", form.get("hook_point"),
                                why="An open string. Where in the block this acts."),
            "chat_template_hash": form.get("chat_template_hash", "").strip() or None,
            "shape": f.shape,
            "dtype": f.dtype,
            "l2_norm": f.l2_norm,
            "activation_norm": _number("activation_norm", form.get("activation_norm")),
            "coeff_low": _number("coeff_low", form.get("coeff_low")),
            "coeff_high": _number("coeff_high", form.get("coeff_high")),
            "steering_position": form.get("steering_position", "").strip() or None,
            "license_status": form.get("license_status", "").strip() or None,
            "artifact_repo": repo,
            "artifact_commit": commit,
            # None when nobody stated one, which is the ordinary case and means
            # the row resolves where every row resolved before
            # `schema/migrations/007`. Not filled in with the Hub here: that
            # would write a host onto a row nobody recorded one for.
            "artifact_host": host,
            "artifact_url_template": url_template,
            "artifact_path": checked.path,
            "artifact_sha256": f.sha256,
        },
    }


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _shown(path: Path) -> str:
    """A path as the operator would type it, and the whole thing when it is not.

    `relative_to` raises rather than falling back, which is right everywhere it
    guards containment and wrong here, where the answer is only ever printed.
    """
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


# --------------------------------------------------------------------------- #
# Suggestions, which are autocomplete and nothing else.


# Read out of the corpus rather than held as a list here, so there is no second
# taxonomy to go stale and nothing that reads like a set of permitted values.
# `astro/src/data/observed-labels.ts` makes the same argument for the site's
# picker: a datalist behind a free-text field is the same information with none
# of the authority. Every one of these fields takes anything typed into it, and
# a value nobody has used before is the normal way a corpus grows.
SUGGEST = {
    "label": "SELECT DISTINCT label FROM submission WHERE label != '' ORDER BY label",
    "kind": "SELECT DISTINCT kind FROM intervention WHERE kind != '' ORDER BY kind",
    "model_id": "SELECT DISTINCT model_id FROM intervention"
                " WHERE model_id != '' ORDER BY model_id",
    "hook_point": "SELECT DISTINCT hook_point FROM intervention"
                  " WHERE hook_point != '' ORDER BY hook_point",
    "layer_convention": "SELECT DISTINCT layer_convention FROM intervention"
                        " WHERE layer_convention != '' ORDER BY layer_convention",
    "steering_position": "SELECT DISTINCT steering_position FROM intervention"
                         " WHERE steering_position IS NOT NULL"
                         " AND steering_position != '' ORDER BY steering_position",
    "license_status": "SELECT DISTINCT license_status FROM intervention"
                      " WHERE license_status IS NOT NULL AND license_status != ''"
                      " ORDER BY license_status",
    "author": "SELECT DISTINCT author FROM submission WHERE author != '' ORDER BY author",
    "link_host": "SELECT DISTINCT artifact_host FROM intervention"
                 " WHERE artifact_host IS NOT NULL AND artifact_host != ''"
                 " ORDER BY artifact_host",
    "link_url_template": "SELECT DISTINCT artifact_url_template FROM intervention"
                         " WHERE artifact_url_template IS NOT NULL"
                         " AND artifact_url_template != ''"
                         " ORDER BY artifact_url_template",
}


# The corpus is the source for everything above and cannot be the source for
# these two on the day the column is added, because no row carries one yet. So
# these are seeded, and the seed is read out of code that already holds the
# value rather than typed here: `controlbun.fetch` for the Hub's layout, which is
# the one a row recording nothing resolves under, and `artifacts/source.py` for
# GitHub's two, which is where all four real directions in this corpus came
# from and which records when each was last checked against the live host.
#
# Three layouts across two hosts, which is the argument for the field rather
# than a table: GitHub needs two of them and 404s on the wrong one. They are
# documentation, they merge into whatever the corpus already holds, and they are
# enforced nowhere. Anything typed in is taken.
def _seeded() -> dict[str, list[str]]:
    hub_host, hub_template = fetch.hub_pin()
    return {
        "link_host": [hub_host, source.HOST],
        "link_url_template": [hub_template, source.MEDIA, source.RAW],
    }


def suggestions(conn: sqlite3.Connection) -> dict[str, list[str]]:
    """What this corpus already holds, per field. Never a constraint."""
    out: dict[str, list[str]] = {}
    seeded = _seeded()
    for field, sql in SUGGEST.items():
        try:
            found = [r[0] for r in conn.execute(sql)]
        except sqlite3.Error:
            found = []
        # Seeded values first and duplicates dropped, so a corpus that grows
        # into one of them does not offer it twice.
        out[field] = list(dict.fromkeys(seeded.get(field, []) + found))
    return out


# --------------------------------------------------------------------------- #
# The page.


STYLE = """
/* The tokens are `astro/src/styles/app.css`'s, copied rather than linked, and the
   page is set in the site's serif for the same reason: this is the same product
   seen from the inside. Copied, because this page is served by a stdlib handler
   with no static route, and giving it one so it could reach into `astro/` would
   hand this process a file-serving surface it has no other reason to have. The
   blues are the two ends of one blackbody curve and that file carries the
   contrast measurements for both surfaces. Red is not here at all: the site
   reserves it for status, and a refusal is an outcome rather than a fault. */
:root {
  color-scheme: light dark;
  --ink: #16161a; --dim: #6b6b72; --faint: #97979e;
  --line: #e4e4e8; --wash: #fafafa; --page: #fff;
  --warn: #8a5a00; --warn-line: #e6d38a;
  --accent: #356AFF; --accent-fill: #386BFE;
  --pop: #fff; --pop-line: #b3b3be;
  --pop-shadow: 0 6px 16px -10px rgba(22, 22, 26, .5),
                0 1px 2px rgba(22, 22, 26, .07);
  --mono: ui-monospace, SFMono-Regular, Menlo, monospace;
}
@media (prefers-color-scheme: dark) {
  :root {
    --ink: #e8e8ea; --dim: #a0a0a8; --faint: #74747c;
    --line: #2a2a30; --wash: #16161a; --page: #0d0d10;
    --warn: #d8a548; --warn-line: #4a3d1a;
    --accent: #95B1FF; --accent-fill: #95B1FF;
    --pop: #16161a; --pop-line: #44444f;
    --pop-shadow: 0 10px 26px -12px rgba(0, 0, 0, .85);
  }
}

* { box-sizing: border-box; }
[hidden] { display: none !important; }
body {
  font: 15px/1.6 ui-serif, Georgia, "Times New Roman", serif;
  color: var(--ink); background: var(--page);
  margin: 0; padding: 2.4rem clamp(1.25rem, 4vw, 4rem) 6rem;
}
:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }

/* ------------------------------------------------------------------ head */

header.top {
  display: flex; align-items: baseline; gap: .7rem; flex-wrap: wrap;
  border-bottom: 1px solid var(--line); padding-bottom: .9rem; margin-bottom: 2rem;
}
header.top .wordmark {
  font-family: var(--mono); font-size: .95rem; font-weight: 600;
  letter-spacing: -.02em;
}
header.top .bind {
  margin-left: auto; font-family: var(--mono); font-size: .78rem; color: var(--faint);
}
h1 { font-size: 1.95rem; margin: 0 0 .3rem; letter-spacing: -.01em; }
.lede { color: var(--dim); margin: 0 0 1.8rem; max-width: 44rem; }
.lede code { font-family: var(--mono); font-size: .85em; }

/* ---------------------------------------------------------------- layout */
/* The form is the input and the readout is the result, so the readout is the
   column that never leaves the screen. */

.work {
  display: grid; grid-template-columns: minmax(0, 1fr) 25rem;
  gap: 2.8rem; align-items: start;
}
@media (max-width: 70rem) {
  .work { grid-template-columns: 1fr; }
  .rail { position: static; }
}
.form { max-width: 54rem; }
/* Scrollable in itself, because a header with twenty keys in it makes the
   readout taller than the window and a sticky block taller than its viewport
   stops following. */
.rail { position: sticky; top: 1.5rem; max-height: calc(100vh - 3rem); overflow: auto; }

h2 {
  font-size: 1.1rem; margin: 2.4rem 0 .2rem; letter-spacing: -.005em;
  border-bottom: 1px solid var(--line); padding-bottom: .35rem;
}
.note { color: var(--dim); font-size: .85rem; margin: .5rem 0 0; max-width: 42rem; }
.note code { font-family: var(--mono); font-size: .88em; }

/* ----------------------------------------------------------------- field */

.grid {
  display: grid; grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 1rem 1.6rem; margin-top: 1rem;
}
.grid.single { grid-template-columns: minmax(0, 1fr); }
.field { position: relative; display: flex; flex-direction: column; gap: .25rem; }
.field > label {
  display: flex; align-items: baseline; gap: .45rem;
  font-size: .85rem; color: var(--ink);
}
/* A field name that is a column name is set in mono, the way every stored string
   on the site is, and a name this form made up for a human stays in the serif. */
.field .name { font-family: var(--mono); font-size: .82rem; }
.field .name.said { font-family: inherit; font-size: .88rem; }
/* The dotted rule is the site's mark for "this is operable", on sortable table
   headers and on the blanks in the situation picker. Here it reads as "there is
   more to this one", and pointing at the field or tabbing into it says what. */
.field .name { text-decoration: underline dotted var(--faint); text-underline-offset: 3px; }
.field:hover .name, .field:focus-within .name { text-decoration-color: var(--accent); }
.field .may {
  font-size: .72rem; color: var(--faint); border: 1px solid var(--line);
  border-radius: 999px; padding: 0 .4rem; white-space: nowrap;
}

input, textarea {
  font: inherit; width: 100%; color: var(--ink); background: var(--page);
  border: 1px solid var(--line); border-radius: 4px; padding: .4rem .55rem;
}
input:hover, textarea:hover { border-color: var(--dim); }
textarea { min-height: 6.5rem; line-height: 1.5; resize: vertical; }
input[type="file"] { padding: .3rem; font-size: .88rem; }
input[type="file"]::file-selector-button {
  font: inherit; font-size: .85rem; color: var(--ink); background: var(--wash);
  border: 1px solid var(--line); border-radius: 3px;
  padding: .2rem .6rem; margin-right: .6rem; cursor: pointer;
}
/* The tensor facts and the pins are strings the corpus stores, so the box they
   are typed into shows them the way the corpus will. */
.field.string input, .field.string textarea { font-family: var(--mono); font-size: .86rem; }

/* The explanation. One floating surface on the site, the type-ahead popup, and
   these borrow its tokens so a second one does not invent a second look. It is
   not hover-only: `:focus-within` opens it for a keyboard, and the input carries
   `aria-describedby` so it is read out whether or not it is on screen. */
.field .why {
  position: absolute; z-index: 20; top: 100%; left: 0; margin-top: .3rem;
  width: max(100%, 21rem); max-width: min(30rem, calc(100vw - 3rem));
  padding: .6rem .8rem;
  font-size: .85rem; line-height: 1.5; color: var(--ink);
  background: var(--pop); border: 1px solid var(--pop-line); border-radius: 5px;
  box-shadow: var(--pop-shadow);
  opacity: 0; visibility: hidden;
}
.field .why code { font-family: var(--mono); font-size: .88em; }
.field .why .from { display: block; margin-top: .35rem; color: var(--dim); font-size: .95em; }
.field:hover .why, .field:focus-within .why { opacity: 1; visibility: visible; }
/* The right-hand column would hang its explanation off the edge of the page. */
.grid > .field:nth-child(even) .why { left: auto; right: 0; }
/* A delay, so crossing the form with a pointer does not set off a row of them.
   The only motion on the page, and it answers something the reader did. */
@media (prefers-reduced-motion: no-preference) {
  .field .why { transition: opacity .09s ease, visibility 0s linear .09s; }
  .field:hover .why, .field:focus-within .why {
    transition: opacity .1s ease .3s, visibility 0s linear .3s;
  }
}

/* ------------------------------------------------------------ mode, bytes */

.modes { display: flex; gap: .6rem; flex-wrap: wrap; margin-top: 1rem; }
.modes .seg {
  display: flex; align-items: baseline; gap: .45rem; cursor: pointer;
  border: 1px solid var(--line); border-radius: 4px; padding: .45rem .75rem;
  font-size: .9rem; color: var(--dim);
}
.modes .seg input { width: auto; }
.modes .seg:hover { border-color: var(--dim); }
.modes .seg:has(input:checked) { border-color: var(--accent-fill); background: var(--wash); }
.modes .seg input:checked ~ .what { color: var(--ink); }
.modes .what strong { font-weight: 600; }

fieldset { border: 0; border-left: 2px solid var(--line); border-radius: 0;
           padding: .2rem 0 .2rem 1.1rem; margin: 1.3rem 0 0; }
fieldset > legend { display: none; }

/* ------------------------------------------------------------- the handoff */

.handoff {
  border: 1px solid var(--line); border-radius: 6px; background: var(--wash);
  padding: .9rem 1.1rem 1.1rem; margin-top: .4rem;
}
.handoff h2 { border: 0; margin: 0; padding: 0; font-size: 1rem; }
.handoff .note { margin-top: .3rem; }
.handoff .acts { display: flex; gap: .6rem; flex-wrap: wrap; margin-top: .8rem; }
#agent-paste { margin-top: .9rem; }
#agent-paste textarea {
  min-height: 4rem; background: var(--page);
  font-family: var(--mono); font-size: .84rem;
}
.said-quiet { font-size: .82rem; color: var(--dim); display: block; margin-bottom: .25rem; }
.status { font-size: .84rem; color: var(--dim); margin: .6rem 0 0; }

/* What was looked for and is not there, with the account of why. Set like the
   form and not like a warning: an absence is a state this schema holds, and the
   sentence beside it is the difference between one a reader can act on and an
   empty cell. Editable because the operator is the one publishing the sentence,
   and clearing one drops it rather than recording a blank. */
#agent-absent { margin-top: .9rem; }
#agent-absent .absence { margin-top: .5rem; }
#agent-absent .absence label {
  display: block; font-family: var(--mono); font-size: .8rem; color: var(--dim);
  margin-bottom: .2rem;
}
#agent-absent textarea { min-height: 3.2rem; }

/* What the parser worked out rather than read. Not styled as a warning: none
   of these is a fault and most pastes that produce them are fine. They are
   read like footnotes, so they are set like footnotes, and the rule down the
   side is there because a list of them gets long. */
.notes {
  margin: .5rem 0 0; padding: 0 0 0 .8rem; list-style: none;
  border-left: 2px solid var(--line);
}
.notes li { margin: .3rem 0; color: var(--ink); }

/* ---------------------------------------------------------------- buttons */

button {
  font: inherit; font-size: .92rem; color: var(--ink); background: var(--page);
  border: 1px solid var(--line); border-radius: 4px;
  padding: .45rem .9rem; cursor: pointer;
}
button:hover:not(:disabled) { background: var(--wash); border-color: var(--dim); }
/* Nothing on this site is a filled button, so the one that does the work says so
   with the brand rule instead. */
button.go { border-color: var(--accent-fill); color: var(--accent); }
button:disabled { color: var(--faint); border-color: var(--line); cursor: default; }

.acts { display: flex; gap: .6rem; flex-wrap: wrap; }
.acts.after { margin-top: .6rem; }
.rail .acts { margin-bottom: 1.2rem; }

/* ----------------------------------------------------------- the readout */
/* The strongest thing on the page. It is what the tool is for: the form is a
   claim and this is what the bytes said back. */

.out { border: 1px solid var(--line); border-radius: 6px; margin-bottom: 1.2rem; }
.out > h3 {
  font-size: .74rem; text-transform: uppercase; letter-spacing: .05em;
  color: var(--faint); font-weight: 600; margin: 0;
  padding: .6rem .9rem; border-bottom: 1px solid var(--line); background: var(--wash);
}
.out .body { padding: .85rem .9rem; border-left: 3px solid transparent; }
.out[data-state="empty"] .body { color: var(--dim); font-size: .88rem; }
.out[data-state="busy"] .body { color: var(--dim); }
.out[data-state="read"] .body { border-left-color: var(--accent-fill); }
.out[data-state="refused"] .body { border-left-color: var(--warn-line); }
.out .body > p { margin: 0 0 .5rem; }
.out .body > p:last-child { margin-bottom: 0; }

.refusal-what { font-weight: 600; color: var(--warn); }
.refusal-why { overflow-wrap: anywhere; }

dl.facts { margin: 0; }
dl.facts > div { padding: .45rem 0; border-bottom: 1px solid var(--line); }
dl.facts > div:first-child { padding-top: 0; }
dl.facts > div:last-child { border-bottom: 0; padding-bottom: 0; }
dl.facts dt { color: var(--faint); font-size: .78rem; }
dl.facts dd { margin: .1rem 0 0; overflow-wrap: anywhere; }
dl.facts dd.mono { font-family: var(--mono); font-size: .84rem; }
dl.facts dd.prose { font-size: .88rem; }
/* Absence renders as absence, in the italic the site uses for it, and never as a
   zero, a blank or a red line. */
dl.facts dd.absent { color: var(--faint); font-style: italic; font-size: .88rem; }

footer { margin-top: 3.5rem; padding-top: .9rem; border-top: 1px solid var(--line); }
footer p { margin: 0; color: var(--dim); font-size: .85rem; max-width: 42rem; }
footer code { font-family: var(--mono); font-size: .88em; }

/* The one field that holds prose rather than a value, so it keeps a measure
   instead of running the width of the column. */
#f-definition { max-width: 42rem; min-height: 8rem; }

/* Reaches a screen reader and nothing else. */
.sr-only {
  position: absolute; width: 1px; height: 1px; margin: -1px; padding: 0; border: 0;
  clip-path: inset(50%); overflow: hidden; white-space: nowrap;
}
"""

SCRIPT = """
const body = document.body;
const key = body.dataset.k;
const q = (id) => document.getElementById(id);
const modeOf = () => document.querySelector('input[name=mode]:checked').value;

function paint() {
  const m = modeOf();
  q('link-fields').hidden = m !== 'link';
  q('bytes-fields').hidden = m !== 'bytes';
}
for (const r of document.querySelectorAll('input[name=mode]')) {
  r.addEventListener('change', paint);
}
paint();

function fields() {
  const out = {};
  for (const el of document.querySelectorAll('[data-field]')) {
    out[el.dataset.field] = el.value;
  }
  return out;
}

// The other half of the form: what was looked for and is not there. Read off
// the boxes the paste built, exactly the way `fields` reads off the ones the
// page declared, so there is one way of getting a value out of this page and
// not two. A cleared box is a dropped reason and never a recorded blank.
function absences() {
  const out = {};
  for (const el of document.querySelectorAll('[data-absent]')) {
    if (el.value.trim()) out[el.dataset.absent] = el.value.trim();
  }
  return out;
}

// One box per field the paste accounted for, and the field names come from the
// paste rather than from a list here. A field this page has no input for still
// gets a box: an absence is about a column, and the reason is worth keeping
// whether or not this form has somewhere to type the value.
function showAbsences(absent) {
  const box = q('agent-absent');
  for (const old of box.querySelectorAll('.absence')) old.remove();
  const names = Object.keys(absent || {}).sort();
  box.hidden = names.length === 0;
  for (const name of names) {
    const row = document.createElement('div');
    row.className = 'absence';
    const label = document.createElement('label');
    label.textContent = name;
    label.htmlFor = 'absent-' + name;
    const area = document.createElement('textarea');
    area.id = 'absent-' + name;
    area.dataset.absent = name;
    area.spellcheck = false;
    area.value = absent[name];
    row.append(label, area);
    box.append(row);
  }
  return names.length;
}

// The readout. `state` drives the rule down its left edge, so a result, a
// refusal and an untouched panel are three states of one thing rather than three
// widgets, and a refusal is never colored as an alarm.
function panel(id, state) {
  const box = q(id);
  box.hidden = false;
  box.dataset.state = state;
  return box.querySelector('.body');
}

function say(id, state, text) {
  const p = document.createElement('p');
  p.textContent = text;
  panel(id, state).replaceChildren(p);
}

function refuse(id, text) {
  const what = document.createElement('p');
  what.className = 'refusal-what';
  what.textContent = 'Refused';
  const why = document.createElement('p');
  why.className = 'refusal-why';
  why.textContent = text;
  panel(id, 'refused').replaceChildren(what, why);
}

// Presentation only, and a value this guesses wrong renders as ordinary text. A
// value with no space in it, or a run of `key=value`, is a string the corpus
// stores and gets the mono face every stored string on this site is set in.
// Anything else is the tool talking and keeps the serif. The sentences the
// server writes where nothing was derived start the same few ways, and those
// render as absence rather than as a reading.
const ABSENT = /^(not |unnamed$|none[\\s.,]|none$|nothing,|the file carries no header$)/;
const STORED = /^[\\w.\\-\\/]+=/;

function classOf(value) {
  if (ABSENT.test(value)) return 'absent';
  if (STORED.test(value) || !/\\s/.test(value)) return 'mono';
  return 'prose';
}

function facts(id, payload) {
  const dl = document.createElement('dl');
  dl.className = 'facts';
  for (const [k, v] of payload.display) {
    const row = document.createElement('div');
    const dt = document.createElement('dt');
    dt.textContent = k;
    const dd = document.createElement('dd');
    dd.textContent = v;
    dd.className = classOf(v);
    row.append(dt, dd);
    dl.append(row);
  }
  panel(id, 'read').replaceChildren(dl);
}

let handle = null;

async function post(path, options) {
  let res;
  try {
    res = await fetch(path + (path.includes('?') ? '&' : '?') + 'k=' + key,
                      Object.assign({ method: 'POST' }, options));
  } catch (e) {
    // The tool is not listening any more. Distinguished from every other
    // failure because it is the one the page cannot say anything useful about
    // and the one a stale tab produces, and the token is per run, so the fix
    // is never to retry here.
    return { ok: false, gone: true, body: { refused:
      'this page is talking to an intake that is no longer running. The token '
      + 'in the URL is per run, so reopen the address the current one printed.'
    } };
  }
  const text = await res.text();
  let body;
  try { body = JSON.parse(text); } catch (e) { body = { refused: text }; }
  return { ok: res.ok, status: res.status, body };
}

q('check').addEventListener('click', async () => {
  handle = null;
  q('write').disabled = true;
  q('written').hidden = true;
  const m = modeOf();
  say('checked', 'busy', 'Reading the bytes\\u2026');
  let res;
  if (m === 'link') {
    res = await post('/check', {
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ mode: 'link', fields: fields() }),
    });
  } else {
    const file = q('file').files[0];
    if (!file) {
      refuse('checked', 'No file chosen. Bytes mode reads a file from this '
        + 'machine; link mode reads one already published somewhere.');
      return;
    }
    const url = '/check?mode=bytes&filename=' + encodeURIComponent(file.name)
      + '&fields=' + encodeURIComponent(JSON.stringify(fields()));
    res = await post(url, { body: file });
  }
  if (!res.ok) { refuse('checked', res.body.refused || 'no reason given'); return; }
  handle = res.body.handle;
  facts('checked', res.body);
  q('write').disabled = false;
});

q('write').addEventListener('click', async () => {
  if (!handle) return;
  q('write').disabled = true;
  say('written', 'busy', 'Writing the rows\\u2026');
  const res = await post('/write', {
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ handle, fields: fields(), absent: absences() }),
  });
  if (!res.ok) {
    refuse('written', res.body.refused || 'no reason given');
    q('write').disabled = false;
    return;
  }
  facts('written', res.body);
  handle = null;
});

// The two seams for the prompt handoff, which is built elsewhere. Both routes
// may not exist on this run, and a button that answers a 404 with a sentence is
// the whole contract: nothing here parses a prompt or writes one.
function agentSays(text, notes) {
  const line = q('agent-status');
  line.hidden = false;
  line.textContent = '';
  line.appendChild(document.createTextNode(text));
  // What the parser had to decide rather than read. A paste that parses is not
  // the same as a paste that was understood: a definition closed one sentence
  // in fills every field and quietly drops two thirds of the one field that
  // matters most. These are the only evidence of that, so they are shown even
  // when nothing was refused, and shown in full rather than counted.
  if (notes && notes.length) {
    const list = document.createElement('ul');
    list.className = 'notes';
    for (const note of notes) {
      const item = document.createElement('li');
      item.textContent = note;
      list.appendChild(item);
    }
    line.appendChild(list);
  }
}

q('agent-prompt').addEventListener('click', async () => {
  const res = await post('/agent-prompt', {
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ fields: fields() }),
  });
  if (res.gone || res.status === 404) {
    agentSays(res.body.refused || 'Nothing answers /agent-prompt on this run, '
      + 'so there is no prompt to copy. The form works without it.');
    return;
  }
  if (!res.ok || !res.body.prompt) {
    agentSays(res.body.refused || 'No prompt came back and no reason with it.');
    return;
  }
  try {
    await navigator.clipboard.writeText(res.body.prompt);
    agentSays('Copied. Run it where the extraction happened and paste what comes '
      + 'back.');
  } catch (e) {
    q('agent-text').value = res.body.prompt;
    agentSays('The clipboard refused, so the prompt is in the box below instead.');
  }
});

q('agent-fill').addEventListener('click', async () => {
  const text = q('agent-text').value.trim();
  if (!text) { agentSays('Nothing pasted yet.'); return; }
  const res = await post('/agent-paste', {
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ pasted: text }),
  });
  // Three different failures, and they were one message until a real refusal
  // arrived wearing the words "nothing answers this route". A refusal carries
  // the reason the paste was not read and that reason is the whole product of
  // the error path, so it is shown rather than summarized.
  if (res.gone || res.status === 404) {
    agentSays(res.body.refused || 'Nothing answers /agent-paste on this run, '
      + 'so the paste was not read. Type the fields in below.');
    return;
  }
  if (!res.ok || !res.body.fields) {
    agentSays(res.body.refused || 'The paste was not read and no reason came '
      + 'back with it.');
    return;
  }
  let filled = 0;
  for (const el of document.querySelectorAll('[data-field]')) {
    const value = res.body.fields[el.dataset.field];
    if (typeof value === 'string') { el.value = value; filled += 1; }
  }
  // The reasons were computed and then dropped on the floor here, which made
  // the parser's central rule true of the paste and false of the row: an
  // absence is a positive statement with a reason, and the reason went nowhere.
  const declared = showAbsences(res.body.absent);
  const notes = res.body.notes || [];
  agentSays(filled + ' fields filled from the paste, '
    + declared + ' absences accounted for. Every one of them is still '
    + 'editable, and nothing is checked until you check the bytes.'
    + (notes.length ? ' Read these before you check: they are what the parser '
       + 'had to work out rather than read, and a value it worked out wrong '
       + 'looks exactly like one it read.' : ''), notes);
});
"""


# Every sentence here comes from whatever owns the rule, and names it, so the
# reader can go and check rather than take this page's word: the comments in
# `schema/migrations`, the module docstrings under `src/controlbun`, `BRIEF.md`, and
# this file's own refusals. Nothing below is a fresh explanation of a column. A
# second explanation is a second thing to go stale, and the one written next to
# the column is the one the person who made it meant.
WHY = {
    "link_repo":
        "owner/name, on whichever host the field below names. The bytes stay "
        "there and never rest here; what this records is the pointer. No size "
        "limit, because nothing is held.",
    "link_host":
        "Which host that repo is on, as a bare authority such as "
        "<code>github.com</code>. May be empty, and empty means the Hub, which "
        "is where every row written before migration 007 resolves. It is a "
        "field rather than a list because a table of the hosts we happen to "
        "have met would be a list of where an artifact is allowed to come from, "
        "which is not ours to write. Nothing checks this against anything.",
    "link_url_template":
        "How <code>{host}</code>, <code>{repo}</code>, <code>{commit}</code> "
        "and <code>{path}</code> become a URL. A template may use any of the "
        "four or none of them: GitHub serves file content from a different host "
        "than its repos live on, so its templates do not mention "
        "<code>{host}</code> at all, and it needs two of them because the media "
        "host serves LFS objects and 404s on everything else. May be empty, and "
        "empty means the layout the Hub serves. What is checked is not which "
        "host this names: <code>controlbun.fetch</code> requires the commit to "
        "survive into the URL, because that is what a pin is, and refuses a "
        "scheme a fetch cannot happen over, because a pin that resolves only on "
        "the machine that wrote it is not one anybody else can check.",
    "link_commit":
        "Forty hex characters. <code>controlbun.fetch</code> resolves by commit "
        "only: a tag is movable by whoever owns the repo, so a pin to one is a "
        "pin to whatever is there today, which is the opposite of what "
        "<code>author/label@version</code> promises.",
    "link_path":
        "Recorded as <code>artifact_path</code> verbatim. "
        "<code>fetch.resolve</code> hands one path field to the remote, so the "
        "path inside the repo and the row's <code>artifact_path</code> are the "
        "same string or the fetch is a 404.",
    "file":
        "Converted to safetensors here and checked outside this repository. "
        "<code>controlbun.ingest</code> owns which bytes can be read without "
        "running them; a format nobody has written a converter for is refused "
        "with a sentence naming what has one and where another goes, which is "
        "not a statement that the format is illegitimate.",
    "bytes_repo":
        "The author's own namespace. <code>publish.upload</code> refuses this "
        "registry's own, because bytes there would be a copy this project serves "
        "rather than a thing an author published, which is a different column "
        "and a different question.",
    "bytes_path":
        "Also the row's <code>artifact_path</code>, character for character: one "
        "path field goes to the remote, so a fetch finds the file or it does not.",
    "bytes_tensor":
        "May be empty, and usually is. A file holding one array needs nothing "
        "here. A file holding several is refused by "
        "<code>ingest.one_array</code> in a message naming every one it found, "
        "and typing one of them back is how you say which is the artifact. "
        "Nothing is guessed from a near match: writing the wrong tensor under "
        "the right name is the one failure nothing downstream can catch.",
    "bytes_message": "What the upload says it is, in the commit it makes.",
    "shape":
        "Optional and checked. <code>artifact.confirmed</code> holds the bytes "
        "to whatever you state and the row keeps what you said; state nothing "
        "and the row records what the bytes say.",
    "dtype":
        "As numpy spells it. Stated, it is checked against the bytes and kept; "
        "left empty, the row takes the dtype the file carries.",
    "l2_norm":
        "Cited from wherever you got it, and checked against the bytes. Empty is "
        "not a wrong claim: the column is nullable and the row will record what "
        "the file says.",
    "sha256":
        "Of the whole file, header included, not of the tensor payload. The file "
        "is what gets fetched, cached and handed to a parser, so the file is what "
        "has to be identified. <code>artifact.sort_header</code> exists so that "
        "is a stable quantity, because safetensors serializes its header out of a "
        "randomly seeded HashMap.",
    "author":
        "Your namespace, free to claim. A label namespace permits an unlimited "
        "number of claimants, so claiming one takes nothing from anybody else.",
    "label":
        "Free to claim, and other people may claim it too. A bare label is a "
        "computed view across everyone claiming it, owned by nobody, and ten "
        "people extracting it differently is the content rather than a "
        "duplication problem.",
    "version":
        "<code>author/label@version</code> resolves to one frozen submission "
        "forever. A correction is a new version rather than a rewrite of this one.",
    "created_at":
        "When the work happened, which is not when it was typed in here.",
    "definition":
        "Your own theory of the trait, in prose. Load bearing twice: it feeds "
        "contrast-pair generation, and it is the thing another author disagrees "
        "with when they claim the same label. Migration 001 made it NOT NULL and "
        "nothing here will invent one.",
    "intervention_id":
        "The primary key, and what an eval report or an attack points at.",
    "kind":
        "An open string. <code>direction</code>, <code>sae-latent</code>, "
        "<code>probe</code>, <code>reft</code> and <code>lora</code> are the ones "
        "with client support today, not the permitted set. An unrecognized kind "
        "is storable and displayable and simply has no apply path until somebody "
        "writes one.",
    "model_id":
        "A direction has no meaning apart from the model it was read out of. "
        "Base and instruct are different models; so is a different revision.",
    "model_revision":
        "Empty means nobody recorded it, and it renders as that. NOT NULL does "
        "not produce a revision, it produces a string: an author who never "
        "recorded one types <code>unknown</code>, or <code>main</code>, or pastes "
        "the sha the model has today, and the last is worse than nothing because "
        "it is a false provenance claim that reads exactly like a true one.",
    "layer":
        "An integer, and the column cannot be absent. A hook that is not at a "
        "layer is a kind of artifact this column cannot describe, which is worth "
        "saying out loud rather than filling with a zero.",
    "layer_convention":
        "Stated in the schema rather than the README because getting this wrong "
        "is silent: a vector applied at the wrong layer appears not to work "
        "rather than failing loudly. <code>block-0indexed</code> is a common "
        "value and not the only one.",
    "hook_point":
        "Where in the block this acts. An open string, with "
        "<code>resid_pre</code>, <code>resid_post</code>, <code>mlp_out</code> "
        "and <code>attn_out</code> as the common values rather than the allowed "
        "ones; architectures have hook points those four do not name.",
    "chat_template_hash":
        "Vectors extracted under one template may not transfer to another, and a "
        "vector applied under the wrong one appears not to work rather than "
        "failing loudly. Empty if none was applied.",
    "activation_norm":
        "The typical activation magnitude at that layer, which lets a "
        "coefficient be expressed as a fraction of it rather than a raw alpha "
        "that means nothing across models. Empty unless a coefficient here is "
        "one of those.",
    "coeff_low":
        "The bottom of the range you swept and would recommend. Empty if you did "
        "not sweep one: empty records as not measured, and a zero would record "
        "as a measurement.",
    "coeff_high":
        "The top of the same range. Empty if you did not sweep one.",
    "steering_position":
        "Where in the sequence this is applied. An open string, and the other "
        "half of what somebody needs to apply this the way you did.",
    "license_status":
        "For the source model. Whether its license reaches a direction read out "
        "of it is open, and this registry does not answer it for you. Say what "
        "the license says, where you read it and when, and say what is "
        "unresolved. Unresolved rights mean the artifact is pointed at rather "
        "than served.",
}

# Where each explanation above comes from, kept apart from the text so the page
# can always put it last, whatever else got appended to the sentence.
SOURCE = {
    "link_repo": "artifacts/INTAKE.md",
    "link_host": "schema/migrations/007_any_host.sql",
    "link_url_template": "schema/migrations/007_any_host.sql",
    "link_commit": "src/controlbun/fetch.py",
    "link_path": "artifacts/intake.py",
    "file": "src/controlbun/ingest.py",
    "bytes_repo": "artifacts/publish.py",
    "bytes_path": "artifacts/intake.py",
    "bytes_tensor": "src/controlbun/ingest.py",
    "shape": "src/controlbun/artifact.py",
    "sha256": "schema/migrations/006_artifact_digest.sql",
    "label": "BRIEF.md, the object graph",
    "definition": "schema/migrations/001_init.sql",
    "kind": "schema/migrations/001_init.sql",
    "model_id": "schema/migrations/001_init.sql",
    "model_revision": "schema/migrations/005_unrecorded_revision.sql",
    "layer_convention": "schema/migrations/001_init.sql",
    "hook_point": "BRIEF.md, the data model",
    "chat_template_hash": "BRIEF.md, the data model",
    "activation_norm": "schema/migrations/001_init.sql",
    "steering_position": "BRIEF.md, the data model",
    "license_status": "schema/migrations/001_init.sql",
}

SUGGEST_NOTE = (
    " Suggestions are read out of what this corpus already holds, so there is no "
    "second taxonomy to go stale. Anything typed in is taken, and a value nobody "
    "has used before is the normal way a corpus grows."
)


def _why(name: str, note: str = "", *, suggested: bool = False) -> str:
    """The explanation for one field, with where it came from last.

    Order matters and is the reason `SOURCE` is a second table: the citation is
    the end of the note however much else got appended to it, and a source line
    stranded mid-paragraph reads as part of the next sentence.
    """
    text = " ".join(part for part in (html.escape(note), WHY.get(name, "")) if part)
    if suggested:
        text += SUGGEST_NOTE
    if name in SOURCE:
        text += f'<span class="from">{html.escape(SOURCE[name])}</span>'
    return text


def _field(name: str, title: str, note: str, *, value: str = "",
           suggest: list[str] | None = None, area: bool = False,
           empty_ok: bool = False, string: bool = False) -> str:
    """One field, its name, and the explanation that hangs off it.

    The explanation is not a `title` attribute. It is an element the input points
    at with `aria-describedby`, so a screen reader reads it on focus whether or
    not it is on screen, `:focus-within` opens it for a keyboard, and a pointer
    opens it by resting on the field. Three ways in, one piece of text.
    """
    listid = f"sug-{name}" if suggest else ""
    attrs = f' list="{listid}"' if suggest else ""
    described = f' aria-describedby="why-{name}"'
    control = (
        f'<textarea data-field="{name}" id="f-{name}"{described}></textarea>'
        if area else
        f'<input data-field="{name}" id="f-{name}" value="{html.escape(value)}"'
        f' spellcheck="false" autocomplete="off"{described}{attrs}>'
    )
    options = ""
    if suggest:
        options = f'<datalist id="{listid}">' + "".join(
            f'<option value="{html.escape(s)}">' for s in suggest
        ) + "</datalist>"
    # A column name is set in mono, the way every stored string on the site is.
    # A name this form made up for a human keeps the serif.
    said = "" if title == title.lower() and " " not in title else " said"
    tag = '<span class="may">may be empty</span>' if empty_ok else ""
    why = _why(name, note, suggested=bool(suggest))
    return (
        f'<div class="field{" string" if string else ""}">'
        f'<label for="f-{name}"><span class="name{said}">{html.escape(title)}</span>'
        f'{tag}</label>{control}{options}'
        f'<div class="why" id="why-{name}">{why}</div></div>'
    )


def page(conn: sqlite3.Connection, *, token: str, repo: str, origin: str) -> bytes:
    s = suggestions(conn)
    cap = BYTES_CAP // (1024 * 1024)

    # The handoff seams. The prompt and the parsing behind them are built
    # elsewhere and neither route may exist on this run, so both are designed as
    # part of the page and both answer a 404 with a sentence.
    handoff = (
        '<section class="handoff">'
        '<h2>Hand it to your coding agent</h2>'
        '<p class="note">An agent sitting in the checkout where the extraction '
        'happened can read most of this off your own scripts. Copy the prompt, '
        'run it there, and paste back what it produces. Nothing it fills in is '
        'checked until you check the bytes, and every field stays editable.</p>'
        '<div class="acts">'
        '<button type="button" id="agent-prompt">Copy a prompt for your coding '
        'agent</button>'
        '</div>'
        '<div id="agent-paste">'
        '<label class="said-quiet" for="agent-text">Paste what it produced</label>'
        '<textarea id="agent-text" spellcheck="false"></textarea>'
        '<div class="acts after">'
        '<button type="button" id="agent-fill">Fill the form from this</button>'
        '</div></div>'
        # Built from whatever came back rather than declared here, because the
        # field side of an absence is an open string and a fixed set of boxes
        # would be the list of which fields are allowed an explanation. Empty
        # and hidden until a paste declares one, which is the ordinary case.
        '<div id="agent-absent" hidden>'
        '<p class="said-quiet">What it could not find, and why. These are '
        'recorded beside the row and render next to the absence. Clear one to '
        'drop it; an absence with nobody\'s account of it is a normal state.</p>'
        '</div>'
        '<p class="status" id="agent-status" hidden></p>'
        '</section>'
    )

    where = (
        '<h2>Where the bytes are</h2>'
        '<p class="note">Two modes, one end state: a row pointing at a pinned '
        'remote. Neither writes a served copy.</p>'
        '<div class="modes">'
        '<label class="seg"><input type="radio" name="mode" value="link" checked>'
        '<span class="what"><strong>Link</strong>, they are published somewhere'
        '</span></label>'
        '<label class="seg"><input type="radio" name="mode" value="bytes">'
        '<span class="what"><strong>Bytes</strong>, I have the file here</span>'
        '</label>'
        '</div>'

        '<fieldset id="link-fields"><legend>Link</legend>'
        '<p class="note">Fetched once into a throwaway cache, checked, and '
        'dropped. What is recorded is the pointer, so there is no size limit.</p>'
        '<div class="grid">'
        + _field("link_repo", "Repo", "owner/name.", string=True)
        + _field("link_commit", "Commit",
                 "Forty hex characters.", string=True)
        + '</div><div class="grid single">'
        + _field("link_path", "Path in the repo",
                 "Where the file sits inside that repo.", string=True)
        + '</div><div class="grid">'
        + _field("link_host", "Host", "Which host that repo is on.",
                 suggest=s["link_host"], empty_ok=True, string=True)
        + _field("link_url_template", "URL template",
                 "How those four become a URL.",
                 suggest=s["link_url_template"], empty_ok=True, string=True)
        + '</div></fieldset>'

        '<fieldset id="bytes-fields" hidden><legend>Bytes</legend>'
        f'<p class="note">Read here, converted to safetensors, checked outside '
        f'this repository, then pushed to the namespace below and deleted. '
        f'Nothing rests here. This form holds the whole file in memory while it '
        f'checks it, so it takes up to {cap} MB; that is a cap on this form on '
        f'this machine and says nothing about the artifact. Above it, publish '
        f'the bytes wherever you already publish and use link mode, which has '
        f'no size limit at all.</p>'
        '<div class="grid single">'
        '<div class="field">'
        '<label for="file"><span class="name said">File</span></label>'
        '<input type="file" id="file" aria-describedby="why-file">'
        f'<div class="why" id="why-file">{_why("file")}</div>'
        '</div></div>'
        '<div class="grid">'
        + _field("bytes_repo", "Publish to", "The author's own Hub namespace.",
                 value=repo, string=True)
        + _field("bytes_path", "Path in the repo",
                 "Where it will sit inside that repo.", string=True)
        + '</div><div class="grid">'
        + _field("bytes_tensor", "Which tensor",
                 "Only when the file holds more than one.", string=True,
                 empty_ok=True)
        + _field("bytes_message", "Commit message", "",
                 value="Publish one steering artifact")
        + '</div></fieldset>'
    )

    stated = (
        '<h2>What you state about the bytes</h2>'
        '<p class="note">All four can be left empty, and every one that is not '
        'is checked. State one and the bytes are held to it and the row keeps '
        'what you said; state nothing and the row records what the bytes say. '
        'Saying nothing is not a wrong claim.</p>'
        '<div class="grid">'
        + _field("shape", "shape", "As the row will hold it, a bracketed list.",
                 empty_ok=True, string=True)
        + _field("dtype", "dtype", "", empty_ok=True, string=True)
        + _field("l2_norm", "l2_norm", "", empty_ok=True, string=True)
        + _field("sha256", "sha256", "", empty_ok=True, string=True)
        + '</div>'
    )

    submission = (
        '<h2>The submission</h2>'
        '<p class="note">One author\'s complete take, versioned and immutable. '
        'Somebody else claiming the same label is the content here, not a '
        'collision.</p>'
        '<div class="grid">'
        + _field("author", "author", "", suggest=s["author"], string=True)
        + _field("label", "label", "", suggest=s["label"], string=True)
        + _field("version", "version", "", string=True)
        + _field("created_at", "created_at", "", value=_now(), string=True)
        + '</div><div class="grid single">'
        + _field("definition", "definition", "", area=True)
        + '</div>'
    )

    intervention = (
        '<h2>The intervention</h2>'
        '<p class="note">The application contract. A vector applied at the wrong '
        'layer, hook point or chat template appears not to work rather than '
        'failing loudly, which is why these sit beside the artifact and not in a '
        'README.</p>'
        '<div class="grid">'
        + _field("intervention_id", "id", "", string=True)
        + _field("kind", "kind", "", suggest=s["kind"], string=True)
        + _field("model_id", "model_id", "", suggest=s["model_id"], string=True)
        + _field("model_revision", "model_revision", "", empty_ok=True, string=True)
        + _field("layer", "layer", "", string=True)
        + _field("layer_convention", "layer_convention", "",
                 suggest=s["layer_convention"], string=True)
        + _field("hook_point", "hook_point", "", suggest=s["hook_point"], string=True)
        + _field("chat_template_hash", "chat_template_hash", "", empty_ok=True,
                 string=True)
        + _field("activation_norm", "activation_norm", "", empty_ok=True, string=True)
        + _field("coeff_low", "coeff_low", "", empty_ok=True, string=True)
        + _field("coeff_high", "coeff_high", "", empty_ok=True, string=True)
        + _field("steering_position", "steering_position", "",
                 suggest=s["steering_position"], empty_ok=True, string=True)
        + '</div><div class="grid single">'
        + _field("license_status", "license_status", "",
                 suggest=s["license_status"], empty_ok=True, string=True)
        + '</div>'
    )

    # The readout, and the reason it is a column of its own: the form is a claim
    # and this is what the bytes said back. It stays on screen while the form
    # scrolls, because it is the thing the tool is for.
    rail = (
        '<aside class="rail">'
        '<div class="acts">'
        '<button type="button" id="check" class="go">Check the bytes</button>'
        '<button type="button" id="write" disabled>Write the rows</button>'
        '</div>'
        '<section class="out" id="checked" data-state="empty">'
        '<h3>What the bytes say</h3>'
        '<div class="body" aria-live="polite">'
        '<p>Nothing read yet. Checking fetches or converts the file, prints the '
        'digest, the shape, the dtype and the norm it found, and writes nothing. '
        'Anything you stated above is held against what it reads.</p>'
        '<p>A refusal lands here too, with the reason and the module that owns '
        'the rule. That is an outcome, not a fault.</p>'
        '</div></section>'
        '<section class="out" id="written" data-state="empty" hidden>'
        '<h3>The rows</h3><div class="body" aria-live="polite"></div>'
        '</section>'
        '</aside>'
    )

    body = (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        '<meta name="robots" content="noindex,nofollow">'
        '<title>intake, local only</title>'
        f'<style>{STYLE}</style></head>'
        f'<body data-k="{html.escape(token)}">'
        '<header class="top"><span class="wordmark">controlbun</span>'
        f'<span class="bind">{html.escape(origin)}</span></header>'
        '<h1>intake</h1>'
        '<p class="lede">One artifact into the corpus, from this machine and no '
        'other. This is the operator tool and not a submission route: nothing '
        'can be submitted to this registry, and that is what the dual-use policy '
        'is waiting on. Point at a field name, or tab into it, for what the '
        'column means and who says so.</p>'
        '<div class="work"><main class="form">'
        + handoff + where + stated + submission + intervention +
        '<footer><p>No eval is written here, and a submission with none is a '
        'normal state rather than an incomplete one. Rows go into '
        '<code>registry.db</code> and into <code>artifacts/intake.jsonl</code>, '
        'which is the copy that survives <code>make site</code>.</p></footer>'
        '</main>'
        + rail +
        '</div>'
        f'<script>{SCRIPT}</script></body></html>'
    )
    return body.encode()


# --------------------------------------------------------------------------- #
# The server.


class Intake:
    """Everything one run of the server holds. One lock over all of it.

    `controlbun.fetch.CACHE` is a module global that `check_link` swaps and
    restores, and the staging map is shared, so requests are serialized rather
    than interleaved. An operator tool serving one person does not need
    concurrency, and the two ways of getting this wrong both end with one
    submission's bytes recorded under another's row.
    """

    def __init__(self, database: str, repo: str) -> None:
        self.database = database
        self.repo = repo
        self.token = secrets.token_urlsafe(24)
        self.lock = threading.Lock()
        self.staged: dict[str, Checked] = {}

    def connect(self) -> sqlite3.Connection:
        return db.connect(self.database)

    def drop(self, handle: str) -> None:
        checked = self.staged.pop(handle, None)
        if checked and checked.staging_root:
            shutil.rmtree(checked.staging_root, ignore_errors=True)

    def close(self) -> None:
        for handle in list(self.staged):
            self.drop(handle)


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    server_version = "registry-intake"
    sys_version = ""
    intake: Intake = None  # type: ignore[assignment]

    # -- plumbing ----------------------------------------------------------- #

    def log_message(self, fmt, *args):
        # The query string carries the run token. Logging the request line, which
        # is what the default does, would put it in a terminal scrollback and, on
        # a shared machine, in whatever reads that. The route is enough to watch
        # the tool work.
        route = urlsplit(getattr(self, "path", "") or "").path or "-"
        sys.stderr.write(f"{getattr(self, 'command', None) or '-'} {route}\n")

    def _origin(self) -> str:
        return f"http://{HOST}:{self.server.server_address[1]}"

    def _reply(self, code: int, blob: bytes, kind: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", kind)
        self.send_header("Content-Length", str(len(blob)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(blob)

    def _json(self, code: int, payload: dict) -> None:
        self._reply(code, json.dumps(payload).encode(), "application/json")

    def _refused(self, reason: str, code: int = 400) -> None:
        self._json(code, {"refused": reason})

    def _admitted(self) -> bool:
        """Four checks, and they are the localhost-only constraint in code.

        The bind is necessary and not sufficient. A page the operator did not
        open, in the same browser, can post to 127.0.0.1, and a name that
        resolves to 127.0.0.1 defeats the bind entirely. So: the run token, which
        is in the URL the tool printed and nowhere else; the `Host` header, which
        a rebound name gets wrong; and `Origin` and `Sec-Fetch-Site`, which a
        cross-site post cannot forge. Any of them failing is a refusal with no
        detail, because the reader is not the operator.
        """
        port = self.server.server_address[1]
        got = parse_qs(urlsplit(self.path).query).get("k", [""])[0]
        if not secrets.compare_digest(got, self.intake.token):
            return False
        if self.headers.get("Host") not in (f"{HOST}:{port}", f"localhost:{port}"):
            return False
        origin = self.headers.get("Origin")
        if origin and origin not in (self._origin(), f"http://localhost:{port}"):
            return False
        if self.headers.get("Sec-Fetch-Site") not in (None, "same-origin", "none"):
            return False
        return True

    def _body(self, cap: int) -> bytes:
        """The request body, refused on the declared length before it is read."""
        declared = int(self.headers.get("Content-Length") or 0)
        if declared > cap:
            # The body is still arriving and will not be read, so the socket is
            # no use for another request. Said here rather than in `_reply`,
            # which is right about every other response.
            self.close_connection = True
            raise Refused(
                f"{declared} bytes were offered and this form takes "
                f"{cap}, which is {cap // (1024 * 1024)} MB. "
                "It holds the whole file in memory to digest, sniff, "
                "convert and recheck it before anything is written, and that "
                "order is what the check is worth. The cap is this form's, on "
                "this machine; it is not a judgment about the artifact and "
                "there is no size this registry will not index. Publish the "
                "bytes wherever you already publish and use link mode, which "
                "carries no limit because it never holds them."
            )
        return self.rfile.read(declared)

    # -- routes ------------------------------------------------------------- #

    def do_GET(self):  # noqa: N802
        if urlsplit(self.path).path == "/favicon.ico":
            # Answered before the admission check, because a browser asks for
            # this without the token and a 403 per page load reads like the tool
            # is broken. There is no icon and 204 says so.
            return self._reply(204, b"", "text/plain")
        if not self._admitted():
            return self._refused("not this origin, or no run token in the URL. "
                                 "The command that started this printed the URL "
                                 "to open.", 403)
        if urlsplit(self.path).path != "/":
            return self._refused("no such page here.", 404)
        with self.intake.lock:
            conn = self.intake.connect()
            try:
                blob = page(conn, token=self.intake.token, repo=self.intake.repo,
                            origin=self._origin())
            finally:
                conn.close()
        self._reply(200, blob, "text/html; charset=utf-8")

    def do_POST(self):  # noqa: N802
        if not self._admitted():
            return self._refused("not this origin, or no run token in the URL.", 403)
        route = urlsplit(self.path).path
        try:
            with self.intake.lock:
                if route == "/check":
                    return self._json(200, self._check())
                if route == "/write":
                    return self._json(200, self._write())
                if route == "/agent-prompt":
                    return self._json(200, {"prompt": self._prompt()})
                if route == "/agent-paste":
                    return self._json(200, self._paste())
        except (Refused, agent_handoff.Refused) as refused:
            return self._refused(str(refused))
        except (artifact.MismatchedArtifact, artifact.UnsafeArtifactPath,
                ingest.RefusedBytes, fetch.FetchError, publish.ServedCopy,
                publish.PinError) as refused:
            # Every one of these already carries the reason in its message, and
            # the reader is an operator with a file in hand. A traceback would
            # be the wrong artifact to hand them.
            return self._refused(str(refused))
        except sqlite3.IntegrityError as clash:
            return self._refused(
                f"the database will not take this row: {clash}. A submission is "
                "immutable once written, so a correction is a new version rather "
                "than a rewrite of this one."
            )
        except (RuntimeError, FileNotFoundError, OSError) as stopped:
            return self._refused(str(stopped))
        except Exception as unexpected:  # noqa: BLE001
            # Everything above is a refusal somebody wrote a sentence for. This
            # is a defect, and the operator still gets an answer rather than a
            # dropped connection and a traceback in another window. Re-raised
            # nowhere, because a handler thread dying takes the answer with it.
            sys.stderr.write(f"intake: {unexpected!r}\n")
            return self._json(500, {"refused": f"{type(unexpected).__name__}: "
                                               f"{unexpected}"})
        self._refused("no such endpoint here.", 404)

    def _prompt(self) -> str:
        """The manual the author hands their agent, with this corpus's own
        vocabulary folded in.

        `suggestions` is passed rather than omitted so the prompt can say what
        other people have typed, which is the only claim it makes about those
        strings. `agent_handoff` renders them as observation and not as a menu,
        and the prompt reads the same without them.
        """
        conn = self.intake.connect()
        try:
            return agent_handoff.prompt(suggestions(conn))
        finally:
            conn.close()

    def _paste(self) -> dict:
        """What the author's agent replied, turned into field values.

        Parsed here rather than in the page script because the rules are the
        schema's, and one implementation is the one a test can drive. Nothing
        is written: the values land in the form still editable, and the bytes
        are still checked before any row exists.
        """
        body = self._body(1 << 20)
        try:
            pasted = json.loads(body or b"{}").get("pasted", "")
        except json.JSONDecodeError:
            raise Refused("the paste did not arrive as JSON.") from None
        return agent_handoff.received(pasted)

    def _check(self) -> dict:
        query = parse_qs(urlsplit(self.path).query)
        if query.get("mode", [""])[0] == "bytes":
            blob = self._body(BYTES_CAP)
            if not blob:
                raise Refused("no bytes arrived.")
            form = json.loads(query.get("fields", ["{}"])[0])
            checked = check_bytes(
                blob,
                filename=query.get("filename", ["the dropped file"])[0],
                path=form.get("bytes_path", "").strip(),
                stated=self._stated(form),
                tensor=form.get("bytes_tensor", "").strip(),
            )
        else:
            payload = json.loads(self._body(1 << 20) or b"{}")
            form = payload.get("fields", {})
            checked = check_link(
                repo=_text("repo", form.get("link_repo"),
                           why="owner/name, the repo the artifact is published in."),
                commit=_text("commit", form.get("link_commit"),
                             why="Forty hex characters."),
                path=form.get("link_path", "").strip(),
                stated=self._stated(form),
                host=form.get("link_host", "").strip(),
                url_template=form.get("link_url_template", "").strip(),
            )

        handle = secrets.token_urlsafe(12)
        self.intake.staged[handle] = checked
        return {"handle": handle, "display": checked.display()}

    def _write(self) -> dict:
        payload = json.loads(self._body(1 << 20) or b"{}")
        form = payload.get("fields", {})
        handle = payload.get("handle", "")
        checked = self.intake.staged.get(handle)
        if checked is None:
            raise Refused(
                "nothing staged under that handle, so there are no checked bytes "
                "to write a row about. Check again; a row written from bytes "
                "nobody read is the thing this whole path exists to prevent."
            )

        # The staged verification is about one artifact at one path, and the
        # form is still editable after the check ran. Editing it and writing
        # would upload bytes to one path and record another, or record a pin at
        # a commit nothing was checked against. Refused rather than silently
        # preferring either side, because both sides look right to the person
        # who typed them.
        moved = {
            "bytes": {"bytes_path": checked.path},
            "link": {"link_repo": checked.repo, "link_commit": checked.commit,
                     "link_path": checked.path,
                     # Both of these change which bytes a fetch returns, so both
                     # belong here. Compared against "" rather than None because
                     # the form sends empty strings and the check stores None.
                     "link_host": checked.host or "",
                     "link_url_template": checked.url_template or ""},
        }[checked.mode]
        changed = sorted(
            field for field, was in moved.items()
            if (form.get(field) or "").strip() != was
        )
        if changed:
            raise Refused(
                f"{', '.join(changed)} changed since the check ran, so what was "
                "read and what would be written are not the same artifact. "
                "Check again."
            )

        if checked.mode == "bytes":
            repo = _text("publish to", form.get("bytes_repo"),
                         why="The author's own Hub namespace.")
            commit, url = publish.upload(
                [(checked.path, checked.staged)],
                repo=repo,
                message=form.get("bytes_message", "").strip()
                or "Publish one steering artifact",
                create=True,
            )
            # Bytes mode uploads to the Hub, so the row records the Hub rather
            # than leaving the host to the default. Read off `fetch` so a fork
            # or a test that repoints it records what it actually pushed to.
            host, url_template = fetch.hub_pin()
            published = f"pushed to {repo} at {commit}, {url}"
        else:
            repo, commit = checked.repo, checked.commit
            host, url_template = checked.host, checked.url_template
            published = (f"already at {repo} at {commit}; nothing was uploaded "
                         "and no copy was made")

        entry = entry_from(form, checked, repo=repo, commit=commit,
                           host=host, url_template=url_template,
                           absent=payload.get("absent") or {})
        conn = self.intake.connect()
        try:
            insert(conn, entry)
        finally:
            conn.close()
        # Appended after the rows go in, so the record never claims a write the
        # database refused. The other order loses nothing on a rebuild and gains
        # a line describing a row that was never made.
        append_record(entry)
        self.intake.drop(handle)

        ref = f"{entry['author']}/{entry['label']}@{entry['version']}"
        return {"display": [
            ("wrote", f"{ref}, and intervention {entry['intervention']['id']}"),
            ("artifact", published),
            ("pinned as", f"artifact_repo {repo}, artifact_commit {commit}, "
                          f"artifact_path {entry['intervention']['artifact_path']}"),
            ("host", f"artifact_host {host}, artifact_url_template "
                     f"{url_template}" if host or url_template else
                     "none recorded, so this resolves against "
                     f"{fetch.hub_pin()[0]}, which is where every row written "
                     "before migration 007 resolves"),
            ("served copy", "none. Nothing here writes served_repo."),
            ("evals", "none recorded, which is a state and not a gap. Point one "
                      "at this submission whenever there is one."),
            # Named rather than counted, and the fields listed, because a reason
            # that travelled to the wrong field is invisible in a count. Nothing
            # accounted for is the ordinary case and says so in those words.
            ("absences accounted for",
             ", ".join(sorted(absences_of(entry))) if absences_of(entry) else
             "none. An absence with nobody's account of it is the ordinary "
             "state and renders as absence, not as a gap."),
            ("recorded in", f"{_shown(RECORD)}, so it survives the rebuild "
                            "that drops registry.db"),
        ]}

    @staticmethod
    def _stated(form: dict) -> dict[str, str]:
        return {k: (form.get(k) or "").strip()
                for k in ("shape", "dtype", "l2_norm", "sha256")}


def serve(database: str, repo: str, port: int, *, open_browser: bool = True) -> None:
    intake = Intake(database, repo)
    handler = type("BoundHandler", (Handler,), {"intake": intake})
    httpd = ThreadingHTTPServer((HOST, port), handler)
    url = f"http://{HOST}:{httpd.server_address[1]}/?k={intake.token}"
    # Flushed, because this line is the whole interface: the URL carries the
    # run token and a buffered stdout hands it over when the process exits.
    print(f"intake on {url}", flush=True)
    print("Loopback only, and the token is per run. Ctrl-C to stop.", flush=True)
    if open_browser:
        webbrowser.open(url)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print()
    finally:
        httpd.server_close()
        intake.close()


# --------------------------------------------------------------------------- #


# --------------------------------------------------------------------------- #
# Taking a submission somebody built in a browser.


# The shape `/submit/` writes when somebody fills the fields in, namespaced and
# versioned, because whatever reads one has to know which shape it is holding
# and the shape will change.
LINK_SUBMISSION = "controlbun.registry/link-submission@1"

# And the shape it writes when somebody pastes what their coding agent produced.
# The record carries the paste as the text it is and nothing else is read off
# it there: `agent_handoff.parse` runs here, on this machine, at pull time.
#
# **There is one parser and it is in Python.** A check in the page would be a
# second implementation of several hundred lines of recovery, and two parsers
# that drift is the failure this repository has hit most often. What that costs
# is named rather than hidden: a paste is not checked until the author pulls it,
# so a refusal reaches the submitter by mail rather than as they type, and
# `/submit/` says exactly that beside the box.
AGENT_PASTE = "controlbun.registry/agent-paste@1"

# Every shape this version reads, with why it exists. Two entries rather than
# one since the handoff landed, and a third is a decision somebody makes here
# rather than a string that arrives in a record.
SHAPES = {
    LINK_SUBMISSION: "the twenty fields, filled in and checked one at a time in "
                     "the browser as they were typed",
    AGENT_PASTE: "one block of text a coding agent produced, parsed here by "
                 "`agent_handoff.parse` because there is one parser",
}

# Substrings, matched against key names and never against values. A record from
# `/signed-in/` can carry none of these by construction; one that does was
# written by something else and is not going to be turned into a tracked row.
# Same list and same argument as `artifacts/claim.py`, one object along.
CREDENTIAL_WORDS = (
    "token", "secret", "password", "credential", "authorization",
    "apikey", "api_key", "private_key", "bearer", "verifier",
)


def refuse_credentials(value, *, where: str) -> None:
    """Walk every key. A name that reads like a credential stops the run."""
    if isinstance(value, dict):
        for key, inner in value.items():
            if any(word in str(key).lower() for word in CREDENTIAL_WORDS):
                raise Refused(
                    f"{where} carries a key named {key!r}. This is read in "
                    "order to make a tracked row in a public repository, and "
                    "nothing that reads like a credential is going into one. "
                    "Nothing was written."
                )
            refuse_credentials(inner, where=where)
    elif isinstance(value, list):
        for inner in value:
            refuse_credentials(inner, where=where)


# What a record carries when the fields were filled in, so a paste that also
# carries one of them can be refused by name rather than by shape. `shape`,
# `submitted_at`, `provider`, `subject`, `author` and `uploaded_by_registry` are
# not here: those are stamped or carried by both routes.
FILLED_IN = ("label", "version", "definition", "created_at", "intervention",
             "artifact", "absent")


def _from_fields(submission: dict) -> tuple[dict, dict, dict, dict]:
    """A record whose fields were typed, flattened into what `entry_from` takes.

    Every value is passed through as a string and nothing is defaulted: a field
    the submitter left empty reaches `_text` and refuses there with the sentence
    that says why the field exists, which is the same refusal the form gives.
    """
    artifact_at = submission.get("artifact") or {}
    iv = submission.get("intervention") or {}
    form = {
        "author": str(submission.get("author") or ""),
        "label": str(submission.get("label") or ""),
        "version": str(submission.get("version") or ""),
        "definition": str(submission.get("definition") or ""),
        "created_at": str(submission.get("created_at") or ""),
        "intervention_id": str(iv.get("id") or ""),
    }
    for field in ("kind", "model_id", "model_revision", "layer",
                  "layer_convention", "hook_point", "chat_template_hash",
                  "activation_norm", "coeff_low", "coeff_high",
                  "steering_position", "license_status"):
        value = iv.get(field)
        form[field] = "" if value is None else str(value)
    where = {name: str(artifact_at.get(name) or "")
             for name in ("repo", "commit", "path", "host", "url_template")}
    # Nothing is stated about the tensor on this route. The browser computes no
    # shape, dtype, norm or digest, for the reason `handshake.mjs` gives at
    # length: one thing in this project reads bytes.
    return form, where, {}, submission.get("absent") or {}


def _from_paste(submission: dict, notes: list[str]) -> tuple[dict, dict, dict, dict]:
    """A record carrying one paste, read by the one parser there is.

    **A paste and filled fields together is refused, and neither wins.** That is
    the rule `insert` already applies to a field given both a value and a reason
    for having none, and the argument is the same one: resolving it means
    dropping one of somebody's two statements without saying so, and both of
    them look correct to whoever wrote them.

    **The stamped author outranks the one in the paste.** An agent reading its
    own author's files writes down whatever namespace it found there; the row's
    handle came through the insert policy out of a verified session. So the
    stamped one is what the row records and the disagreement is said out loud,
    which is what `stamped` does one object along for the same reason.
    """
    pasted = submission.get("pasted")
    if not isinstance(pasted, str) or not pasted.strip():
        raise Refused(
            f"this record carries shape {AGENT_PASTE} and no `pasted` text, so "
            "there is nothing to read. Nothing was written."
        )
    also = [name for name in FILLED_IN if submission.get(name)]
    if also:
        raise Refused(
            "this record carries a paste and " + ", ".join(also) + " as well. "
            "Those are two accounts of one submission and nothing here can tell "
            "which was meant, so neither is written. Send the paste or send the "
            "fields."
        )

    got = agent_handoff.parse(pasted)
    notes.extend(got.notes)

    said_as = {spec.form[0]: spec.name for spec in agent_handoff.SPECS}
    form = {said_as[field]: value for field, value in got.values.items()
            if field in said_as}

    stamped_author = str(submission.get("author") or "").strip()
    if stamped_author:
        if form.get("author") and form["author"] != stamped_author:
            notes.append(
                f"the paste says author {form['author']!r} and the session "
                f"stamped {stamped_author!r}. The stamped one is what the row "
                "records, because it came through the insert policy and the "
                "paste came from a coding agent reading files."
            )
        form["author"] = stamped_author
    else:
        notes.append(
            f"nothing stamped an author on this record, so {form.get('author')!r} "
            "out of the paste is what the row records. A record that came "
            "through the site carries the handle the database stamped."
        )

    where = {
        "repo": form.get("artifact_repo", ""),
        "commit": form.get("artifact_commit", ""),
        "path": form.get("artifact_path", ""),
        "host": form.get("artifact_host", ""),
        "url_template": form.get("artifact_url_template", ""),
    }
    # The prompt tells an agent it may `not-found:` the repo and the commit,
    # because the loopback form publishes the bytes itself when they are not
    # anywhere yet. Nothing here can: the site receives no bytes, so a paste
    # with no pin names a file this machine cannot fetch. Refused with what to
    # do about it rather than left to `fetch.commit_sha`, which would say the
    # empty string is not a commit and say nothing about why one is wanted.
    if not where["repo"] or not where["commit"]:
        raise Refused(
            "the paste records no published repo and commit, so there is "
            "nothing to fetch and nothing was written. A submission here is a "
            "pointer to bytes a stranger can fetch. Publish the file and send "
            "the repo, the commit and the path, or take the upload offer on "
            "/submit/, which puts one file in your own account and fills the "
            "pin in."
        )
    # The four the prompt says are optional and checked. Stating one holds the
    # bytes to it, which is `artifact.confirmed`'s job and not this one's; what
    # this does is hand over what the agent said rather than dropping it.
    stated = {name: form[name] for name in ("shape", "dtype", "l2_norm", "sha256")
              if form.get(name)}
    return form, where, stated, agent_handoff.stored_absences(got.absent)


def take(conn: sqlite3.Connection, submission: dict,
         path: Path | None = None, notes: list[str] | None = None) -> dict:
    """One browser-built submission into the corpus, checking the bytes first.

    **Nothing here trusts the record about the bytes.** The submitter states a
    repo, a commit and a path and states nothing about the tensor, and this
    calls `check_link`, which fetches through `controlbun.fetch` exactly the way
    a consumer will and hands what came back to `controlbun.artifact`. So the
    shape, the dtype, the norm and the digest on the row are what the file at
    that commit says, derived by the one thing in this project that reads bytes.
    A submission that names bytes nobody can fetch refuses here with the reason,
    which is the state `DECISIONS.md` 2026-09-20 says the page has to be honest
    about rather than the state it quietly becomes.

    **The namespace is not read out of a field.** `author` on a browser-built
    record is the handle the provider reported, written by
    `astro/src/lib/handshake.mjs` from the capture and never from the form. This
    carries it through and checks nothing about it, because checking it here
    against anything would be this file deciding who somebody is.

    **Two shapes, one path through.** A record carries either the fields
    somebody typed or one block of text their coding agent produced, and
    `SHAPES` says which is which. The paste is parsed here rather than in the
    page, because `agent_handoff.parse` is several hundred lines of liberal-in
    strict-out recovery and a second implementation of it in JavaScript would
    drift from this one. Both branches end at the same `check_link` and the same
    `entry_from`, so there is still one function that writes a submission.

    **There is no review step and nothing to approve.** What this refuses is
    what the schema refuses: a shape with no reader, bytes that do not resolve,
    a contradiction between a value and a reason for having none, and a paste
    the parser will not guess at. None of that is a judgment about the work.

    `notes` collects what had to be decided rather than read, for the caller to
    print. A paste that parses is not the same as a paste that was understood,
    and this list is the only evidence of the difference.
    """
    refuse_credentials(submission, where="the submission")
    said = notes if notes is not None else []
    shape = submission.get("shape")
    if shape not in SHAPES:
        raise Refused(
            f"that file carries shape {shape!r}, and there is no reader for it "
            "here, so nothing was written. This version reads "
            + " and ".join(sorted(SHAPES))
            + ". That is a refusal to write what cannot be read rather than a "
            "statement that the shape is illegitimate."
        )

    if shape == AGENT_PASTE:
        form, where, stated, absent = _from_paste(submission, said)
    else:
        form, where, stated, absent = _from_fields(submission)

    checked = check_link(
        where["repo"], where["commit"], where["path"],
        stated=stated,
        host=where["host"],
        url_template=where["url_template"],
    )
    entry = entry_from(
        form, checked,
        repo=checked.repo, commit=checked.commit,
        host=checked.host, url_template=checked.url_template,
        absent=absent,
    )
    # The row goes in first, for the reason `artifacts/claim.py` gives at the
    # same line: a row with no record line is lost on the next `make site`,
    # which is a rerun of one command, and a record line the database refused
    # is permanent because `replay` stops on a duplicate.
    insert(conn, entry)
    append_record(entry, path)
    return entry


# --------------------------------------------------------------------------- #
# Pulling what the site received into the record the build replays.


# The environment variable the secret key is read from, and it is read from the
# environment and from nowhere else. `.env` holds the project URL and the
# publishable key because the built page carries both by necessity; this one
# bypasses every row-level policy on the project, so it does not go in a file
# that sits in the working tree next to tracked ones. Nothing below prints it,
# logs it, writes it or puts it in an error message.
SECRET_KEY_ENV = "SUPABASE_SECRET_KEY"

# Read from `.env` if it is there, so the author does not restate a value the
# site build already reads from the same place. Overridden by the environment.
PROJECT_URL_ENV = "SUPABASE_URL"

PENDING_TABLE = "pending_submission"


def dotenv(path: Path | None = None) -> dict[str, str]:
    """The repository-root `.env`, which is gitignored and has been from the start.

    The same file `astro/src/pages/signed-in.astro` reads at build time, parsed
    the same way, because a second copy of the project URL is a second place for
    it to disagree.
    """
    path = path or (ROOT / ".env")
    out: dict[str, str] = {}
    try:
        text = path.read_text()
    except OSError:
        return out
    for line in text.splitlines():
        trimmed = line.strip()
        if not trimmed or trimmed.startswith("#") or "=" not in trimmed:
            continue
        name, _, value = trimmed.partition("=")
        out[name.strip()] = value.strip().strip("'\"")
    return out


def credentials(environ: dict[str, str] | None = None,
                env_file: dict[str, str] | None = None) -> tuple[str, str]:
    """The project URL and the secret key, or a refusal naming what is missing.

    Two refusals rather than one, because "it did not work" and "you have not
    set the variable" are different problems and the second one is the whole of
    what usually happened. Neither message carries a value: the key never
    appears in output from this module, including when it is wrong.
    """
    environ = os.environ if environ is None else environ
    env_file = dotenv() if env_file is None else env_file
    url = (environ.get(PROJECT_URL_ENV) or env_file.get(PROJECT_URL_ENV) or "").strip()
    if not url:
        raise Refused(
            f"no {PROJECT_URL_ENV}, in the environment or in .env, so there is "
            "no project to read from. Nothing was written."
        )
    secret = (environ.get(SECRET_KEY_ENV) or "").strip()
    if not secret:
        raise Refused(
            f"{SECRET_KEY_ENV} is not set. It is read from the environment and "
            "from nowhere else, and it is deliberately not in .env: it bypasses "
            "every row-level policy on the project, so it does not live in a "
            "file in the working tree. Set it for the length of this command "
            "and nothing was written in the meantime."
        )
    return url.rstrip("/"), secret


def _ask(url: str, secret: str, *, method: str = "GET", body: bytes | None = None,
         headers: dict[str, str] | None = None) -> tuple[int, bytes]:
    """One request, with the secret key in the headers and never in a message.

    The exception a failure raises names the endpoint, the status and what the
    endpoint said. `urllib` puts the URL in its own messages and the key is in a
    header rather than in the URL, so no path here can put it in output.
    """
    request = urllib.request.Request(url, data=body, method=method)
    request.add_header("apikey", secret)
    request.add_header("Authorization", f"Bearer {secret}")
    for name, value in (headers or {}).items():
        request.add_header(name, value)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.status, response.read()
    except urllib.error.HTTPError as refused:
        said = refused.read().decode("utf-8", "replace")[:400]
        raise Refused(
            f"the project answered {refused.code} to a {method} on "
            f"{PENDING_TABLE}. {said}"
        ) from refused
    except urllib.error.URLError as unreachable:
        raise Refused(
            f"the project could not be reached ({unreachable.reason}). Nothing "
            "was written, here or there."
        ) from unreachable


def pending(url: str, secret: str, *, include_taken: bool = False) -> list[dict]:
    """Every row not yet read in, oldest first.

    Oldest first because that is the order they arrived in and an order has to
    be something. It is not a ranking and it decides nothing: every row is read
    in, and a row's position in this list changes nothing about it.
    """
    query = f"{url}/rest/v1/{PENDING_TABLE}?select=*&order=received_at.asc"
    if not include_taken:
        query += "&taken_at=is.null"
    _, raw = _ask(query, secret)
    rows = json.loads(raw)
    if not isinstance(rows, list):
        raise Refused(
            f"the project answered with {type(rows).__name__} rather than a "
            "list of rows, so nothing here knows what it is holding."
        )
    return rows


def stamped(row: dict) -> tuple[dict, list[str]]:
    """The submission as the author reads it, and where the row disagrees with it.

    **The stamped columns win.** `subject` and `handle` on the row were written
    by Postgres out of the verified session and refused if they disagreed with
    it; `subject` and `author` inside `record` are what the browser put there,
    and a browser's copy of anything is a stranger's JSON. So the record that
    goes into the corpus carries the stamped pair.

    **The disagreement is returned rather than swallowed.** The two should agree
    and one case where they will not is ordinary: the record's `subject` comes
    from Hugging Face's userinfo endpoint at the moment of the capture and the
    stamped one comes from the claims Supabase held for the session, and a
    handle renamed between those two reads is a real difference about a real
    person. Preferring one silently would make that invisible. It is printed,
    and it is not a refusal: there is nothing here for anybody to adjudicate.
    """
    record = row.get("record")
    if not isinstance(record, dict):
        raise Refused(
            f"row {row.get('id')} carries no record object, so there is nothing "
            "to read. Nothing was written."
        )
    subject = row.get("subject") or ""
    handle = row.get("handle") or ""
    if not subject or not handle:
        raise Refused(
            f"row {row.get('id')} has no stamped subject or handle, which the "
            "table refuses to write, so this row did not come through the "
            "insert policy. Nothing was written."
        )
    differs = []
    if record.get("subject") not in (None, subject):
        differs.append(
            f"the record says subject {record.get('subject')!r} and the session "
            f"stamped {subject!r}"
        )
    if record.get("author") not in (None, handle):
        differs.append(
            f"the record says author {record.get('author')!r} and the session "
            f"stamped handle {handle!r}"
        )
    return {**record, "subject": subject, "author": handle}, differs


def mark_taken(url: str, secret: str, row_id: str, at: str) -> None:
    """`taken_at`, which means read in and never means approved.

    Set after the row and the record line are both written, so a run that dies
    between them leaves the row unmarked and the next pull refuses it as a
    duplicate rather than losing it silently.
    """
    _ask(
        f"{url}/rest/v1/{PENDING_TABLE}?id=eq.{urllib.parse.quote(str(row_id))}",
        secret,
        method="PATCH",
        body=json.dumps({"taken_at": at}).encode(),
        headers={"Content-Type": "application/json", "Prefer": "return=minimal"},
    )


def pull(conn: sqlite3.Connection, rows: list[dict], *,
         path: Path | None = None,
         mark=None, at: str | None = None) -> list[dict]:
    """Every pending row into the corpus, through the one function that writes.

    `take` is that function, and it is the same one the author calls on a file
    somebody mailed. So the record and the database cannot come apart and there
    is no second path that writes a row, which is the shape `artifacts/claim.py`
    and `artifacts/publish.py` already use.

    **A refusal stops that row and not the run.** A pin nobody can fetch is one
    submitter's problem and the rows behind it are other people's. The refused
    row keeps `taken_at` null, so it is still there next time and the author can
    write back about it. Refusing is not rejecting: nothing here judges the work,
    and what stops a row is what the schema stops, which `take` documents.

    Returns one dict per row saying what happened, for the caller to print.
    """
    at = at or _now()
    out = []
    for row in rows:
        report: dict = {"id": row.get("id"), "received_at": row.get("received_at"),
                        "handle": row.get("handle"), "notes": []}
        try:
            submission, differs = stamped(row)
            report["differs"] = differs
            entry = take(conn, submission, path, notes=report["notes"])
        except sqlite3.IntegrityError as clash:
            # Not the same thing as a refusal and it gets its own sentence. The
            # corpus already holds this one, which is either a row that was read
            # in by a run that died before it could be marked, or a version
            # string somebody reused. `taken_at` stays null either way: marking
            # it here would assert the record line exists, and whether it does
            # is the thing to go and look at.
            report["refused"] = (
                f"the corpus already holds this submission ({clash}). A "
                "submission is immutable and a correction is a new version, so "
                "this is a row already read in or a version string reused. "
                "Check artifacts/intake.jsonl before marking it by hand."
            )
            out.append(report)
            continue
        except (Refused, ValueError, OSError, fetch.FetchError) as refused:
            # `fetch.FetchError` is on this list because it is a `RuntimeError`
            # rather than a `ValueError`, so a pin the fetcher will not take
            # used to end the whole run instead of the one row it is about. One
            # submitter's unfetchable pin is not the other rows' problem.
            report["refused"] = str(refused)
            out.append(report)
            continue
        report["entry"] = entry
        report["ref"] = registry_ref.format(
            entry["author"], entry["intervention"].get("model_id"),
            entry["label"], entry["version"],
        )
        if mark is not None:
            mark(row.get("id"), at)
            report["taken_at"] = at
        out.append(report)
    return out


def cmd_pull(args) -> int:
    url, secret = credentials()
    rows = pending(url, secret)
    if not rows:
        print("nothing pending. The table is empty of unread rows, which is a "
              "state and not a problem.")
        return 0
    conn = opened(args.db)
    try:
        if args.dry_run:
            results = []
            for row in rows:
                try:
                    _, differs = stamped(row)
                except Refused as refused:
                    results.append({"id": row.get("id"), "refused": str(refused)})
                    continue
                results.append({"id": row.get("id"), "differs": differs,
                                "handle": row.get("handle"),
                                "received_at": row.get("received_at")})
        else:
            results = pull(
                conn, rows, path=args.record,
                mark=lambda row_id, at: mark_taken(url, secret, row_id, at),
            )
    finally:
        conn.close()

    refused = 0
    for result in results:
        print(f"  row       {result['id']}  from {result.get('handle')} "
              f"at {result.get('received_at')}")
        for line in result.get("differs") or []:
            print(f"    stamped identity wins: {line}")
        # What the parser had to decide rather than read, printed even when the
        # row went in. A paste that parses is not the same as a paste that was
        # understood: a definition closed one sentence in fills every field and
        # quietly drops two thirds of the one field that matters most, and
        # these are the only evidence of it.
        for line in result.get("notes") or []:
            print(f"    read as    {line}")
        if result.get("refused"):
            refused += 1
            print(f"    refused   {result['refused']}")
            print("              taken_at is still null, so it is there next time")
            continue
        if args.dry_run:
            print("    would take this row; nothing was written")
            continue
        iv = result["entry"]["intervention"]
        print(f"    wrote     {result['ref']}")
        print(f"    pinned    {iv['artifact_repo']} at {iv['artifact_commit']}, "
              f"path {iv['artifact_path']}")
        print(f"    bytes     sha256 {iv['artifact_sha256']}, shape {iv['shape']}, "
              f"dtype {iv['dtype']}")
        print(f"    taken_at  {result['taken_at']}")

    print()
    if args.dry_run:
        print("nothing was written and no row was marked. Drop --dry-run to "
              "take them.")
    else:
        print(f"{len(results) - refused} written, {refused} refused. The record "
              "is tracked and this is the durable copy. Commit it, then "
              "`make verify` and publish; nothing is on the site until you do.")
    return 0


def opened(path: str) -> sqlite3.Connection:
    """A database that already has the schema, or a sentence saying it does not.

    Migrating here instead would let a mistyped `--db` conjure a database and
    then report success at having written a submission into it, which is a
    worse answer than the traceback it replaces. Same guard and same argument
    as `artifacts/claim.py opened`.
    """
    conn = db.connect(path)
    got = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        ("submission",),
    ).fetchone()
    if not got:
        conn.close()
        raise Refused(
            f"{path} has no `submission` table, so there is nowhere to write. "
            "Build the corpus first with `artifacts/seed.py`, or point --db at "
            "the one you meant. Nothing was written, here or to the record."
        )
    return conn


def cmd_prompt(args) -> int:
    """Write the agent prompt the built page carries.

    Generated rather than re-typed into a template, which is the whole of why
    it is here: the text is a pure function of `agent_handoff.SPECS` and what
    this corpus already holds, so a copy in an Astro page would be a second
    spelling of a document that changes whenever a field does.
    `astro/src/data/controlbun.json` is the precedent, and
    `tests/test_submit_page.py` holds the built page to this file so the two
    cannot come apart.
    """
    conn = opened(args.db)
    try:
        text = agent_handoff.prompt(suggestions(conn))
    finally:
        conn.close()
    out = Path(args.out)
    out.write_text(json.dumps(
        {
            "generated_by": "artifacts/intake.py prompt",
            "prompt": text,
        },
        indent=2,
    ) + "\n")
    print(f"  wrote     {_shown(out)}, {len(text)} characters")
    return 0


def cmd_take(args) -> int:
    given = json.loads(Path(args.file).read_text())
    conn = opened(args.db)
    notes: list[str] = []
    try:
        entry = take(conn, given, args.record, notes=notes)
    finally:
        conn.close()
    iv = entry["intervention"]
    ref = registry_ref.format(entry["author"], iv.get("model_id"),
                              entry["label"], entry["version"])
    for line in notes:
        print(f"  read as   {line}")
    print(f"  wrote     {ref}")
    print(f"  pinned    {iv['artifact_repo']} at {iv['artifact_commit']}, "
          f"path {iv['artifact_path']}")
    print(f"  bytes     sha256 {iv['artifact_sha256']}, shape {iv['shape']}, "
          f"dtype {iv['dtype']}")
    print()
    print("the record is tracked and this is the durable copy. Commit it, then "
          "`make verify` and publish; nothing is on the site until you do.")
    return 0


def main(argv: list[str] | None = None) -> int:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--db", default=str(ROOT / "registry.db"))

    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="command", required=True)

    run = sub.add_parser("serve", parents=[common],
                         help=f"the form, on {HOST} and nowhere else")
    run.add_argument("--port", type=int, default=0,
                     help="0 asks the OS for a free one, which is the default")
    run.add_argument("--repo", default=publish.DEFAULT_REPO,
                     help="the namespace bytes mode publishes to")
    run.add_argument("--no-browser", action="store_true")

    sub.add_parser("replay", parents=[common],
                   help="reinsert everything in the record, after a rebuild")

    said = sub.add_parser(
        "prompt", parents=[common],
        help="write the agent prompt the built page carries")
    said.add_argument("--out", default=str(PROMPT_DATA),
                      help=f"default {PROMPT_DATA.relative_to(ROOT)}, which is tracked")

    took = sub.add_parser(
        "take", parents=[common],
        help="a submission somebody built at /submit/ and handed over")
    took.add_argument("file", help="the JSON file they downloaded")
    took.add_argument("--record", type=Path, default=None,
                      help=f"default {RECORD.relative_to(ROOT)}, which is tracked")

    pulled = sub.add_parser(
        "pull", parents=[common],
        help="every submission the site received, into the tracked record")
    pulled.add_argument("--record", type=Path, default=None,
                        help=f"default {RECORD.relative_to(ROOT)}, which is tracked")
    pulled.add_argument("--dry-run", action="store_true",
                        help="read and report, write nothing and mark nothing")

    args = ap.parse_args(argv)
    if args.command == "serve":
        serve(args.db, args.repo, args.port, open_browser=not args.no_browser)
        return 0
    if args.command in ("take", "pull", "prompt"):
        run = {"take": cmd_take, "pull": cmd_pull, "prompt": cmd_prompt}[args.command]
        try:
            return run(args)
        # `agent_handoff.Refused` beside this module's own, for the reason the
        # loopback handler catches both: the reader is somebody holding a reply
        # from their agent, and the sentence it carries is the entire product
        # of the error path. A traceback here would throw it away.
        except (Refused, agent_handoff.Refused) as refused:
            raise SystemExit(str(refused)) from refused

    conn = db.connect(args.db)
    try:
        for ref in replay(conn):
            print(f"  replayed  {ref}")
    except Refused as refused:
        raise SystemExit(str(refused)) from refused
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
