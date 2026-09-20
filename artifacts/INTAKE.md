# Getting one artifact into the corpus, from a form on this machine

> **Status 2026-09-20.** Live. The loopback form is still how an artifact the
> author is entering himself gets into the corpus. What changed on 2026-09-20 is
> that it is no longer the only way in: the published site now sends a
> submission to Postgres, and `intake.py pull` reads it from there.

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

The same file also reads `astro/dist`, and what it looks for there changed on
2026-09-20. It used to fail if the built site shipped a form or a POST target of
any kind. The site now sends a submission, so the question a guard can usefully
ask is where a request is aimed rather than whether one exists. `ALWAYS_REFUSED`
still fails the build on a loopback address, a `sendBeacon` or a multipart post;
`MAY_SEND_TO` names every destination the site's own script can reach and why,
so a new one is an edit somebody made rather than a line that arrived; and
`test_nothing_on_the_site_posts_to_this_site` holds the original property, which
is that a build emitting files runs no route and cannot be posted to.

That is still the way this leaks. Not somebody rebinding the socket, but a
request appearing on the published site months from now with nothing failing.

**Why the bind stays loopback, now that the reason it was written down is gone.**
This paragraph used to say a submission route fires one of the three dual-use
capability triggers, so the listener must be unreachable until the policy exists.
`DECISIONS.md` 2026-09-19 lifted those triggers and decided no policy is
required, and a submission route exists on the public site. The constraint here
survives on its own footing: this process writes to the corpus the build
replays, with no identity behind it and nothing stamping who sent what. The
published path has Postgres stamping the sender from a verified session, which
is the property that makes it safe to expose. This one has nothing of the kind,
so it stays where only the person running it can reach it.

## Reading the form

Every field name carries its own explanation, taken from whatever owns the rule
and citing it: the migration comments in `schema/migrations`, the module
docstrings under `src/controlbun`, `BRIEF.md`. Point at a name, or tab into the
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

**Link.** Paste a repo, a commit and a path. The bytes are fetched into a
throwaway cache, checked, and dropped. What is recorded is the pointer. No size
limit, because nothing is held.

Two further fields say which host that repo is on and how the four values become
a URL, and both may be empty. Empty means the Hub, which is where every row
written before `schema/migrations/007` resolves. They are free text with
suggestions rather than a menu, for the reason `controlbun.ingest.PinnedRepoFile`
gives: a table of the hosts we happen to have met would be a list of where an
artifact is allowed to come from. What is checked is not which host they name.
`controlbun.fetch` requires the commit to survive into the URL, because that is
what a pin is, and refuses a scheme a fetch cannot happen over, because a pin
that resolves only on the machine that wrote it is not one anybody else can
check.

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
rule. A pickle is refused by `controlbun.ingest` and says so. A branch name is
refused by `controlbun.fetch.commit_sha`. A digest that disagrees is refused by
`controlbun.artifact`. Nothing is re-decided in the form.

No eval is written. A submission with none is a normal state.

## What was looked for and is not there

An absence is a positive statement with a reason, never an omission. The prompt
handoff asks for one on a `not-found:` line, which takes the field name and the
sentence, and the boxes those come back in sit under the paste region. Edit them,
or clear one to drop it. They are recorded beside the row and render next to the
absence on the page.

The field name is an open string. `schema/migrations/008` keys a reason to
whatever it is about and nothing enumerates which fields may carry one, so a
reason about something this form has no box for is stored and shown rather than
refused.

Most absences have no reason and never will, and that is not a lesser record. An
absence nobody accounted for renders exactly as it did before the table existed:
the field says absent and says nothing else.

A value and a reason for the same field is refused. Those are two claims about
one field and nothing here can tell which was meant, so neither is written and
the refusal names the field. Preferring either would delete one of your two
sentences without saying so.

## The record, and `make site`

Rows go into `registry.db` and into `artifacts/intake.jsonl`, which is the copy
that matters. `make site` deletes the database and rebuilds it from
`artifacts/seed.py`, so a row written only into a column
is gone on the next build. The record is append-only and tracked, and `insert` is
the one function that turns an entry into rows, so the live write and the replay
cannot come apart. That is the argument `artifacts/published.json` already makes
about two columns, applied to twenty.

`make site` calls the replay itself, between the two seeders and the export:

```
.venv/bin/python artifacts/intake.py replay
```

That was a manual step for exactly as long as `falsifier/verify.py` failed any
row whose `artifact_path` has no file on disk, which every row this writes is:
the bytes are at a pinned remote and not here. `_pinned` tells a pin apart from
a missing file, and the run prints how many rows it did not recheck. See
`DECISIONS.md` 2026-09-19.

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
