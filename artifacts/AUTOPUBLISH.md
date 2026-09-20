# Publishing what `/submit/` received, with nobody typing anything

> **Status 2026-09-20.** Live, and the instructions below are to be acted on.
> The launchd agent is not installed by anything in the repository: it is
> installed by running `make autopublish-install`, once, on purpose.

Premise, restated because a premise stated in one document gets violated in
every other one: the registry never designates, consumers pin, visibly. Nothing
in this pipeline reads a submission, ranks one, holds one back or decides
whether one is worth publishing. It moves rows the site already accepted into
the corpus the site already serves.

**There is no review step and there will not be one.** A stranger's text goes
live under your name and your domain before you have read it. That is the
decision, it is recorded in `DECISIONS.md` 2026-09-20 with what it forecloses,
and it is not a gap for somebody to close later.

## Install it

Two commands, in this order.

**Store the key.** The Supabase secret key bypasses every row-level policy on
the project, so it lives in the login Keychain and in no file. `-w` last and
with no value prompts for it, which keeps it out of shell history. `-U` updates
an item that is already there, which a second run without it would fail on.

```
security add-generic-password -U -a "$USER" -s controlbun-supabase -w
```

**Install the agent.**

```
make autopublish-install
```

That renders `artifacts/com.controlbun.autopublish.plist` with this machine's
paths, writes it to `~/Library/LaunchAgents/com.controlbun.autopublish.plist`,
lints it and bootstraps it into your GUI domain. It fires every fifteen minutes,
starting within fifteen minutes of the install rather than immediately.

**Then run one pull by hand, from a terminal, while you are sitting there.**

```
make pull-dry
```

The first time anything reads that Keychain item, macOS raises an access prompt.
Choose **Always Allow**. Do this before the agent's first firing: a prompt with
nobody at the keyboard is a job that waits, and the read has a twenty second
timeout precisely so that it fails and says so rather than sitting on the lock.

## The commands

```
make pull-dry              read the table, report, write nothing, mark nothing
make pull                  read the table into artifacts/intake.jsonl
make deploy                gate, then push main and gh-pages
make autopublish-now       fire the job once, now
make autopublish-stop      stop the agent
```

`make deploy` is the sequence `GO-LIVE.md` section 4 has you typing by hand. It
runs `make verify` itself, refreshes `/private/tmp/pages` from `astro/dist`,
commits the built site onto `gh-pages`, and pushes `main` and `gh-pages` in one
`git push`. One push rather than two, so the pre-push hook runs the gate once
more and diffs the pushed tree against the `astro/dist` that just passed, and so
the built site and the source it was built from go out together.

It refuses a dirty tree, a checkout that is not on `main`, and a checkout whose
`core.hooksPath` is not this repository's `hooks/`. Run `make hooks` if it says
the last one.

## What the job does, in order

1. Takes a lock, or says which pid has it and stops.
2. Refuses a working tree with changes it did not make.
3. Refuses an unwired pre-push hook, and a checkout not on `main`.
4. Reads the key out of the Keychain, with a timeout.
5. Runs `artifacts/intake.py pull`. A row the schema refuses stops that row and
   not the run, keeps `taken_at` null, and is there again next time.
6. If the record gained no lines: no commit, no push, no deploy, and no line in
   the log unless the outcome differs from the last one.
7. Runs `make verify`. Red means nothing is committed and nothing is pushed.
8. Refuses if a tracked file changed that is not one of the three it stages.
9. Stages those three by name and commits. Never `git add -A`.
10. Pushes `main` and `gh-pages`, which runs the gate again in the hook.
11. Says what published, in the log and in a notification.

The three paths it stages, and nothing else:

```
artifacts/intake.jsonl
astro/src/data/controlbun.json
astro/src/data/agent-prompt.json
```

## Where to look

```
~/Library/Logs/controlbun/autopublish.log
```

Everything the job prints and everything `make` prints inside it, in the order
it happened. A run that published nothing writes nothing, so the file grows with
events rather than with firings, and there is no rotation because there is
nothing to rotate.

Beside it, `autopublish.lock` while a run is in progress, and
`last-outcome.sha256`, which is how a refused row is reported once instead of
four times an hour.

```
launchctl print gui/$(id -u)/com.controlbun.autopublish
```

Shows whether the agent is loaded, when it last ran and what it exited with.

## Stopping it

```
make autopublish-stop
```

That is `launchctl bootout gui/$(id -u)/com.controlbun.autopublish`. It stops
firing immediately. The plist stays at
`~/Library/LaunchAgents/com.controlbun.autopublish.plist`; delete that file too
if you want it gone rather than stopped.

Stop it before a long session in this checkout if you would rather not think
about it. The job's lock keeps two firings apart and keeps a firing off another
firing's build, but **a bare `make verify` that you run yourself takes no lock**
and cannot be made to: `hooks/pre-push` runs `make verify` inside a push the job
already holds the lock for, so a lock on that target would deadlock the deploy.
What protects you instead is the dirty-tree refusal, which is why it comes
before anything else.

## Taking something down

Nothing here is an erasure and the document says so rather than implying
otherwise. The corpus is a file in git, the deploy branch is a git history, and
both are public and cloneable. Removing a submission is a new commit that stops
serving it, not the disappearance of what was served.

1. Stop the agent, so nothing publishes underneath you.

   ```
   make autopublish-stop
   ```

2. Remove the entry's line from `artifacts/intake.jsonl`. The record is the
   durable copy and `make site` rebuilds the database from it, so a line removed
   there is a row that does not come back.

3. Rebuild and redeploy.

   ```
   make deploy
   ```

4. The row in `pending_submission` still carries `taken_at`, so it is not pulled
   again. If you want it pulled again later, clear that column.

What none of that does: unpublish. The commit that carried it is still in
`main`, the built page is still in the `gh-pages` history, and anybody who
cloned either still has both. If the text has to be gone rather than
unserved, that is a history rewrite on a public repository, and it is a
different job from this one.

## When it goes wrong

**"the Keychain did not answer within 20s"** An access prompt is waiting and
nobody clicked it. Run `make pull-dry` from a terminal and choose Always Allow.
If it recurs after that, the item's access control was replaced; store it again
with the `security add-generic-password` line above, which resets it.

**"no Keychain item for service 'controlbun-supabase'"** It was never stored, or
it was stored under a different account. The refusal prints the line to run.

**"the working tree is not clean"** The message says which case it is. If every
path listed is one of the three the job stages, a previous run pulled and then
hit a red gate: the rows are in the record and the log says what failed. If
anything else is listed, something of yours is uncommitted.

**"another run holds ... (pid N)"** A firing overlapped a long build. It stops
and the next one picks up. If the pid is not running, the next firing clears the
lock itself and says so.

**"`make verify` failed"** The rows are in `artifacts/intake.jsonl` and nothing
was committed or pushed. The tree stays dirty on purpose, so the next firing
refuses rather than committing on top of a build that did not pass. Read the
log, fix it, and run `make deploy`.

**"a path this job does not stage changed"** The build started writing a fourth
tracked file. Nothing was committed. Decide whether it belongs in `STAGED` in
`artifacts/autopublish.py` and add it deliberately.

**The pull needs a database.** `artifacts/intake.py pull` writes into
`registry.db`, which is gitignored and built by `make site`. On a fresh clone,
run `make verify` once before the first pull.
