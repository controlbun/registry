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

    link    paste a repo, a commit and a path. The bytes are fetched into a
            throwaway cache, checked, and dropped. What is kept is the pointer.
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
import publish  # noqa: E402

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
        "license_status", "artifact_repo", "artifact_commit", "artifact_path",
        "artifact_sha256",
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


def check_link(repo: str, commit: str, path: str, stated: dict[str, str]) -> Checked:
    """Fetch a pinned file, check it, keep the pointer and drop the bytes.

    Through `fetch.resolve`, which is the consumer path verbatim: what an
    operator wants confirmed is that `client.load` will get these bytes on a
    machine with no checkout, and the way to confirm that is to take the same
    branch it takes. The cache is swapped for a throwaway first, so this is a
    real download rather than a reread and so nothing is left behind. That is
    `artifacts/publish.py verify`'s trick and the reason is the same one.
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

    with tempfile.TemporaryDirectory(prefix="registry-intake-") as tmp:
        # Serialized by the caller's lock: this is a module global in
        # `registry.fetch` and two requests swapping it at once would restore
        # each other's value.
        was, fetch.CACHE = fetch.CACHE, Path(tmp)
        try:
            blob = fetch.resolve(artifact_path=path, artifact_repo=repo,
                                 artifact_commit=commit)
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
        where=f"{fetch.HUB}/{repo} at {commit}, path {path}. Fetched, checked, "
              "and not kept: what this records is the pointer.",
        facts=facts,
        tensor_name=_tensor_name(blob),
        header=artifact.metadata_of(blob),
        stated={k: v for k, v in stated.items() if v},
        repo=repo, commit=commit, path=path,
    )


def check_bytes(blob: bytes, filename: str, path: str,
                stated: dict[str, str]) -> Checked:
    """Convert and check a dropped file, outside this repository.

    `root=` points `registry.ingest` at a temporary directory, so the checked
    safetensors lands there rather than in the tree. The containment rule still
    applies inside it, which is why the argument is a root and not a bypass: a
    `path` with a `..` in it is refused against the staging directory exactly as
    it would be against the repository.

    Everything about which bytes are readable is `registry.ingest`'s, including
    the refusals. Nothing is re-decided here.
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
               repo: str, commit: str) -> dict:
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
}


def suggestions(conn: sqlite3.Connection) -> dict[str, list[str]]:
    """What this corpus already holds, per field. Never a constraint."""
    out: dict[str, list[str]] = {}
    for field, sql in SUGGEST.items():
        try:
            out[field] = [r[0] for r in conn.execute(sql)]
        except sqlite3.Error:
            out[field] = []
    return out


# --------------------------------------------------------------------------- #
# The page.


STYLE = """
:root { color-scheme: light dark; }
* { box-sizing: border-box; }
body { font: 15px/1.55 ui-sans-serif, system-ui, sans-serif; margin: 0;
       padding: 2rem 1.5rem 6rem; max-width: 52rem; }
h1 { font-size: 1.3rem; margin: 0 0 .25rem; }
h2 { font-size: .95rem; text-transform: uppercase; letter-spacing: .08em;
     margin: 2.25rem 0 .75rem; opacity: .65; }
p.note { opacity: .75; margin: .35rem 0 0; }
fieldset { border: 1px solid; border-color: color-mix(in srgb, currentColor 22%, transparent);
           border-radius: 6px; padding: 1rem 1.1rem 1.2rem; margin: 0 0 1rem; }
legend { padding: 0 .4rem; font-weight: 600; }
label { display: block; margin: .8rem 0 0; }
label > span { display: block; font-weight: 600; font-size: .85rem; }
label > em { display: block; font-style: normal; opacity: .7; font-size: .82rem;
             margin-bottom: .25rem; }
input, textarea, button { font: inherit; width: 100%; padding: .45rem .55rem;
                          border-radius: 5px;
                          border: 1px solid color-mix(in srgb, currentColor 30%, transparent);
                          background: transparent; color: inherit; }
textarea { min-height: 7rem; }
button { width: auto; cursor: pointer; padding: .5rem 1.1rem; font-weight: 600; }
.row { display: grid; grid-template-columns: 1fr 1fr; gap: 0 1rem; }
.modes { display: flex; gap: 1.25rem; margin-bottom: .5rem; }
.modes label { display: flex; gap: .4rem; align-items: center; margin: 0; }
.modes input { width: auto; }
.panel { margin-top: 1.25rem; padding: 1rem 1.1rem; border-radius: 6px;
         border: 1px solid color-mix(in srgb, currentColor 30%, transparent); }
.panel[hidden] { display: none; }
dl.facts { display: grid; grid-template-columns: 10rem 1fr; gap: .3rem 1rem;
           margin: .5rem 0 0; font-family: ui-monospace, monospace; font-size: .84rem; }
dl.facts dt { opacity: .65; }
dl.facts dd { margin: 0; overflow-wrap: anywhere; }
.refused { border-color: currentColor; }
.refused strong { display: block; margin-bottom: .35rem; }
pre { white-space: pre-wrap; margin: 0; font-size: .84rem; overflow-wrap: anywhere; }
footer { margin-top: 3rem; opacity: .7; font-size: .86rem; }
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

function refuse(where, text) {
  const box = q(where);
  box.hidden = false;
  box.className = 'panel refused';
  box.innerHTML = '<strong>Refused</strong><pre></pre>';
  box.querySelector('pre').textContent = text;
}

function facts(where, payload) {
  const box = q(where);
  box.hidden = false;
  box.className = 'panel';
  const dl = document.createElement('dl');
  dl.className = 'facts';
  for (const [k, v] of payload.display) {
    const dt = document.createElement('dt');
    dt.textContent = k;
    const dd = document.createElement('dd');
    dd.textContent = v;
    dl.append(dt, dd);
  }
  box.replaceChildren(dl);
}

let handle = null;

async function post(path, options) {
  const res = await fetch(path + (path.includes('?') ? '&' : '?') + 'k=' + key,
                          Object.assign({ method: 'POST' }, options));
  const text = await res.text();
  let body;
  try { body = JSON.parse(text); } catch (e) { body = { refused: text }; }
  return { ok: res.ok, body };
}

q('check').addEventListener('click', async () => {
  handle = null;
  q('write').disabled = true;
  q('written').hidden = true;
  const m = modeOf();
  q('checked').hidden = false;
  q('checked').className = 'panel';
  q('checked').textContent = 'checking\\u2026';
  let res;
  if (m === 'link') {
    res = await post('/check', {
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ mode: 'link', fields: fields() }),
    });
  } else {
    const file = q('file').files[0];
    if (!file) { refuse('checked', 'No file chosen.'); return; }
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
  q('written').hidden = false;
  q('written').className = 'panel';
  q('written').textContent = 'writing\\u2026';
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
"""


def _field(name: str, title: str, note: str, *, value: str = "",
           suggest: list[str] | None = None, area: bool = False) -> str:
    listid = f"sug-{name}" if suggest else ""
    attrs = f' list="{listid}"' if suggest else ""
    control = (
        f'<textarea data-field="{name}" id="f-{name}"></textarea>'
        if area else
        f'<input data-field="{name}" id="f-{name}" value="{html.escape(value)}"'
        f' spellcheck="false" autocomplete="off"{attrs}>'
    )
    options = ""
    if suggest:
        options = f'<datalist id="{listid}">' + "".join(
            f'<option value="{html.escape(s)}">' for s in suggest
        ) + "</datalist>"
    return (
        f'<label for="f-{name}"><span>{html.escape(title)}</span>'
        f'<em>{html.escape(note)}</em>{control}{options}</label>'
    )


def page(conn: sqlite3.Connection, *, token: str, repo: str, origin: str) -> bytes:
    s = suggestions(conn)
    cap = BYTES_CAP // (1024 * 1024)

    where = (
        '<h2>Where the bytes are</h2>'
        '<div class="modes">'
        '<label><input type="radio" name="mode" value="link" checked> '
        'Link: they are already published somewhere</label>'
        '<label><input type="radio" name="mode" value="bytes"> '
        'Bytes: I have the file here</label>'
        '</div>'

        '<fieldset id="link-fields"><legend>Link</legend>'
        '<p class="note">Fetched once into a throwaway cache, checked, and '
        'dropped. What is recorded is the pointer.</p>'
        + _field("link_repo", "Hub repo", "owner/name, a model repo.")
        + _field("link_commit", "Commit",
                 "Forty hex characters. A branch or a tag is refused, because "
                 "whoever owns the repo can move one.")
        + _field("link_path", "Path in the repo",
                 "Recorded as artifact_path verbatim. fetch.resolve hands one "
                 "path field to the remote, so these are the same string.")
        + '</fieldset>'

        '<fieldset id="bytes-fields" hidden><legend>Bytes</legend>'
        f'<p class="note">Read here, converted to safetensors, checked outside '
        f'this repository, then pushed to the namespace below and deleted. '
        f'Nothing rests here. This form holds the whole file in memory while it '
        f'checks it, so it takes up to {cap} MB; that is a cap on this form on '
        f'this machine and says nothing about the artifact. Above it, publish '
        f'the bytes wherever you already publish and use link mode, which has '
        f'no size limit at all.</p>'
        '<label for="f-file"><span>File</span>'
        '<em>Anything registry.ingest has a converter for. A format nobody '
        'wrote one for is refused with a sentence naming what has one and '
        'where another goes.</em>'
        '<input type="file" id="file"></label>'
        + _field("bytes_repo", "Publish to", "The author's own Hub namespace. "
                 "Never this registry's, which would be a served copy.",
                 value=repo)
        + _field("bytes_path", "Path in the repo",
                 "Also the row's artifact_path, character for character.")
        + _field("bytes_message", "Commit message", "What the upload says it is.",
                 value="Publish one steering artifact")
        + '</fieldset>'
    )

    stated = (
        '<h2>What you state about the bytes</h2>'
        '<p class="note">All optional and all checked. State one and the bytes '
        'are held to it and the row keeps what you said; state nothing and the '
        'row records what the bytes say. Saying nothing is not a wrong claim.</p>'
        '<div class="row">'
        + _field("shape", "shape", "As the row will hold it, e.g. a bracketed list.")
        + _field("dtype", "dtype", "As numpy spells it.")
        + _field("l2_norm", "l2_norm", "Cited from wherever you got it.")
        + _field("sha256", "sha256", "Of the whole file, header included.")
        + '</div>'
    )

    submission = (
        '<h2>The submission</h2>'
        '<div class="row">'
        + _field("author", "author", "Your namespace. Free to claim.",
                 suggest=s["author"])
        + _field("label", "label", "Free to claim, and other people may claim it too.",
                 suggest=s["label"])
        + _field("version", "version", "author/label@version freezes to this forever.")
        + _field("created_at", "created_at", "When the work happened.", value=_now())
        + '</div>'
        + _field("definition", "definition",
                 "Your own theory of the trait, in prose. This is the thing "
                 "somebody else disagrees with.", area=True)
    )

    intervention = (
        '<h2>The intervention</h2>'
        '<div class="row">'
        + _field("intervention_id", "id", "Primary key. What an eval or an attack "
                 "will point at.")
        + _field("kind", "kind", "Open string.", suggest=s["kind"])
        + _field("model_id", "model_id", "Base and instruct are different models.",
                 suggest=s["model_id"])
        + _field("model_revision", "model_revision",
                 "Leave empty if nobody recorded it. Empty reads as not recorded, "
                 "which is not the same as unknown and much better than a sha "
                 "the model happens to have today.")
        + _field("layer", "layer", "An integer.")
        + _field("layer_convention", "layer_convention",
                 "Getting this wrong is silent.", suggest=s["layer_convention"])
        + _field("hook_point", "hook_point", "Open string.", suggest=s["hook_point"])
        + _field("chat_template_hash", "chat_template_hash",
                 "Empty if none was applied.")
        + _field("activation_norm", "activation_norm",
                 "Only if a coefficient here is a fraction of activation "
                 "magnitude. Empty otherwise.")
        + _field("coeff_low", "coeff_low", "Empty if you did not sweep one.")
        + _field("coeff_high", "coeff_high", "Empty if you did not sweep one.")
        + _field("steering_position", "steering_position", "Open string.",
                 suggest=s["steering_position"])
        + _field("license_status", "license_status",
                 "A steering vector is derived from model weights, so what the "
                 "model's license permits for derived artifacts is the question.",
                 suggest=s["license_status"])
        + '</div>'
    )

    body = (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="robots" content="noindex,nofollow">'
        '<title>intake, local only</title>'
        f'<style>{STYLE}</style></head>'
        f'<body data-k="{html.escape(token)}">'
        '<h1>intake</h1>'
        f'<p class="note">Running on {html.escape(origin)} and reachable from '
        'nowhere else. This is the operator tool, not a submission route: '
        'nothing can be submitted to this registry, and that is what the '
        'dual-use policy is waiting on. Both modes end the same way, as a row '
        'pointing at a pinned remote. Nothing here writes a served copy.</p>'
        + where + stated + submission + intervention +
        '<h2>Check, then write</h2>'
        '<p class="note">Checking reads the bytes and writes nothing. It shows '
        'what it actually read, so you can disagree with it before anything is '
        'recorded.</p>'
        '<p><button type="button" id="check">Check the bytes</button> '
        '<button type="button" id="write" disabled>Write the rows</button></p>'
        '<div class="panel" id="checked" hidden></div>'
        '<div class="panel" id="written" hidden></div>'
        '<footer>No eval is written here, and a submission with none is a '
        'normal state rather than an incomplete one. Rows go into registry.db '
        'and into artifacts/intake.jsonl, which is the copy that survives '
        '<code>make site</code>.</footer>'
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
        except Refused as refused:
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
            )
        else:
            payload = json.loads(self._body(1 << 20) or b"{}")
            form = payload.get("fields", {})
            checked = check_link(
                repo=_text("Hub repo", form.get("link_repo"),
                           why="owner/name, the repo the artifact is published in."),
                commit=_text("commit", form.get("link_commit"),
                             why="Forty hex characters."),
                path=form.get("link_path", "").strip(),
                stated=self._stated(form),
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
                     "link_path": checked.path},
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
            published = f"pushed to {repo} at {commit}, {url}"
        else:
            repo, commit = checked.repo, checked.commit
            published = (f"already at {repo} at {commit}; nothing was uploaded "
                         "and no copy was made")

        entry = entry_from(form, checked, repo=repo, commit=commit)
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
