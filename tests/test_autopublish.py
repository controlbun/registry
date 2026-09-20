"""Publishing runs itself, so every way it can refuse is a test.

Premise, restated because a premise stated in one document gets violated in
every other one: plurality is the product, the registry never designates, and
nothing here reads a submission or decides whether one is worth publishing.
What these tests hold is the machine: a run that publishes nothing commits
nothing, a run that finds somebody mid-edit does nothing at all, and no path
reaches the deploy branch without the gate.

**What cannot be tested here, said rather than implied.** Three things.

`hooks/pre-push` is a shell script git runs, and running it for real needs a
remote to push to and a full `make verify` inside it, which takes minutes and
writes `astro/dist`. So what is checked is that nothing in the deploy path can
skip it: no `--no-verify` anywhere, `core.hooksPath` checked before the push,
and the push argv pinned. That the hook then does what it says is
`hooks/pre-push`'s own business, and `test_the_hook_still_does_the_two_things`
reads it to confirm it has not been hollowed out.

The `launchd` agent is not loaded by any test. `plutil -lint` on the rendered
template is the whole of what can be checked without installing an agent that
pushes to a public site, and installing one from a test run is not a thing to
do.

The Keychain read is exercised against a service name nothing has stored, which
proves the refusal and its instructions. The success path needs an item in the
login Keychain, which a test must not create.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "artifacts"))

import autopublish  # noqa: E402

SOURCE = (ROOT / "artifacts" / "autopublish.py").read_text()
MAKEFILE = (ROOT / "Makefile").read_text()


def statements(text: str) -> str:
    """Source with its comments and docstrings taken out.

    Written because the first run of the scans below failed on this module's own
    prose: the docstring says "never `git add -A`" and the Makefile comment says
    "Never `--no-verify`", and a substring scan cannot tell a rule from its
    violation. `tests/test_invariants.py` drops comment lines for the same
    reason and this drops triple-quoted blocks as well, because the argument for
    a rule is written where the rule is.
    """
    out, inside = [], False
    for line in text.split("\n"):
        stripped = line.strip()
        if inside:
            if '"""' in stripped:
                inside = False
            continue
        if stripped.startswith("#") or stripped.startswith("//"):
            continue
        if stripped.startswith('"""') or stripped.startswith('r"""'):
            if stripped.count('"""') == 1:
                inside = True
            continue
        out.append(line)
    return "\n".join(out)


CODE = statements(SOURCE)
RECIPES = statements(MAKEFILE)


def test_the_comment_strip_does_not_hide_a_real_one():
    """A strip that took everything out would make every scan below inert.

    The same control `tests/test_pending_submission.py` keeps over its own SQL
    comment strip, for the same reason: a helper that silently returns nothing
    turns four checks green at once.
    """
    assert "def secret_from_keychain" in CODE
    assert "add -A" not in CODE and "add -A" in SOURCE
    assert "deploy:" in RECIPES
    assert statements('x = 1\n"""\ndoc\n"""\ny = 2\n').split() == ["x", "=", "1",
                                                                  "y", "=", "2"]


# --------------------------------------------------------------------------- #
# A checkout to run against.


def _git(root: Path, *args: str) -> str:
    done = subprocess.run(["git", *args], cwd=root, capture_output=True,
                          text=True, check=True)
    return done.stdout


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """A checkout shaped like this one: a record, a hook, and a `main`.

    Not a copy of the real repository. What the code under test touches is the
    record, the three staged paths, the hook wiring and the branch name, and a
    fixture holding those is one a test can reason about.
    """
    root = tmp_path / "checkout"
    (root / "artifacts").mkdir(parents=True)
    (root / "hooks").mkdir()
    (root / "astro" / "src" / "data").mkdir(parents=True)
    (root / "astro" / "dist").mkdir(parents=True)

    (root / "artifacts" / "intake.jsonl").write_text("")
    (root / "astro" / "src" / "data" / "controlbun.json").write_text("{}\n")
    (root / "astro" / "src" / "data" / "agent-prompt.json").write_text("{}\n")
    (root / "astro" / "dist" / "index.html").write_text("<!doctype html>\n")
    (root / "astro" / "dist" / ".nojekyll").write_text("")
    hook = root / "hooks" / "pre-push"
    hook.write_text("#!/bin/sh\nexit 0\n")
    hook.chmod(0o755)

    _git(root.parent, "init", "-q", "-b", "main", str(root))
    _git(root, "config", "user.email", "test@example.invalid")
    _git(root, "config", "user.name", "Test")
    _git(root, "config", "core.hooksPath", "hooks")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "first")
    return root


@pytest.fixture
def state(tmp_path, monkeypatch) -> Path:
    """The job's lock and repeat marker, out of the owner's home directory."""
    here = tmp_path / "jobdir"
    here.mkdir()
    monkeypatch.setattr(autopublish, "JOB_DIR", here)
    monkeypatch.setattr(autopublish, "LOCK", here / "autopublish.lock")
    monkeypatch.setattr(autopublish, "OUTCOME", here / "last-outcome.sha256")
    monkeypatch.setattr(autopublish, "notify", lambda *a, **k: None)
    return here


def commits(root: Path) -> int:
    return len(_git(root, "log", "--format=%H").split())


# --------------------------------------------------------------------------- #
# The tree the owner works in.


def test_a_clean_tree_is_the_only_one_it_will_run_on(repo):
    autopublish.refuse_a_dirty_tree(repo)  # does not raise


def test_it_refuses_when_somebody_is_mid_edit(repo):
    """The worst outcome here is a commit carrying half of the owner's work.

    Worse than not publishing, because not publishing is visible in the log and
    a commit that swept up somebody's work in progress is not.
    """
    (repo / "BRIEF.md").write_text("half a sentence")
    with pytest.raises(autopublish.Refused) as refused:
        autopublish.refuse_a_dirty_tree(repo)
    said = str(refused.value)
    assert "BRIEF.md" in said
    assert "othing was pulled" in said
    assert "in the middle of something" in said


def test_an_untracked_file_counts_as_mid_edit(repo):
    (repo / "scratch.md").write_text("notes")
    with pytest.raises(autopublish.Refused) as refused:
        autopublish.refuse_a_dirty_tree(repo)
    assert "scratch.md" in str(refused.value)


def test_a_dirty_tree_of_only_its_own_paths_says_a_previous_run_stopped(repo):
    """The same refusal, and a different sentence, because it is a different problem.

    A tree dirty in exactly the paths this job writes is a run that pulled and
    then hit a red gate. Telling the owner to go looking for what he was in the
    middle of would send him after something that is not there.
    """
    (repo / "artifacts" / "intake.jsonl").write_text('{"author": "someone"}\n')
    with pytest.raises(autopublish.Refused) as refused:
        autopublish.refuse_a_dirty_tree(repo)
    said = str(refused.value)
    assert "a previous run" in said
    assert "in the middle of something" not in said


def test_the_paths_it_stages_are_tracked_files_of_this_repository():
    """A staged path that is not tracked would be staged and never committed.

    This is the list `git add -A` is not being used in place of, so it has to
    name real files. Checked against the real repository rather than a fixture,
    because the point is that this list and that tree agree.
    """
    tracked = set(subprocess.run(
        ["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True,
    ).stdout.split())
    for path in autopublish.STAGED:
        assert path in tracked, f"{path} is staged by the job and is not tracked"


# --------------------------------------------------------------------------- #
# The key.


def test_a_missing_keychain_item_refuses_and_says_how_to_store_it():
    """The refusal carries the command, because that is the whole of the fix.

    Run against a service nothing has stored, so it exercises the real
    `security` binary and the real failure. The success path is not tested: it
    needs an item in the login Keychain and a test must not put one there.
    """
    with pytest.raises(autopublish.Refused) as refused:
        autopublish.secret_from_keychain(
            service="controlbun-no-such-service-in-any-keychain")
    said = str(refused.value)
    assert "security add-generic-password" in said
    assert '-s controlbun-no-such-service-in-any-keychain -w' in said
    assert "Nothing was written" in said


def test_a_keychain_that_does_not_answer_is_a_prompt_nobody_clicked(monkeypatch):
    """A hang is worse than a failure, so the read is bounded and says why.

    Under launchd there is nobody to click an access prompt. Without the
    timeout the job would sit holding the lock, logging nothing and notifying
    nothing, which is the one failure mode that looks like everything is fine.
    """
    def hangs(*args, **kwargs):
        raise subprocess.TimeoutExpired(cmd="security", timeout=kwargs["timeout"])
    monkeypatch.setattr(autopublish.subprocess, "run", hangs)
    with pytest.raises(autopublish.Refused) as refused:
        autopublish.secret_from_keychain(timeout=3)
    said = str(refused.value)
    assert "within 3s" in said
    assert "Always Allow" in said


def test_an_empty_keychain_item_is_not_a_key(monkeypatch):
    class Empty:
        returncode = 0
        stdout = "\n"
    monkeypatch.setattr(autopublish.subprocess, "run", lambda *a, **k: Empty())
    with pytest.raises(autopublish.Refused) as refused:
        autopublish.secret_from_keychain()
    assert "is empty" in str(refused.value)


def test_the_key_never_reaches_output():
    """It bypasses every row-level policy on the project, so it goes one place.

    The same rule `tests/test_pending_submission.py` holds over
    `artifacts/intake.py`, held here over the module that reads it out of the
    Keychain and hands it on. The variable is `secret` for the reason that file
    gives: a name like `key` collides with dictionary keys and the check cannot
    tell them apart.
    """
    lines = CODE.split("\n")
    printing = [
        line.strip() for line in lines
        if ("print(" in line or "say(" in line or "notify(" in line)
        and "secret" in line
    ]
    assert not printing, f"the secret key reaches output: {printing}"
    interpolating = [line.strip() for line in lines if "{secret" in line]
    assert not interpolating, (
        f"the secret key is interpolated into a string: {interpolating}"
    )
    # It is put into one child's environment and written nowhere. A file, a
    # command line (which `ps` shows) and a log line are each a line this
    # catches.
    assignments = [
        line.strip() for line in lines
        if "secret" in line and ("write_text" in line or "write(" in line)
    ]
    assert not assignments, f"the secret key is written somewhere: {assignments}"


def test_the_key_is_not_read_from_a_file_in_the_working_tree():
    """A key in the tree is a key one `git add -A` away from a public repository.

    `artifacts/intake.py credentials` refuses to fall back to `.env` for it,
    and this is the other end of that rule: the Keychain is the only source.
    """
    body = CODE.split("def secret_from_keychain")[1].split("\ndef ")[0]
    assert ".env" not in body and "read_text" not in body
    assert 'KEYCHAIN_SERVICE = "controlbun-supabase"' in CODE


# --------------------------------------------------------------------------- #
# Nothing to publish, which is the ordinary case forever.


def _quiet_pull(written: str = ""):
    """A pull that ran and wrote nothing into the record, like a pull usually does."""
    def pull(root, *, capture=False, dry_run=False, secret=None):
        if written:
            (root / autopublish.RECORD).write_text(written)
        return 0, "nothing pending. The table is empty of unread rows.\n"
    return pull


def test_no_rows_means_no_commit_no_push_and_no_deploy(repo, state, monkeypatch):
    """The run that happens every fifteen minutes forever.

    It has to leave the checkout exactly as it found it. A commit here would
    be an empty one every quarter hour, and a push would be a gate run for
    nothing.
    """
    monkeypatch.setattr(autopublish, "secret_from_keychain",
                        lambda **k: "not used; the pull is stubbed")
    monkeypatch.setattr(autopublish, "pull", _quiet_pull())
    monkeypatch.setattr(autopublish, "gate", _never("the gate ran"))
    monkeypatch.setattr(autopublish, "push_built", _never("something was pushed"))

    before = commits(repo)
    assert autopublish.job(repo) == 0
    assert commits(repo) == before
    assert autopublish.changed(repo) == ([], [])


def test_the_same_nothing_is_reported_once_and_then_not_again(repo, state,
                                                              monkeypatch, capsys):
    """A row the schema refuses keeps `taken_at` null and comes back forever.

    Reporting it every fifteen minutes is how a log becomes a file nobody
    opens, which would take the notification down with it.
    """
    monkeypatch.setattr(autopublish, "secret_from_keychain", lambda **k: "unused")
    monkeypatch.setattr(autopublish, "pull", _quiet_pull())
    monkeypatch.setattr(autopublish, "gate", _never("the gate ran"))
    monkeypatch.setattr(autopublish, "push_built", _never("something was pushed"))

    autopublish.job(repo)
    first = capsys.readouterr().out
    assert "nothing published this run" in first

    autopublish.job(repo)
    assert capsys.readouterr().out == "", (
        "the second identical run said something, so the log fills with the "
        "same sentence four times an hour"
    )


def test_a_pull_that_fails_says_so_once(repo, state, monkeypatch, capsys):
    def failing(root, *, capture=False, dry_run=False, secret=None):
        return 1, "the project could not be reached (timed out).\n"
    monkeypatch.setattr(autopublish, "secret_from_keychain", lambda **k: "unused")
    monkeypatch.setattr(autopublish, "pull", failing)
    monkeypatch.setattr(autopublish, "gate", _never("the gate ran"))
    monkeypatch.setattr(autopublish, "push_built", _never("something was pushed"))

    assert autopublish.job(repo) == 1
    assert "the pull did not finish" in capsys.readouterr().err
    assert autopublish.job(repo) == 1
    assert capsys.readouterr().err == ""


def _never(why: str):
    def called(*args, **kwargs):
        raise AssertionError(why)
    return called


# --------------------------------------------------------------------------- #
# Rows, and the one path that commits.


ENTRY = json.dumps({
    "author": "someone",
    "label": "a-label",
    "version": "v1",
    "intervention": {"model_id": "gpt2"},
})


def test_rows_are_staged_by_name_gated_and_committed(repo, state, monkeypatch):
    """The publishing path, with the gate and the push stubbed.

    What it asserts is the part this module owns: the gate ran before the
    commit, exactly the three paths were staged, and the commit message names
    what arrived.
    """
    ran = []

    def pull(root, *, capture=False, dry_run=False, secret=None):
        (root / autopublish.RECORD).write_text(ENTRY + "\n")
        (root / "astro" / "src" / "data" / "controlbun.json").write_text('{"a":1}\n')
        return 0, "  wrote someone/gpt2/a-label@v1\n"

    monkeypatch.setattr(autopublish, "secret_from_keychain", lambda **k: "unused")
    monkeypatch.setattr(autopublish, "pull", pull)
    monkeypatch.setattr(autopublish, "gate",
                        lambda root, *, capture: ran.append("gate"))
    monkeypatch.setattr(autopublish, "push_built",
                        lambda root, *, capture: ran.append("push") or "abc1234")

    before = commits(repo)
    assert autopublish.job(repo) == 0
    assert ran == ["gate", "push"], "the gate has to run before anything is pushed"
    assert commits(repo) == before + 1
    assert autopublish.changed(repo) == ([], [])

    body = _git(repo, "log", "-1", "--format=%B")
    assert "someone/gpt2/a-label@v1" in body
    assert "nobody typing anything" in body

    staged = _git(repo, "show", "--name-only", "--format=", "HEAD").split()
    assert sorted(staged) == sorted(
        ["artifacts/intake.jsonl", "astro/src/data/controlbun.json"]
    ), "the commit carries a path the job did not mean to stage"


def test_a_red_gate_commits_nothing_and_pushes_nothing(repo, state, monkeypatch):
    """The failure has to be loud and it has to leave the tree alone.

    The record stays dirty on purpose. That is what makes the next firing
    refuse instead of committing on top of a build that did not pass.
    """
    def pull(root, *, capture=False, dry_run=False, secret=None):
        (root / autopublish.RECORD).write_text(ENTRY + "\n")
        return 0, ""

    def red(root, *, capture):
        raise autopublish.Refused("`make verify` failed, so nothing was pushed.")

    told = []
    monkeypatch.setattr(autopublish, "secret_from_keychain", lambda **k: "unused")
    monkeypatch.setattr(autopublish, "pull", pull)
    monkeypatch.setattr(autopublish, "gate", red)
    monkeypatch.setattr(autopublish, "push_built", _never("something was pushed"))
    monkeypatch.setattr(autopublish, "notify",
                        lambda title, message: told.append(title))

    before = commits(repo)
    assert autopublish.job(repo) == 1
    assert commits(repo) == before
    assert autopublish.changed(repo)[0] == ["artifacts/intake.jsonl"]
    assert told and "gate failed" in told[0]


def test_a_file_the_job_does_not_stage_stops_the_commit(repo, state, monkeypatch):
    """Never `git add -A`, and this is what takes its place.

    If the build starts writing a fourth tracked file, the run stops and says
    which one rather than either dropping it or sweeping it in. Somebody then
    decides whether it belongs in `STAGED`, which is a decision rather than a
    line that arrived.
    """
    def pull(root, *, capture=False, dry_run=False, secret=None):
        (root / autopublish.RECORD).write_text(ENTRY + "\n")
        (root / "hooks" / "pre-push").write_text("#!/bin/sh\nexit 0\n# changed\n")
        return 0, ""

    monkeypatch.setattr(autopublish, "secret_from_keychain", lambda **k: "unused")
    monkeypatch.setattr(autopublish, "pull", pull)
    monkeypatch.setattr(autopublish, "gate", lambda root, *, capture: None)
    monkeypatch.setattr(autopublish, "push_built", _never("something was pushed"))

    before = commits(repo)
    assert autopublish.job(repo) == 1
    assert commits(repo) == before


def test_the_refs_come_off_the_record_and_not_off_printed_output(repo):
    (repo / autopublish.RECORD).write_text(ENTRY + "\n" + ENTRY + "\n")
    assert autopublish.arrivals(repo, 0) == [
        "someone/gpt2/a-label@v1", "someone/gpt2/a-label@v1",
    ]
    assert autopublish.arrivals(repo, 1) == ["someone/gpt2/a-label@v1"]


# --------------------------------------------------------------------------- #
# One at a time.


def test_a_second_run_will_not_start_while_the_first_holds_the_lock(state):
    with autopublish.lock():
        with pytest.raises(autopublish.Refused) as refused:
            with autopublish.lock():
                raise AssertionError("two runs got in at once")
    assert "another run holds" in str(refused.value)
    assert not autopublish.LOCK.exists(), "the lock outlived the run holding it"


def test_a_lock_left_by_a_run_that_died_is_taken_rather_than_obeyed(state, capsys):
    """Otherwise one killed run stops publishing until somebody notices.

    Pid 1 is running and is not this; a pid nothing owns is the case that
    matters, and the highest allocatable pid plus one cannot be in use.
    """
    autopublish.LOCK.parent.mkdir(parents=True, exist_ok=True)
    autopublish.LOCK.write_text("999999\n")
    with autopublish.lock():
        assert autopublish.LOCK.read_text().strip() == str(os.getpid())
    assert "clearing a lock" in capsys.readouterr().out


# --------------------------------------------------------------------------- #
# Nothing reaches the deploy branch that the gate did not pass in the same run.


def test_nothing_anywhere_skips_the_hook():
    """`--no-verify` is the one flag that would make all of this decorative.

    A locally built `astro/dist` is the whole argument for having no hosted
    build. A push past the gate deletes that argument quietly: the falsifier
    would be checking one build and readers reading another.
    """
    for where, text in (("autopublish.py", CODE), ("Makefile", RECIPES)):
        assert "--no-verify" not in text, f"{where} can skip the gate"
        assert "-c core.hooksPath" not in text, f"{where} overrides the hook path"
    # `make hooks` is the one place that sets it, and it sets it to the tracked
    # directory. Nothing else in the repository writes that setting.
    assert "git config core.hooksPath hooks" in MAKEFILE
    assert MAKEFILE.count("git config core.hooksPath") == 1
    # And the deploy path checks the wiring before it pushes rather than after.
    assert "refuse_an_unwired_hook(root)" in SOURCE


def test_the_deploy_refuses_a_checkout_whose_hook_is_not_wired(repo):
    """A push with no hook succeeds, quietly, with the gate skipped.

    Which makes this the half of the invariant the hook itself cannot hold:
    `hooks/pre-push` binds a push somebody made, and binds nothing at all in a
    checkout where `core.hooksPath` was never set.
    """
    autopublish.refuse_an_unwired_hook(repo)  # wired, does not raise

    _git(repo, "config", "--unset", "core.hooksPath")
    with pytest.raises(autopublish.Refused) as refused:
        autopublish.refuse_an_unwired_hook(repo)
    assert "make hooks" in str(refused.value)
    assert "Nothing was pushed" in str(refused.value)


def test_the_deploy_refuses_a_hook_that_is_not_the_tracked_one(repo):
    other = repo / "elsewhere"
    other.mkdir()
    (other / "pre-push").write_text("#!/bin/sh\nexit 0\n")
    (other / "pre-push").chmod(0o755)
    _git(repo, "config", "core.hooksPath", "elsewhere")
    with pytest.raises(autopublish.Refused) as refused:
        autopublish.refuse_an_unwired_hook(repo)
    assert "make hooks" in str(refused.value)


def test_a_hook_that_is_not_executable_is_a_hook_git_skips(repo):
    (repo / "hooks" / "pre-push").chmod(0o644)
    with pytest.raises(autopublish.Refused) as refused:
        autopublish.refuse_an_unwired_hook(repo)
    assert "not executable" in str(refused.value)


def test_a_deploy_from_the_wrong_branch_refuses(repo):
    """This repository has several worktrees, each on its own branch.

    They share one object store, so `git push origin main gh-pages` from any of
    them pushes the same two refs. A deploy from an agent's worktree would
    publish that worktree's build under main's name.
    """
    autopublish.refuse_the_wrong_branch(repo)  # on main, does not raise

    _git(repo, "checkout", "-q", "-b", "worktree-something")
    with pytest.raises(autopublish.Refused) as refused:
        autopublish.refuse_the_wrong_branch(repo)
    said = str(refused.value)
    assert "worktree-something" in said and "Nothing was pushed" in said


def test_the_deploy_runs_the_gate_before_it_pushes(repo, monkeypatch):
    ran = []
    monkeypatch.setattr(autopublish, "gate",
                        lambda root, *, capture: ran.append("gate"))
    monkeypatch.setattr(autopublish, "push_built",
                        lambda root, *, capture: ran.append("push") or "abc1234")
    assert autopublish.deploy(repo, capture=True) == "abc1234"
    assert ran == ["gate", "push"]


def test_a_deploy_over_uncommitted_work_refuses(repo, monkeypatch):
    """The site is built from the tree and the commit beside it is not.

    So deploying over uncommitted work serves a page whose source is not the
    source that went public, which is the equivalence the whole no-hosted-build
    argument rests on.
    """
    monkeypatch.setattr(autopublish, "gate", _never("the gate ran"))
    monkeypatch.setattr(autopublish, "push_built", _never("something was pushed"))
    (repo / "BRIEF.md").write_text("mid sentence")
    with pytest.raises(autopublish.Refused) as refused:
        autopublish.deploy(repo, capture=True)
    assert "BRIEF.md" in str(refused.value)


def test_a_red_gate_stops_the_deploy_before_the_pages_worktree_is_touched(repo,
                                                                         monkeypatch):
    def red(root, *, capture):
        raise autopublish.Refused("`make verify` failed, so nothing was pushed.")
    monkeypatch.setattr(autopublish, "gate", red)
    monkeypatch.setattr(autopublish, "push_built",
                        _never("the deploy branch was touched after a red gate"))
    with pytest.raises(autopublish.Refused):
        autopublish.deploy(repo, capture=True)


def test_the_hook_still_does_the_two_things_the_deploy_relies_on():
    """Read rather than run, and the docstring at the top says why.

    If the hook stopped running `make verify`, or stopped diffing the pushed
    tree against `astro/dist`, every check above would still pass and the
    deploy would be ungated.
    """
    hook = (ROOT / "hooks" / "pre-push").read_text()
    assert "make verify" in hook
    assert "refs/heads/gh-pages" in hook
    assert "astro/dist" in hook
    assert os.access(ROOT / "hooks" / "pre-push", os.X_OK)


def test_the_push_names_both_refs_in_one_invocation():
    """One push, so the hook runs the gate once and both refs go out together.

    The built site and the source it was built from are published together or
    not at all, which is what lets a reader check that what is served came from
    what is public.
    """
    line = [l for l in SOURCE.splitlines() if '"push", "origin"' in l]
    assert line, "the push argv changed shape; this check no longer reads it"
    assert 'SOURCE_BRANCH, DEPLOY_BRANCH' in line[0]


def test_nothing_stages_everything():
    """`git add -A` in this checkout would sweep up the owner's work in progress.

    The deploy worktree is the place it would have been safe, and it is not
    used there either: the reason is that this file also runs unattended in the
    checkout the owner works in, and a habit does not know which directory it
    is in.
    """
    for where, text in (("autopublish.py", CODE), ("Makefile", RECIPES)):
        assert "add -A" not in text, f"{where} stages everything"
        assert "add --all" not in text, f"{where} stages everything"
    # And what it does instead: the paths go in by name, from one tuple.
    assert 'git(root, "add", "--", *staging)' in CODE
    assert 'git(pages, "add", "--", *paths)' in CODE


# --------------------------------------------------------------------------- #
# The deploy branch, and the agent.


def test_the_built_site_is_copied_dotfiles_and_all(repo):
    """Without `.nojekyll` Pages runs Jekyll, Jekyll drops `_astro/`, and every
    page serves with no CSS and no error anywhere. `GO-LIVE.md` calls it the one
    silent breakage, which is why it is checked here rather than trusted.
    """
    pages = repo / "pages"
    _git(repo, "worktree", "add", "-q", "--detach", str(pages))
    _git(pages, "checkout", "-q", "--orphan", "gh-pages")

    assert autopublish.refresh(repo, pages) is True
    names = {p.name for p in pages.iterdir()}
    assert ".nojekyll" in names and "index.html" in names
    staged = _git(pages, "diff", "--cached", "--name-only").split()
    assert sorted(staged) == [".nojekyll", "index.html"]

    _git(pages, "-c", "user.email=t@e.invalid", "-c", "user.name=T",
         "commit", "-q", "-m", "Deploy")
    assert autopublish.refresh(repo, pages) is False, (
        "an unchanged build committed again, so every firing would add a commit"
    )


def test_a_build_that_is_not_there_is_not_deployed(repo):
    pages = repo / "pages"
    pages.mkdir()
    shutil.rmtree(repo / "astro" / "dist")
    with pytest.raises(autopublish.Refused) as refused:
        autopublish.refresh(repo, pages)
    assert "no built site" in str(refused.value)


def test_the_agent_renders_and_is_a_valid_plist(tmp_path):
    """`plutil -lint` is the whole of what can be checked without installing it.

    An agent that fires every fifteen minutes and pushes to a public site is
    not something a test run installs.
    """
    text = autopublish.plist(ROOT)
    left = re.findall(r"@[A-Z_]+@", text)
    assert not left, f"placeholders went unfilled: {left}"
    out = tmp_path / "agent.plist"
    out.write_text(text)
    subprocess.run(["plutil", "-lint", str(out)], check=True, capture_output=True)

    assert f"<string>{autopublish.LABEL}</string>" in text
    assert f"<integer>{autopublish.INTERVAL}</integer>" in text
    assert "<key>RunAtLoad</key>\n    <false/>" in text, (
        "installing the agent would publish immediately, which is not what "
        "installing it asks for"
    )
    # launchd gives a job /usr/bin:/bin:/usr/sbin:/sbin and nothing else, and
    # `make site` runs npm. A job that cannot find npm fails at the build every
    # time it fires.
    assert "<key>PATH</key>" in text
    assert str(Path(shutil.which("npm")).parent) in text


def test_the_agent_is_a_template_in_the_repository_and_not_written_anywhere():
    """Tracked as a template plus a target, so installing it is a thing the
    owner did rather than a thing that happened."""
    assert autopublish.PLIST.exists()
    assert "LaunchAgents" not in CODE, (
        "this module writes into ~/Library/LaunchAgents; that belongs in a "
        "target the owner runs"
    )
    assert "LaunchAgents" in MAKEFILE


def test_the_makefile_keeps_the_network_call_out_of_the_build():
    """`site` runs inside `verify` which runs in the pre-push hook.

    A pull there would break the build for anyone without the key and make it
    depend on a remote service being up.
    """
    site = MAKEFILE.split("\nsite:")[1].split("\n\n")[0]
    assert "autopublish" not in site and "pull" not in site


def test_the_operator_document_covers_the_four_things_it_has_to():
    doc = (ROOT / "artifacts" / "AUTOPUBLISH.md").read_text()
    assert "security add-generic-password" in doc
    assert str(autopublish.LOG).replace(str(Path.home()), "~") in doc
    assert "launchctl bootout" in doc
    assert "make autopublish-install" in doc
