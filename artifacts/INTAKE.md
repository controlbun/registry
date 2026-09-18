# Getting one artifact into the corpus, from a form on this machine

Premise, restated because a premise stated in one document gets violated in every
other one: the registry never designates, consumers pin, visibly. Nothing in this
form ranks, scores or approves anything. Every field it collects is open, the
suggestions beside them are read out of what the corpus already holds, and the
only things it refuses are bytes it cannot read without running them and rows the
schema will not take.

```
.venv/bin/python artifacts/intake.py serve
```

It prints a URL and opens it. The URL carries a token generated for that run, and
the listener is on 127.0.0.1 and nothing else.

## Why it is not part of the site

`astro.config.mjs` is `output: "static"` and its own comment says why: a build
that emits files cannot drift into being a public surface the way a running
process can. This is a running process, so it carries the same constraint in code
instead.

Four things, all in `tests/test_intake.py`:

- the bind is 127.0.0.1, and there is no flag that changes it
- a per-run token, in the URL and nowhere else
- the `Host` header is checked, because a name that resolves to 127.0.0.1 defeats
  the bind by itself
- `Origin` and `Sec-Fetch-Site` are checked, because a page you did not open, in
  the same browser, can post to a loopback port

The same file also reads `astro/dist` and fails if the built site ever ships a
form, a POST target, a file input or a loopback address. That is the way this
leaks: not somebody rebinding the socket, but a form appearing on the published
site months from now with nothing failing.

A submission route is one of the three capabilities that fire the dual-use trigger
(`DECISIONS.md`, 2026-09-17). The policy does not exist, so the thing that must not
exist is a listener anyone but the operator can reach.

## Reading the form

Every field name carries its own explanation, taken from whatever owns the rule
and citing it: the migration comments in `schema/migrations`, the module
docstrings under `src/registry`, `BRIEF.md`. Point at a name, or tab into the
field, and it opens. It is not a `title` attribute: the input points at the text
with `aria-describedby`, so a screen reader reads it on focus and a keyboard
opens it without a pointer. `tests/test_intake.py` checks that every field has
one and that none of them is hover-only.

Fields the schema stores as nullable are marked "may be empty", which is the only
thing on the page that distinguishes one field from another. Nothing is ranked,
nothing is scored, and the suggestions behind the open fields are still read out
of the corpus.

The readout is the column on the right, and it stays there while the form
scrolls, because the form is a claim and the readout is what the bytes said back.
A refusal lands in the same panel as a reading, in the same type, with the reason
and the module that owns the rule. It is an outcome rather than a fault and is
not colored as one.

Two ids on the page belong to the prompt handoff, which is built elsewhere:
`agent-prompt` and `agent-paste`. Until the routes behind them exist, both say so
in a sentence and the form works without them.

## Two modes, one end state

Both finish as a row pointing at a pinned remote. Neither writes `served_repo`.

**Link.** Paste a Hub repo, a commit and a path. The bytes are fetched into a
throwaway cache, checked, and dropped. What is recorded is the pointer. No size
limit, because nothing is held.

**Bytes.** Drop a file. It is converted to safetensors and checked in a temporary
directory outside this repository, pushed to the namespace in the form through
`artifacts/publish.py upload`, and the staged file is deleted. The row records the
pin. Bytes never rest here.

Above 500 MB, bytes mode refuses and says what the cap is: this form holds the
whole file in memory to digest, sniff, convert and recheck it before anything is
written, and that order is what the check is worth. It is a limit of this form on
this machine and not a statement about the artifact. Link mode has no limit.

## What it shows you before it writes anything

Checking reads the bytes and writes nothing. It prints what it actually read: the
digest, the byte count, the tensor's own name, the shape, the dtype, the norm, and
the header the file carries. If you stated a shape, a dtype, a norm or a digest of
your own, the bytes are held to it and the row keeps what you said; if you stated
nothing, the row records what the bytes say. Saying nothing is not a wrong claim.

Every refusal is a sentence with the reason in it, from whichever module owns the
rule. A pickle is refused by `registry.ingest` and says so. A branch name is
refused by `registry.fetch.commit_sha`. A digest that disagrees is refused by
`registry.artifact`. Nothing is re-decided in the form.

No eval is written. A submission with none is a normal state.

## The record, and `make site`

Rows go into `registry.db` and into `artifacts/intake.jsonl`, which is the copy
that matters. `make site` deletes the database and rebuilds it from
`fixtures/build.py` and `artifacts/seed.py`, so a row written only into a column
is gone on the next build. The record is append-only and tracked, and `insert` is
the one function that turns an entry into rows, so the live write and the replay
cannot come apart. That is the argument `artifacts/published.json` already makes
about two columns, applied to twenty.

After a rebuild:

```
.venv/bin/python artifacts/intake.py replay
```

**`make site` does not call this yet, on purpose.** `falsifier/verify.py` fails a
row whose `artifact_path` has no file on disk, and every row this writes is one of
those: the bytes are at a pinned remote and not here. Wiring the replay into the
build needs that check to learn that a pinned remote with no local copy is a
state rather than a missing file, which is a decision about the falsifier and not
something to slip in through a form.

## Uploading

Bytes mode is the only thing here that needs a credential, and it needs the same
one `artifacts/publish.py` does. `HF_TOKEN` is read from the environment or from
`.env`, printed nowhere, and put on no command line. The upload goes through
`publish.upload`, which refuses this registry's own namespace: bytes there would
be a copy this project serves rather than a thing an author published, which is a
different column and a different question.

`huggingface_hub` is the optional `publish` extra:

```
uv pip install --python .venv/bin/python -e '.[publish]'
```

Link mode needs none of it.
