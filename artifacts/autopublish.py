"""What `/submit/` received, on the site, with nobody typing anything.

Premise, restated because a premise stated in one document gets violated in every
other one: **plurality is the product; the registry never designates, consumers
pin, visibly.** Nothing here reads a submission, ranks one, holds one back or
decides whether one is worth publishing. It moves rows the site already accepted
into the corpus the site already serves. The only things that stop a row are the
things `artifacts/intake.py take` already stops, and they stop one row rather
than the run.

**There is no review step and adding one is not a fix for anything here.** The
owner decided on 2026-09-20 that publishing is automatic end to end, knowing that
a stranger's text goes live under his name and his domain before he has read it.
`DECISIONS.md` carries that decision, what it forecloses and the two things it
does not solve. An approval flag, a hold queue or a quality check added to this
file would reverse it silently, which is the one way this design is known to go
wrong.

**What this is instead of a safeguard: refusals that are about the machine.**
Every refusal below is about whether it is safe to run at all, never about
whether a submission is any good:

    the tree is dirty            somebody is mid-edit, or a previous run failed
    another run holds the lock   two builds in one checkout is a mess
    no key in the Keychain       there is nothing to read the table with
    the Keychain did not answer  a prompt is waiting and nobody is there
    the hook is not wired        a push would not run the gate
    HEAD is not the source branch    a deploy from a worktree is a mistake
    the gate failed              nothing is pushed and the failure is loud
    a file changed that this does not stage   never `git add -A`

**The gate runs in the same run as the deploy, twice, and that is deliberate.**
`deploy` runs `make verify` itself, so a red gate stops before anything is
committed. `hooks/pre-push` runs it again on the push and diffs the pushed tree
against the `astro/dist` that just passed. The build is byte-deterministic, which
is what makes the second check meaningful rather than flaky: an unchanged corpus
produces an identical `astro/dist`, file for file, so a mismatch means the tree
being pushed is not the tree that was gated.

**The secret key bypasses every row-level policy on the project**, so it is read
from the login Keychain at the moment it is needed, put into one child process's
environment, and never written, printed or logged. `artifacts/intake.py` reads it
from the environment and from nowhere else, which is the other half of the same
rule. The read has a timeout because a Keychain access prompt with nobody at the
keyboard is a job that hangs, and a hang is worse than a failure: nothing
notifies, nothing logs, and the lock stays held.

    make pull-dry            read the table, write nothing
    make pull                read the table into the tracked record
    make deploy              gate, then push the source and the built site
    make autopublish-install install the launchd job
    make autopublish-stop    stop it

`artifacts/AUTOPUBLISH.md` is the operator document: the Keychain line to run,
where the log is, how to stop it and how to take something down.
"""

from __future__ import annotations

import argparse
import getpass
import hashlib
import json
import os
import shutil
import subprocess
import sys
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "src"))

from controlbun import ref as registry_ref  # noqa: E402


class Refused(RuntimeError):
    """Something this will not do, with the reason already in the message.

    One class for every refusal, the same argument `artifacts/intake.py` makes:
    the reader is an operator reading a notification or a log line, and a
    sentence they can act on is the entire product of the error path.
    """


# --------------------------------------------------------------------------- #
# Where things are.

# The Keychain item. Service and account rather than a file, because a file in
# the working tree is one `git add -A` away from a public repository and this
# key bypasses every row-level policy on the project. `AUTOPUBLISH.md` carries
# the line that stores it.
KEYCHAIN_SERVICE = "controlbun-supabase"

# Seconds. A `find-generic-password` read is instant when the item's access
# control allows the caller, and waits forever on a GUI prompt when it does
# not. Under launchd nobody is there to click it, so the read is bounded and
# the timeout is reported as what it is.
KEYCHAIN_TIMEOUT = 20

SOURCE_BRANCH = "main"
DEPLOY_BRANCH = "gh-pages"

# Pages serves the root of this branch, so the branch root is the contents of
# `astro/dist` and nothing else. `/private/tmp` rather than `/tmp` because the
# second is a symlink to the first and `git worktree list` records the real
# path; comparing the two as strings is how this refuses to find a worktree
# that is sitting right there. macOS clears `/private/tmp` of untouched files,
# so the worktree is recreated when it is gone rather than assumed.
PAGES_WORKTREE = Path("/private/tmp/pages")

# The tracked files a pull plus a build changes, and the only paths ever staged.
# `git add -A` in this checkout would sweep up whatever the owner was in the
# middle of, so nothing here uses it and the run refuses outright if a path
# outside this tuple changed.
RECORD = "artifacts/intake.jsonl"
STAGED = (
    RECORD,
    "astro/src/data/controlbun.json",
    "astro/src/data/agent-prompt.json",
)

# One directory, so there is one place to look. The log is where launchd sends
# the job's stdout and stderr, so a line this prints and a line `make` prints
# land in the same file in the order they happened.
JOB_DIR = Path.home() / "Library" / "Logs" / "controlbun"
LOG = JOB_DIR / "autopublish.log"
LOCK = JOB_DIR / "autopublish.lock"

# The digest of the last run that published nothing. A row the schema refuses
# keeps `taken_at` null, so it is read again on the next firing and refused
# again, forever. Reporting that every fifteen minutes is how a log becomes a
# thing nobody reads. It is reported when it changes and not otherwise.
OUTCOME = JOB_DIR / "last-outcome.sha256"

LABEL = "com.controlbun.autopublish"
INTERVAL = 900

PLIST = HERE / "com.controlbun.autopublish.plist"


def now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# --------------------------------------------------------------------------- #
# Saying what happened.


def say(line: str, *, error: bool = False) -> None:
    """One timestamped line, to stdout or stderr.

    launchd sends both to `LOG`. Nothing here opens the log itself: a second
    writer to the same file interleaves with the first, and the child processes
    inherit these descriptors, so `make verify` output lands in the right place
    for free.
    """
    stream = sys.stderr if error else sys.stdout
    print(f"[{now()}] {line}", file=stream, flush=True)


def notify(title: str, message: str) -> None:
    """A macOS notification, because the owner has to learn without looking.

    Arguments go through `argv` rather than into the script text, so a refusal
    carrying a quote or a backslash cannot close the string it is inside.
    A failure to notify is never a failure of the run: the log already has it.
    """
    try:
        subprocess.run(
            [
                "/usr/bin/osascript",
                "-e", "on run argv",
                "-e", "display notification (item 1 of argv) "
                      "with title (item 2 of argv)",
                "-e", "end run",
                message[:400], title,
            ],
            capture_output=True, timeout=20, check=False,
        )
    except (OSError, subprocess.SubprocessError) as failed:
        say(f"the notification did not go out ({failed}); the log has it", error=True)


def once(report: str, *, state: Path | None = None) -> bool:
    """True the first time an outcome is seen, False while it repeats.

    Every run that publishes nothing goes through here. Nothing pending is the
    ordinary case forever and says the same sentence every time; a refused row
    says the same sentence every time until somebody deals with it. Neither is
    news after the first one.

    The path is resolved here rather than defaulted in the signature, so a test
    can point the module's state somewhere that is not the owner's home.
    """
    state = state or OUTCOME
    digest = hashlib.sha256(report.encode()).hexdigest()
    try:
        seen = state.read_text().strip()
    except OSError:
        seen = ""
    if seen == digest:
        return False
    state.parent.mkdir(parents=True, exist_ok=True)
    state.write_text(digest + "\n")
    return True


def published(state: Path | None = None) -> None:
    """Clear the repeat marker, so the next quiet run reports once again."""
    try:
        (state or OUTCOME).unlink()
    except OSError:
        pass


# --------------------------------------------------------------------------- #
# One at a time.


@contextmanager
def lock(path: Path | None = None):
    """An exclusive hold, or a refusal naming who has it.

    Two firings in one checkout, or a firing on top of the deploy the owner
    started by hand, would have two builds writing `astro/dist` and two
    processes staging the same paths. `O_EXCL` is the atomic part; the pid
    inside is what lets a lock left by a killed run be taken rather than
    needing a human.

    **This does not cover a bare `make verify` the owner runs himself.** That
    target takes no lock and cannot be made to take one: `hooks/pre-push` runs
    `make verify` inside a push this already holds the lock for, so a lock
    there would deadlock the deploy. `AUTOPUBLISH.md` says so and says what to
    do instead.
    """
    path = path or LOCK
    path.parent.mkdir(parents=True, exist_ok=True)
    for attempt in (1, 2):
        try:
            fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            break
        except FileExistsError:
            holder = _holder(path)
            if holder is not None and _alive(holder):
                raise Refused(
                    f"another run holds {path} (pid {holder}), so this one did "
                    "nothing. Two builds in one checkout would write the same "
                    "`astro/dist` and stage the same paths."
                )
            if attempt == 2:
                raise Refused(
                    f"{path} could not be taken and could not be cleared. "
                    "Remove it by hand once you are sure nothing is running."
                )
            say(f"clearing a lock left by pid {holder}, which is not running")
            try:
                path.unlink()
            except OSError:
                pass
    try:
        os.write(fd, f"{os.getpid()}\n".encode())
        os.close(fd)
        yield path
    finally:
        try:
            path.unlink()
        except OSError:
            pass


def _holder(path: Path) -> int | None:
    try:
        return int(path.read_text().strip())
    except (OSError, ValueError):
        return None


def _alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


# --------------------------------------------------------------------------- #
# The key, read at the moment it is needed.


def secret_from_keychain(*, service: str = KEYCHAIN_SERVICE,
                         account: str | None = None,
                         timeout: int = KEYCHAIN_TIMEOUT) -> str:
    """The Supabase secret key out of the login Keychain, or a refusal.

    Three failures and three different sentences, because "it did not work"
    covers a missing item, a locked Keychain and a prompt nobody clicked, and
    the three want different things done about them.

    Nothing returned by this function is printed, logged, interpolated into a
    message or written anywhere. It goes into one child process's environment.
    `tests/test_autopublish.py` holds that over the whole module, the way
    `tests/test_pending_submission.py` holds it over `artifacts/intake.py`.
    """
    account = account or getpass.getuser()
    store = (f'security add-generic-password -U -a "$USER" '
             f'-s {service} -w')
    try:
        asked = subprocess.run(
            ["/usr/bin/security", "find-generic-password",
             "-s", service, "-a", account, "-w"],
            capture_output=True, text=True, timeout=timeout, check=False,
        )
    except subprocess.TimeoutExpired as waited:
        raise Refused(
            f"the Keychain did not answer within {timeout}s. That is almost "
            "always an access prompt waiting for a click, and under launchd "
            "nobody is there to click it. Run `make pull-dry` from a terminal "
            "once and choose Always Allow, which is the answer the prompt is "
            "asking for."
        ) from waited
    except OSError as missing:
        raise Refused(
            f"/usr/bin/security could not be run ({missing}), so the key could "
            "not be read. Nothing was written."
        ) from missing
    if asked.returncode != 0:
        raise Refused(
            f"no Keychain item for service {service!r} and account "
            f"{account!r}, so there is nothing to read the table with. Store "
            f"it with:\n\n    {store}\n\n"
            "`-w` last and with no value prompts, which keeps the key out of "
            "shell history. Nothing was written."
        )
    secret = asked.stdout.strip()
    if not secret:
        raise Refused(
            f"the Keychain item for service {service!r} is empty. Replace it "
            f"with:\n\n    {store}\n\nNothing was written."
        )
    return secret


# --------------------------------------------------------------------------- #
# The checkout, and what state it has to be in.


def git(root: Path, *args: str, check: bool = True) -> str:
    done = subprocess.run(
        ["git", *args], cwd=root, capture_output=True, text=True, check=False,
    )
    if check and done.returncode != 0:
        raise Refused(
            f"`git {' '.join(args)}` failed in {root}: "
            f"{(done.stderr or done.stdout).strip()}"
        )
    return done.stdout


def changed(root: Path) -> tuple[list[str], list[str]]:
    """Tracked files that differ from HEAD, and untracked files that are not ignored.

    Two lists rather than `git status --porcelain`, because that output has to
    be parsed and a rename or a path with a space parses wrong exactly when it
    matters. These two are one path per line and nothing else.
    """
    tracked = [p for p in git(root, "diff", "--name-only", "HEAD").split("\n") if p]
    untracked = [
        p for p in
        git(root, "ls-files", "--others", "--exclude-standard").split("\n") if p
    ]
    return tracked, untracked


def refuse_a_dirty_tree(root: Path) -> None:
    """The owner works in this checkout, so the job never runs on top of him.

    A run that committed around his uncommitted edits, or swept them into a
    commit, is the worst outcome available here. It is worse than not
    publishing, because not publishing is visible and a commit carrying half of
    somebody's work in progress is not.
    """
    tracked, untracked = changed(root)
    if not tracked and not untracked:
        return
    mine = [p for p in tracked if p in STAGED]
    theirs = [p for p in tracked if p not in STAGED] + untracked
    lines = [f"  changed    {p}" for p in tracked]
    lines += [f"  untracked  {p}" for p in untracked]
    if mine and not theirs:
        why = (
            "Every one of these is a path this job writes, so a previous run "
            "got as far as pulling and then stopped. Look at the log, then "
            "commit them or throw them away."
        )
    else:
        why = (
            "Some of these are not paths this job writes, so somebody is in "
            "the middle of something. Nothing was pulled, nothing was built "
            "and nothing was pushed."
        )
    raise Refused(
        "the working tree is not clean, so this did nothing:\n"
        + "\n".join(lines) + "\n\n" + why
    )


def refuse_an_unwired_hook(root: Path) -> None:
    """A push with no hook is a deploy the gate never saw.

    `hooks/pre-push` is the half of the invariant that binds a push somebody
    made. It binds nothing at all in a checkout where `core.hooksPath` was
    never set, and `git push` says nothing about that: it succeeds, quietly,
    with the gate skipped. So the one target that pushes checks the wiring
    before it pushes, rather than discovering afterwards that it did not run.
    """
    configured = git(root, "config", "--get", "core.hooksPath", check=False).strip()
    if not configured:
        raise Refused(
            "`core.hooksPath` is not set in this checkout, so `git push` would "
            "run no pre-push hook and the gate would not run. Wire it with "
            "`make hooks`. Nothing was pushed."
        )
    hook = (root / configured / "pre-push").resolve()
    tracked = (root / "hooks" / "pre-push").resolve()
    if hook != tracked:
        raise Refused(
            f"`core.hooksPath` points at {configured!r}, whose pre-push is "
            f"{hook}, and the gate lives at {tracked}. Wire it with "
            "`make hooks`. Nothing was pushed."
        )
    if not os.access(hook, os.X_OK):
        raise Refused(
            f"{hook} is not executable, so git would skip it and the push "
            "would not be gated. Nothing was pushed."
        )


def refuse_the_wrong_branch(root: Path) -> None:
    """A deploy names the branch it pushes, so it runs where that branch is.

    The repository has several worktrees, each on its own branch, all sharing
    one object store. `git push origin main gh-pages` from any of them pushes
    the same two refs, which means a deploy issued from an agent's worktree
    would publish a build made from that worktree's tree under main's name.
    """
    head = git(root, "rev-parse", "--abbrev-ref", "HEAD").strip()
    if head != SOURCE_BRANCH:
        raise Refused(
            f"HEAD here is {head!r} and a deploy pushes {SOURCE_BRANCH!r}, so "
            f"the built site would not be the built site of {SOURCE_BRANCH!r}. "
            f"Run this from the checkout that is on {SOURCE_BRANCH}. Nothing "
            "was pushed."
        )


# --------------------------------------------------------------------------- #
# Running the gate, and the build it gates.


def make(root: Path, target: str, *, capture: bool,
         env: dict[str, str] | None = None) -> tuple[int, str]:
    """One `make` target. Captured for the job, streamed for a person.

    Captured because the job's log is a file somebody reads later and a green
    gate is one line of news in two hundred of pytest dots. Streamed by hand
    because somebody watching a build wants to see it move.

    `MAKEFLAGS` and `MAKELEVEL` are dropped. `make deploy` runs this through a
    recipe, so without that the nested make inherits the outer one's flags,
    including a jobserver file descriptor that is not open in this process.
    """
    env = dict(env or os.environ)
    env.pop("MAKEFLAGS", None)
    env.pop("MAKELEVEL", None)
    done = subprocess.run(
        ["make", target], cwd=root, env=env,
        capture_output=capture, text=True, check=False,
    )
    return done.returncode, ((done.stdout or "") + (done.stderr or "")) if capture else ""


def tail(output: str, lines: int = 40) -> str:
    kept = [line for line in output.split("\n") if line.strip()]
    return "\n".join(kept[-lines:])


# --------------------------------------------------------------------------- #
# The deploy branch.


def pages_worktree(root: Path, path: Path = PAGES_WORKTREE) -> Path:
    """The worktree holding the deploy branch, made if it is not there.

    macOS clears untouched files out of `/private/tmp`, so this is a path that
    disappears on its own schedule rather than a fixture. `git worktree prune`
    first, because a registration whose directory is gone makes `git worktree
    add` refuse a path nothing is using.
    """
    git(root, "worktree", "prune")
    if (path / ".git").exists():
        head = git(path, "rev-parse", "--abbrev-ref", "HEAD").strip()
        if head != DEPLOY_BRANCH:
            raise Refused(
                f"{path} is on {head!r} and the deploy branch is "
                f"{DEPLOY_BRANCH!r}. Nothing was pushed."
            )
        return path
    have = git(root, "rev-parse", "--verify", "--quiet",
               f"refs/heads/{DEPLOY_BRANCH}", check=False).strip()
    if have:
        git(root, "worktree", "add", str(path), DEPLOY_BRANCH)
    else:
        remote = git(root, "rev-parse", "--verify", "--quiet",
                     f"refs/remotes/origin/{DEPLOY_BRANCH}", check=False).strip()
        if not remote:
            raise Refused(
                f"there is no {DEPLOY_BRANCH} branch here and none at origin, "
                "so there is nothing to deploy onto. `GO-LIVE.md` section 4 has "
                "the first-time sequence. Nothing was pushed."
            )
        git(root, "worktree", "add", "-b", DEPLOY_BRANCH, str(path),
            f"origin/{DEPLOY_BRANCH}")
    return path


def refresh(root: Path, pages: Path) -> bool:
    """The built site into the deploy worktree, staged file by file.

    `git rm -rf .` rather than a copy over the top, so the branch root is the
    built site and nothing else: no stale page surviving a rename, no
    `.gitignore` from the source branch reaching over to ignore what is being
    deployed. Every entry rather than a glob, so `.nojekyll` comes with it;
    without that file Pages runs Jekyll, Jekyll drops `_astro/`, and every page
    serves with no CSS and no error anywhere. `GO-LIVE.md` calls that the one
    silent breakage, and it is the reason the shell version said `dist/.` and
    not `dist/*`.

    **Staged by explicit path.** `GO-LIVE.md` wrote `git add -A` here and it
    was safe here, on an emptied worktree holding only what was just copied.
    It is not a habit worth keeping in a file that also runs unattended in the
    checkout the owner works in, so this enumerates what it copied instead.
    Returns whether there was anything to commit.
    """
    built = root / "astro" / "dist"
    if not built.is_dir():
        raise Refused(
            f"{built} does not exist, so there is no built site to deploy. "
            "Nothing was pushed."
        )
    git(pages, "rm", "-r", "-f", "-q", "--ignore-unmatch", ".")
    for item in built.iterdir():
        target = pages / item.name
        if item.is_dir():
            shutil.copytree(item, target)
        else:
            shutil.copy2(item, target)
    paths = sorted(
        str(p.relative_to(pages)) for p in pages.rglob("*")
        if p.is_file() and ".git" not in p.relative_to(pages).parts
    )
    if not paths:
        raise Refused(
            "the built site copied across as zero files, which is not a site. "
            "Nothing was pushed."
        )
    git(pages, "add", "--", *paths)
    # Trees rather than `git diff --cached`, which has to name HEAD and HEAD is
    # unborn the first time a deploy branch is made. Comparing the tree the
    # index would write against the one HEAD carries answers the question
    # without a special case for that.
    staged = git(pages, "write-tree").strip()
    committed = git(pages, "rev-parse", "--verify", "--quiet", "HEAD^{tree}",
                    check=False).strip()
    return staged != committed


# --------------------------------------------------------------------------- #
# The commands.


def gate(root: Path, *, capture: bool) -> None:
    """`make verify`, and a refusal that says nothing moved if it is red.

    Its own function because it is run exactly once per run and two callers
    need it at different points: `deploy` runs it and then pushes, and `job`
    runs it between the pull and the commit, because a commit made before the
    gate would leave the corpus carrying a row the gate had not seen.

    `hooks/pre-push` runs it a second time on the push and diffs the pushed
    tree against the `astro/dist` this one just built. That is not redundancy
    for its own sake: the first run decides whether to commit at all, and the
    second binds what is being pushed to what passed.
    """
    say("running the gate")
    code, output = make(root, "verify", capture=capture)
    if code != 0:
        raise Refused(
            "`make verify` failed, so nothing was committed and nothing was "
            "pushed.\n" + (tail(output) if capture else "The output is above.")
        )
    say("gate green")


def push_built(root: Path, *, capture: bool) -> str:
    """The built site onto the deploy branch, and both refs out in one push.

    One `git push` with two refs rather than two pushes, for two reasons. The
    pre-push hook runs `make verify`, so two pushes would run the gate twice
    for one deploy. And the built site and the source it was built from go out
    together or not at all, which is the property the whole no-hosted-build
    argument rests on: a reader can check that what is served came from what is
    published.

    Called only after `gate`, and the hook checks that again on the way out.
    """
    pages = pages_worktree(root)
    sha = git(root, "rev-parse", "--short", "HEAD").strip()
    if refresh(root, pages):
        git(pages, "commit", "-q", "-m", f"Deploy {sha}")
        say(f"deploy branch now carries the build at {sha}")
    else:
        say(f"the deploy branch already carries this build ({sha}); nothing to commit")

    say(f"pushing {SOURCE_BRANCH} and {DEPLOY_BRANCH}")
    done = subprocess.run(
        ["git", "push", "origin", SOURCE_BRANCH, DEPLOY_BRANCH],
        cwd=root, capture_output=capture, text=True, check=False,
    )
    if done.returncode != 0:
        raise Refused(
            "the push was refused, so nothing reached the site.\n"
            + (tail((done.stdout or "") + (done.stderr or "")) if capture
               else "The output is above.")
        )
    say("pushed")
    return sha


def deploy(root: Path, *, capture: bool = False) -> str:
    """The hand-typed sequence in `GO-LIVE.md` section 4, as one thing.

    Preconditions first, because each of them is a way for a push to look like
    it worked and publish something nobody gated: an unwired hook makes the
    gate optional, and the wrong branch makes the build somebody else's tree.

    A dirty tree is refused here too, and for a reason of its own. The site is
    built from the working tree and the commit pushed beside it is not, so
    deploying over uncommitted work would serve a page whose source is not the
    source that went public. That equivalence is the whole argument for having
    no hosted build, and it would be broken by the target that exists to keep
    it.
    """
    refuse_the_wrong_branch(root)
    refuse_an_unwired_hook(root)
    refuse_a_dirty_tree(root)
    gate(root, capture=capture)
    return push_built(root, capture=capture)


def pull(root: Path, *, dry_run: bool = False, capture: bool = False,
         secret: str | None = None) -> tuple[int, str]:
    """`artifacts/intake.py pull`, with the key from the Keychain in its environment.

    The key is put into the child's environment and into nothing else. It is
    not written to a file, not passed on a command line where `ps` would show
    it, and not returned from here.
    """
    if secret is None:
        secret = secret_from_keychain()
    env = dict(os.environ)
    env["SUPABASE_SECRET_KEY"] = secret
    argv = [sys.executable, str(HERE / "intake.py"), "pull"]
    if dry_run:
        argv.append("--dry-run")
    done = subprocess.run(
        argv, cwd=root, env=env, capture_output=capture, text=True, check=False,
    )
    return done.returncode, ((done.stdout or "") + (done.stderr or "")) if capture else ""


def arrivals(root: Path, before: int) -> list[str]:
    """The refs the pull just wrote, read off the record rather than off output.

    The record is the durable copy and it is append-only, so the entries past
    the line count taken before the pull are exactly what this run added.
    Parsing the human-readable output instead would make a printed sentence
    load-bearing.
    """
    lines = (root / RECORD).read_text().splitlines()
    out = []
    for line in lines[before:]:
        try:
            entry = json.loads(line)
        except ValueError:
            continue
        out.append(registry_ref.format(
            entry.get("author"),
            (entry.get("intervention") or {}).get("model_id"),
            entry.get("label"), entry.get("version"),
        ))
    return out


def job(root: Path) -> int:
    """One firing. Safe to run every fifteen minutes forever.

    In order, and every step is a place it can stop:

        1. take the lock, or say who has it
        2. refuse a tree with changes this job did not make
        3. refuse an unwired hook, and a checkout not on the source branch
        4. read the key out of the Keychain, with a timeout
        5. pull; a refused row stops that row and not the run
        6. nothing new in the record, so no commit, no push, no deploy,
           and no line in the log if it is the same nothing as last time
        7. gate; a red gate commits nothing and pushes nothing
        8. refuse a change to a path this does not stage
        9. stage those paths by name and commit
       10. push the source and the site, which runs the gate again in the hook
       11. say what published, in the log and in a notification
    """
    with lock():
        refuse_a_dirty_tree(root)
        refuse_an_unwired_hook(root)
        refuse_the_wrong_branch(root)

        record = root / RECORD
        before = len(record.read_text().splitlines()) if record.exists() else 0

        # The key is read here and handed straight down, so it never binds to
        # a name in this frame and nothing in this function can print it.
        code, output = pull(root, capture=True, secret=secret_from_keychain())
        after = len(record.read_text().splitlines()) if record.exists() else 0

        if code != 0 or after == before:
            report = f"exit {code}\n{output}"
            if once(report):
                say("nothing published this run" if code == 0 else
                    "the pull did not finish", error=code != 0)
                say(tail(output, 20))
                if code != 0:
                    notify("controlbun: the pull did not finish", tail(output, 4))
            return 0 if code == 0 else 1

        refs = arrivals(root, before)
        say(f"{len(refs)} submission(s) in the record: {', '.join(refs)}")
        if output.strip():
            say(tail(output, 30))

        try:
            gate(root, capture=True)
        except Refused as red:
            say(str(red), error=True)
            notify("controlbun: the gate failed, nothing published",
                   f"{len(refs)} submission(s) are in the record and the tree "
                   "stays dirty until you deal with it. See the log.")
            return 1

        tracked, untracked = changed(root)
        unexpected = [p for p in tracked if p not in STAGED] + untracked
        if unexpected:
            say("a path this job does not stage changed, so nothing was "
                "committed: " + ", ".join(unexpected), error=True)
            notify("controlbun: nothing published",
                   "a file changed that the job does not stage. See the log.")
            return 1

        staging = [p for p in STAGED if p in tracked]
        git(root, "add", "--", *staging)
        git(root, "commit", "-q", "-m", _message(refs))
        say(f"committed {', '.join(staging)}")

        sha = push_built(root, capture=True)
        published()
        say(f"published {len(refs)} submission(s) at {sha}")
        notify(f"controlbun published {len(refs)} submission(s)",
               ", ".join(refs))
        return 0


def _message(refs: list[str]) -> str:
    """The commit message for a run nobody typed.

    It names what arrived and says which script made it, because a commit whose
    author is a laptop and whose content is a stranger's submission is a thing
    somebody will read the log for later.
    """
    head = ("Publish the submission that arrived at /submit/" if len(refs) == 1
            else f"Publish {len(refs)} submissions that arrived at /submit/")
    body = "\n".join(f"  {r}" for r in refs)
    return (
        f"{head}\n\n{body}\n\n"
        f"Pulled, gated and deployed by artifacts/autopublish.py at {now()},\n"
        "with nobody typing anything. DECISIONS.md 2026-09-20 records that\n"
        "publishing is automatic and the two things it does not solve."
    )


# --------------------------------------------------------------------------- #
# The launchd job.


def plist(root: Path, python: str | None = None) -> str:
    """The agent definition, rendered from the tracked template.

    A template plus a target rather than a file written into
    `~/Library/LaunchAgents` by whoever last touched this: an agent that fires
    every fifteen minutes and pushes to a public site is something the owner
    installs on purpose.

    `PATH` is set here because launchd gives a job
    `/usr/bin:/bin:/usr/sbin:/sbin` and nothing else, and `make site` runs
    `npm`, which on this machine is under nvm. A job that cannot find `npm`
    fails at the build every fifteen minutes.
    """
    python = python or sys.executable
    node = str(Path(shutil.which("npm") or "/usr/local/bin/npm").parent)
    path = ":".join(dict.fromkeys(
        [node, "/opt/homebrew/bin", "/usr/local/bin",
         "/usr/bin", "/bin", "/usr/sbin", "/sbin"]
    ))
    return (
        PLIST.read_text()
        .replace("@LABEL@", LABEL)
        .replace("@PYTHON@", python)
        .replace("@ROOT@", str(root))
        .replace("@SCRIPT@", str(root / "artifacts" / "autopublish.py"))
        .replace("@PATH@", path)
        .replace("@INTERVAL@", str(INTERVAL))
        .replace("@LOG@", str(LOG))
    )


# --------------------------------------------------------------------------- #


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="command", required=True)

    pulled = sub.add_parser("pull", help="the table into the tracked record")
    pulled.add_argument("--dry-run", action="store_true",
                        help="read and report, write nothing and mark nothing")

    sub.add_parser("deploy", help="gate, then push the source and the built site")
    sub.add_parser("run", help="one firing of the scheduled job")
    sub.add_parser("plist", help="the launchd agent, on stdout")

    args = ap.parse_args(argv)
    try:
        if args.command == "pull":
            code, _ = pull(ROOT, dry_run=args.dry_run, capture=False)
            return code
        if args.command == "deploy":
            deploy(ROOT, capture=False)
            return 0
        if args.command == "run":
            return job(ROOT)
        if args.command == "plist":
            sys.stdout.write(plist(ROOT))
            return 0
    except Refused as refused:
        say(str(refused), error=True)
        if args.command == "run":
            notify("controlbun: nothing published", str(refused).split("\n")[0])
        return 1
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
