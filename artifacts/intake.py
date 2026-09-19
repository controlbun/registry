"""A form on 127.0.0.1 that gets one artifact into the corpus, and its rows with it.

Premise, restated because a premise stated in one document gets violated in every
other one: **plurality is the product; the registry never designates, consumers
pin, visibly.** Nothing here ranks, scores, approves or filters a submission. Every
field it collects is open, the suggestions beside them are read out of what this
corpus already holds, and the only things this refuses are bytes it cannot read
without running them and rows the schema will not take.

**This is not the submission route, and the binding is what makes that true.** It
listens on 127.0.0.1 and on nothing else. There is no `--host`. A submission route
is one of the three capabilities that fire the dual-use trigger (`DECISIONS.md`,
2026-09-17: "anything can be submitted"), and that policy does not exist yet, so
the thing that must not exist is a listener anybody but the operator can reach.
`astro.config.mjs` stays `output: "static"` for the same reason in a different
register, and its comment says it: "a build that emits files cannot drift into
being a public surface the way a running process can". This is a running process,
so it carries the constraint in code rather than in a build flag: the loopback
bind, a per-run token in the URL, a `Host` header check and an `Origin` check,
because a browser on this machine will happily post to 127.0.0.1 on behalf of a
page the operator did not open. `tests/test_intake.py` holds all four.

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

**Nothing in this file decides what an artifact may be.** `registry.ingest` owns
the question of which bytes can be read without executing them and answers it with
an open converter set. `registry.artifact` owns the comparison between a claim and
the bytes. `registry.fetch` owns the rule that a pin is a commit. This file owns a
form, a socket and two INSERTs, and every rule it appears to apply is one of those
three being called.

**`artifacts/intake.jsonl` is the durable record, and the reason is the reason
`published.json` exists.** `make site` deletes `registry.db` and rebuilds it from
`fixtures/build.py` and `artifacts/seed.py`, so a row written only into the
database is gone on the next build. The record is append-only and tracked; `insert`
is the one function that turns an entry into rows, and both the live write and
`replay` call it, so the two cannot come apart. Nothing in the `Makefile` calls
`replay` yet: the falsifier fails a row whose `artifact_path` has no file on disk,
and every row this writes is one of those, so wiring the replay into the build
needs that check to learn that a pinned remote with no local copy is a state.
That is a decision for the author, not something to slip in here.

    .venv/bin/python artifacts/intake.py serve
    .venv/bin/python artifacts/intake.py replay
"""

from __future__ import annotations

import argparse
import html
import json
import secrets
import shutil
import sqlite3
import sys
import tempfile
import threading
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

from registry import artifact, db, fetch, ingest  # noqa: E402
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
    """
    iv = entry["intervention"]
    conn.execute(
        "INSERT INTO submission (author,label,version,definition,created_at,"
        "is_synthetic) VALUES (?,?,?,?,?,0)",
        (entry["author"], entry["label"], entry["version"], entry["definition"],
         entry["created_at"]),
    )
    columns = (
        "id", "kind", "model_id", "model_revision", "layer", "layer_convention",
        "hook_point", "chat_template_hash", "shape", "dtype", "l2_norm",
        "activation_norm", "coeff_low", "coeff_high", "steering_position",
        "license_status", "artifact_repo", "artifact_commit", "artifact_host",
        "artifact_url_template", "artifact_path", "artifact_sha256",
    )
    conn.execute(
        "INSERT INTO intervention (author,label,version,is_synthetic,"
        + ",".join(columns) + ") VALUES (?,?,?,0," + ",".join("?" * len(columns)) + ")",
        (entry["author"], entry["label"], entry["version"],
         *(iv.get(c) for c in columns)),
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
        ref = f"{entry['author']}/{entry['label']}@{entry['version']}"
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

    Every field optional, which is `registry.artifact.Claim`'s design and not a
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
    `registry.fetch`'s: forty hex characters, a commit that survives into the
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
        # `registry.fetch` and two requests swapping it at once would restore
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


def check_bytes(blob: bytes, filename: str, path: str,
                stated: dict[str, str], tensor: str = "") -> Checked:
    """Convert and check a dropped file, outside this repository.

    `root=` points `registry.ingest` at a temporary directory, so the checked
    safetensors lands there rather than in the tree. The containment rule still
    applies inside it, which is why the argument is a root and not a bypass: a
    `path` with a `..` in it is refused against the staging directory exactly as
    it would be against the repository.

    Everything about which bytes are readable is `registry.ingest`'s, including
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
               host: str | None = None, url_template: str | None = None) -> dict:
    """One form submission as the record line that will be replayed forever.

    The tensor facts come off `checked` and never off the form, because they are
    what the bytes say. Where the operator stated one, `artifact.confirmed` has
    already kept the stated value and proved the bytes agree with it, which is
    `_keep_the_claim`'s whole argument: a citation the bytes confirm is worth
    more than a number derived from the bytes it is compared against.
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
# value rather than typed here: `registry.fetch` for the Hub's layout, which is
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
    body: JSON.stringify({ handle, fields: fields() }),
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
  const notes = res.body.notes || [];
  agentSays(filled + ' fields filled from the paste. Every one of them is still '
    + 'editable, and nothing is checked until you check the bytes.'
    + (notes.length ? ' Read these before you check: they are what the parser '
       + 'had to work out rather than read, and a value it worked out wrong '
       + 'looks exactly like one it read.' : ''), notes);
});
"""


# Every sentence here comes from whatever owns the rule, and names it, so the
# reader can go and check rather than take this page's word: the comments in
# `schema/migrations`, the module docstrings under `src/registry`, `BRIEF.md`, and
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
        "host this names: <code>registry.fetch</code> requires the commit to "
        "survive into the URL, because that is what a pin is, and refuses a "
        "scheme a fetch cannot happen over, because a pin that resolves only on "
        "the machine that wrote it is not one anybody else can check.",
    "link_commit":
        "Forty hex characters. <code>registry.fetch</code> resolves by commit "
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
        "<code>registry.ingest</code> owns which bytes can be read without "
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
        "For the source model. A steering vector is derived from model weights, "
        "so what that model's license permits for derived artifacts is the "
        "question, and unresolved redistribution rights mean the artifact cannot "
        "be served.",
}

# Where each explanation above comes from, kept apart from the text so the page
# can always put it last, whatever else got appended to the sentence.
SOURCE = {
    "link_repo": "artifacts/INTAKE.md",
    "link_host": "schema/migrations/007_any_host.sql",
    "link_url_template": "schema/migrations/007_any_host.sql",
    "link_commit": "src/registry/fetch.py",
    "link_path": "artifacts/intake.py",
    "file": "src/registry/ingest.py",
    "bytes_repo": "artifacts/publish.py",
    "bytes_path": "artifacts/intake.py",
    "bytes_tensor": "src/registry/ingest.py",
    "shape": "src/registry/artifact.py",
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

    `registry.fetch.CACHE` is a module global that `check_link` swaps and
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
                           host=host, url_template=url_template)
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
            ("recorded in", f"{_shown(RECORD)}, so it survives the rebuild "
                            "that drops registry.db"),
            ("still to do", "make site does not replay the record yet. Until it "
                            "does, run `artifacts/intake.py replay` after a "
                            "rebuild."),
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

    args = ap.parse_args(argv)
    if args.command == "serve":
        serve(args.db, args.repo, args.port, open_browser=not args.no_browser)
        return 0

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
