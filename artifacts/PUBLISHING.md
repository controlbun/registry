# Publishing the real artifacts to the Hub

The four directions under `artifacts/soham/` go to a Hub repo in the author's own
namespace, and the registry records a pinned pointer to them. After that,
`client.load("soham/pro-human@L24").vector()` works without a checkout, because
`fetch.resolve` stops falling through to the local file.

The upload is yours to run. Everything else here does no network write.

## Order

```
.venv/bin/python artifacts/publish.py plan                     # no network at all
.venv/bin/python artifacts/publish.py push --create            # the upload
.venv/bin/python artifacts/publish.py record --commit <40 hex> # the pin
.venv/bin/python artifacts/publish.py verify                   # the round trip
make verify
```

`plan` prints what would go where and stops. Read it before anything else: the
path inside the Hub repo has to equal `artifact_path` exactly, and the plan is
where a mismatch is visible for free rather than as a 404 months later.

`push` needs `huggingface_hub`, which is an optional extra rather than a
dependency of the client:

```
uv pip install --python .venv/bin/python -e '.[publish]'
```

It reads `HF_TOKEN` from the environment or from `.env`, prints it nowhere, and
puts it on no command line. `--create` makes the repo if it is not there;
without it, a missing repo is a refusal rather than a silent creation. The
commit SHA it prints is what `record` wants.

## Uploading by hand instead

`plan` prints the equivalent `hf upload` lines. The web UI works too. Either way
the path inside the repo has to be the full `artifacts/soham/<file>.safetensors`,
not the bare filename.

Then pin what you just pushed:

```
.venv/bin/python artifacts/publish.py record --at-head
```

`--at-head` asks the Hub what `main` points at and freezes the answer. The branch
name is never recorded. If you pushed more than once, pass `--commit` with the
one you mean instead.

## What `verify` does

Fetches every pinned artifact back through `registry.fetch` into a fresh cache
directory, so it is a real download and not a reread of bytes this machine
already has. Then three checks: the bytes are byte identical to the file in this
tree, they satisfy the row's sha256, shape and dtype, and
`client.load(ref).vector()` returns a tensor. Anything else prints `WRONG PIN`
and exits nonzero.

A wrong pin is worse than no pin. The client refuses bytes that disagree with
the record and names the author's own file as the substituted one, so a bad
commit in a row is a published artifact nobody can fetch.

## Three things that are fixed, and why

**The repo is under `sohampadia`, not `controlbun`.** `artifact_repo` is where
the author published a thing. `served_repo` is where this registry serves a copy
from, and `schema/migrations/004` keeps them apart so a mirror that drifted from
its origin is expressible. Nothing here writes `served_repo`. Serving a copy
makes this a distributor and needs the dual-use policy, which is deferred until
a capability arrives (`DECISIONS.md`, 2026-09-17); the author publishing his own
bytes under his own account is not that capability.

**It is a model repo.** `record` writes `https://{host}/{repo}/resolve/{commit}/{path}`
onto the row, which is what the Hub serves models under. That is a default and
not a constraint: since `schema/migrations/007` the layout is a field, so a
dataset repo at `/datasets/{repo}/resolve/...`, a GitHub repo, or a host nobody
here has met is `--url-template` and not a code change.

**The pin is a commit and lives in `artifacts/published.json`.** A branch moves,
so `fetch.commit_sha` refuses anything that is not forty hex characters, and
`record` goes through it. The file is the durable copy: `make site` drops
`registry.db` and rebuilds it, and `artifacts/seed.py` reapplies the pins through
the same function `record` uses.

## After the pin

The local files stay. They are what the falsifier rechecks offline, what
`comparison.load_vector` reads, and the fallback for anyone with a checkout and
no network. `fetch.resolve` prefers the remote once a commit is recorded, which
is the point: the fetch path that only ever took the local branch now gets
exercised.
