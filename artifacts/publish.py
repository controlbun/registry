"""Publish the author's own artifacts to the author's own Hub namespace, and pin them.

Four steps, separable on purpose, because one of them is a network write the
author runs himself and the other three are not.

    plan     what would go where, and under what path. Reads nothing remote.
    push     the upload. Needs `huggingface_hub` and a token, and is optional:
             the same commit can be made by hand in the web UI or by `hf upload`.
    record   write `artifact_repo` and `artifact_commit` onto the rows, so
             `fetch.resolve` takes the remote branch instead of the local file.
    verify   fetch it back through `registry.fetch` with an empty cache and
             check the bytes against the local file and against the row.

**The author's namespace, never `controlbun/*`.** `artifact_repo` records where
the author published an artifact, which is provenance. `served_repo` records
where this registry serves a copy from, and `schema/migrations/004` keeps the
two apart because one pair of columns cannot express a mirror that has drifted
from its origin. Nothing here writes `served_repo` or anything like it: serving
a copy makes this a distributor and needs the dual-use policy, which is deferred
until a capability arrives rather than until a date (`DECISIONS.md`,
2026-09-17). An author publishing his own bytes under his own account, with this
registry recording the pointer, is not that capability. `upload` refuses that
namespace rather than only describing the rule, because the second caller takes
its repo out of a text field.

**The path inside the Hub repo is `artifact_path`, character for character.**
`fetch.resolve` hands one path field to whichever of the three sources it picks,
so the repository-relative path and the path in the Hub repo are the same string
or the remote fetch returns a 404. That is 004's "our copy keeps the author's
filename" read against the code that uses it. It is also why the plan prints the
path twice: the `hf upload` argument that would get this wrong is the second one.

**Why the pin is a file and not only a row.** `make site` drops the database and
rebuilds it from `fixtures/build.py` and `artifacts/seed.py`, so a commit written
only into a column is gone on the next build, and the artifact silently falls
back to the local file on a machine that has one. `published.json` is the record
and `apply_pins` is the only thing that writes those two columns; the rebuild and
`record` both call it, so there is one of it rather than two.

**Resolving a branch to a commit lives here rather than in `registry.fetch`.**
That module says in its own docstring that it does not resolve a branch or a
tag, and a helper sitting next to it that did would be one refactor away from
being wired into the read path. Asking the Hub what `main` points at right now,
and then freezing the answer, is an author-side operation that happens once per
upload. What gets recorded is forty hex characters either way: `fetch.commit_sha`
is the one rule and this file states none of its own.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "src"))

from registry import artifact, client, db, fetch  # noqa: E402
from registry.artifact import local_path  # noqa: E402

# The pin record. Tracked, because it is the only durable copy of the commit.
PINS = HERE / "published.json"

# The author's own account, which is what `artifact_repo` is for. `controlbun`
# is the organization that owns this registry, and a repo under it would be a
# copy this project serves rather than a thing the author published. Override
# with `--repo`; the value that ends up in a row is whatever was recorded.
DEFAULT_REPO = "sohampadia/pro-human"

# A Hub model repo, because `fetch.hub_url` builds `{repo}/resolve/{commit}/{path}`
# and that is the layout the Hub serves models under. A dataset repo lives at
# `/datasets/{repo}/resolve/...` and the URL builder cannot address it. This is a
# fact about one function, not a rule about where artifacts may live: point it at
# another host by setting `REGISTRY_HUB`, and a layout neither of those serve
# needs a line in `fetch.hub_url` rather than permission from anybody.
REPO_TYPE = "model"

# The namespace this registry itself owns. Uploading into it would write bytes
# this project serves, which is `served_repo` and a different column, and which
# fires the first of the three dual-use triggers (`DECISIONS.md`, 2026-09-17).
OUR_NAMESPACE = "controlbun"


class PinError(ValueError):
    """A recorded pin that does not match anything, or does not resolve."""


class ServedCopy(ValueError):
    """An upload aimed at this registry's own namespace rather than an author's.

    The docstring above says never `controlbun/*` and said it in prose only,
    which is the shape `CLAUDE.md` calls aspirational. It is a check now because
    a second caller arrived: `artifacts/intake.py` takes a repo out of a form
    field, and the difference between publishing your own bytes and serving a
    copy of somebody's is one word typed into a text box.
    """


# --------------------------------------------------------------------------- #
# The pin record, and the one function that writes the two columns.


def read_pins(path: Path = PINS) -> dict[str, dict]:
    """The recorded pins, keyed by `artifact_path`. Absent is empty, not an error."""
    if not path.exists():
        return {}
    return json.loads(path.read_text()).get("files", {})


def write_pins(files: dict[str, dict], path: Path = PINS) -> None:
    """Rewrite the record, keeping whatever note the file already carried."""
    existing = json.loads(path.read_text()) if path.exists() else {}
    existing["files"] = {k: files[k] for k in sorted(files)}
    path.write_text(json.dumps(existing, indent=2) + "\n")


def apply_pins(conn, path: Path = PINS) -> list[tuple[str, str, str]]:
    """Write every recorded pin onto its row. Returns what it wrote.

    Called by `artifacts/seed.py` after it inserts, and by `record` against a
    database that already exists. One implementation, because the rebuild and
    the recording step are writing the same two columns from the same file and
    two spellings of that is how the two go out of step.

    A pin naming a path no row carries is an error rather than a no-op. The
    interesting way for this to be wrong is a renamed artifact, and a silent
    zero-row update would leave the row pointing at a local file forever while
    the record claimed it was published.
    """
    written: list[tuple[str, str, str]] = []
    for rel, pin in sorted(read_pins(path).items()):
        repo = pin["repo"]
        # The one rule about what a pin may be, stated in `registry.fetch` and
        # reused here rather than restated. A branch name in this file is
        # refused at build time, which is the earliest anything reads it.
        commit = fetch.commit_sha(pin["commit"])
        cur = conn.execute(
            "UPDATE intervention SET artifact_repo=?, artifact_commit=?"
            " WHERE artifact_path=? AND is_synthetic=0",
            (repo, commit, rel),
        )
        if cur.rowcount == 0:
            raise PinError(
                f"{path.name} pins {rel} at {repo}@{commit[:12]}, and no "
                "non-synthetic intervention row carries that artifact_path. "
                "Either the artifact was renamed and the pin was not, or the "
                "pin is for a corpus this database does not hold."
            )
        written.append((rel, repo, commit))
    conn.commit()
    return written


# --------------------------------------------------------------------------- #
# What there is to publish.


@dataclass(frozen=True)
class Item:
    """One artifact, its row, and the bytes checked against that row."""

    ref: str
    # Repository-relative on disk and, once published, the path inside the Hub
    # repo. One field because `fetch.resolve` has one field.
    path: str
    local: Path
    size: int
    sha256: str
    shape: str
    dtype: str
    repo: str | None
    commit: str | None

    @property
    def pinned(self) -> bool:
        return bool(self.repo and self.commit)


def select(conn, only: list[str] | None = None) -> list[Item]:
    """Every real artifact this repository holds bytes for, checked as it goes.

    Synthetic rows are left out and that is not a quality judgment about them:
    `fixtures/SYNTHETIC.md` says nothing in that directory is a measurement, and
    uploading a fabricated direction under the author's name would publish a
    file whose whole point is that it is not one.

    Each row's bytes are confirmed against what the row records before anything
    plans to upload them. Publishing bytes that disagree with the row would pin
    a commit the client then refuses, and it would do it under the author's own
    account, which is the worst place to find out.
    """
    rows = conn.execute(
        "SELECT author, label, version, artifact_path, artifact_sha256, shape,"
        " dtype, artifact_repo, artifact_commit FROM intervention"
        " WHERE is_synthetic=0 AND artifact_path IS NOT NULL"
    ).fetchall()

    items: list[Item] = []
    for row in rows:
        rel = row["artifact_path"]
        if only and rel not in only:
            continue
        path = local_path(rel, root=ROOT)
        if not path.exists():
            # A row this registry points at rather than holds. There is nothing
            # here to upload, and that is a state rather than a failure.
            continue
        blob = path.read_bytes()
        facts = artifact.confirmed(
            blob,
            artifact.Claim(shape=row["shape"], dtype=row["dtype"],
                           sha256=row["artifact_sha256"]),
            subject=rel,
        )
        items.append(Item(
            ref=f"{row['author']}/{row['label']}@{row['version']}",
            path=rel,
            local=path,
            size=len(blob),
            sha256=facts.sha256,
            shape=facts.shape,
            dtype=facts.dtype,
            repo=row["artifact_repo"],
            commit=row["artifact_commit"],
        ))

    missing = sorted(set(only or []) - {i.path for i in items})
    if missing:
        raise SystemExit(
            "--only names paths that are not real artifacts with bytes here: "
            + ", ".join(missing)
        )
    return items


# --------------------------------------------------------------------------- #
# The Hub, on the two occasions this needs to talk to it directly.


def repo_exists(repo: str, *, timeout: int = 30) -> bool:
    """Whether a public model repo is there, asked without a token."""
    try:
        fetch.get_url(f"{fetch.HUB}/api/models/{repo}", timeout=timeout)
        return True
    except fetch.FetchError:
        return False


def head_commit(repo: str, branch: str = "main", *, timeout: int = 30) -> str:
    """What a branch points at right now, for the caller to freeze.

    Reading a branch is not the same as pinning one. Nothing here records the
    branch name: the answer goes through `fetch.commit_sha` and forty hex
    characters is what reaches a row, so a later push to the same branch does
    not move a submission that was already published.
    """
    raw = fetch.get_url(
        f"{fetch.HUB}/api/models/{repo}/revision/{branch}",
        timeout=timeout,
        not_found=(
            f"{repo} has no branch {branch}, or the repo is not publicly "
            "readable. Nothing here sends credentials on a read."
        ),
    )
    info = json.loads(raw)
    sha = info.get("sha")
    if not sha:
        raise SystemExit(
            f"the Hub's answer for {repo}@{branch} carries no sha, so there is "
            "no commit to pin. Pass --commit with the one you mean."
        )
    return fetch.commit_sha(sha)


def _token() -> str:
    """The upload token, from the environment or from `.env`.

    Never printed, never written anywhere, and never passed on a command line.
    `.env` is gitignored and is where this project's secrets live, so reading it
    here saves the author from putting the value into a shell invocation.
    """
    token = os.environ.get("HF_TOKEN")
    if token:
        return token
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text().splitlines():
            if line.startswith("HF_TOKEN="):
                return line.split("=", 1)[1].strip()
    raise SystemExit(
        "no HF_TOKEN in the environment or in .env, so there is nothing to "
        "authenticate an upload with. Uploading is the one thing here that "
        "needs a credential; plan, record and verify do not."
    )


# --------------------------------------------------------------------------- #
# The four steps.


def cmd_plan(args, conn) -> int:
    """Everything that would happen, and nothing happening.

    No network at all, including reads. A dry run that talks to the Hub is a dry
    run that behaves differently on a train.
    """
    items = select(conn, args.only)
    if not items:
        print("nothing to publish: no non-synthetic row has bytes in this tree")
        return 0

    print(f"plan: {len(items)} artifact(s) -> {args.repo}, a {REPO_TYPE} repo")
    print()
    for item in items:
        print(f"  {item.ref}")
        print(f"    from    {item.path}")
        print(f"    to      {args.repo} : {item.path}")
        print(f"    bytes   {item.size}  sha256 {item.sha256}")
        print(f"    tensor  {item.shape} {item.dtype}, and the row agrees")
        if item.pinned:
            print(f"    pinned  {item.repo}@{item.commit}")
        else:
            print("    pinned  not yet; the row resolves to the local file")
        print()

    print("the same upload by hand, one commit per file:")
    for item in items:
        print(f"  hf upload {args.repo} {item.path} {item.path} "
              f"--repo-type {REPO_TYPE}")
    print()
    print("nothing was uploaded, nothing was written, and nothing was fetched.")
    return 0


MISSING_HUB_LIBRARY = (
    "huggingface_hub is not installed in this environment, so the upload "
    "cannot run here. Two ways on:\n"
    "  uv pip install --python .venv/bin/python -e '.[publish]'\n"
    "  artifacts/publish.py plan   # prints the `hf upload` equivalent\n"
    "The upload is the only thing that needs it. Recording the pin and "
    "checking the round trip do not, which is why they are separate steps "
    "and why the client never imports it."
)


def upload(files: list[tuple[str, Path]], *, repo: str, message: str,
           create: bool = False) -> tuple[str, str]:
    """Put bytes at paths in a Hub repo, in one commit. Returns commit and URL.

    Split out of `cmd_push` when `artifacts/intake.py` needed the same network
    write for bytes that are not a row in this database yet: an operator drops
    a file, it is converted and checked, and it goes to the author's namespace
    without ever being an artifact this tree holds. Two spellings of an upload
    would be two places for the namespace guard and the token handling to come
    apart, and the token is the half that must not.

    `files` is `(path_in_repo, local_file)`, and the caller is responsible for
    the first being the `artifact_path` its row records. That equality is the
    constraint in this module's docstring and it is not re-derived here, because
    the two callers arrive at it differently: `select` reads it off a row and
    intake takes it from a field somebody typed.
    """
    try:
        from huggingface_hub import CommitOperationAdd, HfApi  # noqa: PLC0415
    except ImportError:
        raise RuntimeError(MISSING_HUB_LIBRARY) from None

    if repo.split("/")[0] == OUR_NAMESPACE:
        raise ServedCopy(
            f"{repo} is under {OUR_NAMESPACE}, which is this registry's own "
            "namespace. Bytes put there are a copy this project serves rather "
            "than a thing an author published, which is `served_repo` and a "
            "different column, and it makes this a distributor. That is the "
            "first of the three triggers in DECISIONS.md 2026-09-17 and the "
            "dual-use policy it names does not exist yet. Publish under your "
            "own account."
        )

    api = HfApi(endpoint=fetch.HUB, token=_token())

    if not repo_exists(repo):
        if not create:
            raise FileNotFoundError(
                f"{repo} does not exist or is not public. Create it in the web "
                "UI, or ask for it to be created here. Creating a repo is a "
                "write and this does not make one by accident."
            )
        api.create_repo(repo, repo_type=REPO_TYPE, exist_ok=True)

    # One commit for every file, so one SHA pins the set and a reader sees the
    # publication as the single act it was.
    info = api.create_commit(
        repo,
        [CommitOperationAdd(path_in_repo=rel, path_or_fileobj=str(local))
         for rel, local in files],
        commit_message=message,
        repo_type=REPO_TYPE,
    )
    return fetch.commit_sha(info.oid), info.commit_url


def cmd_push(args, conn) -> int:
    """The upload. The one step that writes to somebody else's server."""
    items = select(conn, args.only)
    if not items:
        print("nothing to publish")
        return 0

    try:
        commit, url = upload(
            [(i.path, i.local) for i in items],
            repo=args.repo, message=args.message, create=args.create,
        )
    except (RuntimeError, FileNotFoundError) as stopped:
        raise SystemExit(str(stopped)) from stopped

    print(f"pushed {len(items)} file(s) to {args.repo}")
    print(f"  commit {commit}")
    print(f"  {url}")
    print()
    print("nothing has been recorded yet. Next:")
    print(f"  .venv/bin/python artifacts/publish.py record --repo {args.repo} "
          f"--commit {commit}")
    return 0


def cmd_record(args, conn) -> int:
    """Write the pin into `published.json` and onto the rows."""
    items = select(conn, args.only)
    if not items:
        print("nothing to record")
        return 0

    if args.commit:
        commit = fetch.commit_sha(args.commit)
    elif args.at_head:
        commit = head_commit(args.repo, args.branch)
        print(f"{args.repo}@{args.branch} is at {commit}, frozen as of now")
    else:
        raise SystemExit(
            "pass --commit with the forty hex characters the upload produced, "
            "or --at-head to read the branch and freeze what it points at. A "
            "branch name is not recorded either way."
        )

    files = read_pins()
    for item in items:
        was = files.get(item.path)
        files[item.path] = {"repo": args.repo, "commit": commit}
        if was and (was["repo"], was["commit"]) != (args.repo, commit):
            print(f"  repinned {item.path}")
            print(f"    was {was['repo']}@{was['commit']}")
    write_pins(files)
    print(f"wrote {PINS.relative_to(ROOT)}")

    for rel, repo, sha in apply_pins(conn):
        print(f"  {rel} -> {repo}@{sha[:12]}")
    print()
    print("the rows resolve remotely now. Check that they actually do:")
    print("  .venv/bin/python artifacts/publish.py verify")
    return 0


def cmd_verify(args, conn) -> int:
    """Fetch every pinned artifact back and compare it to the bytes here.

    **Why an empty cache.** `fetch.CACHE` is keyed by commit and never expires,
    which is right in use and would make this check pass on bytes this machine
    already had. A directory per run leaves the author's real cache alone and
    makes the network step actually happen, which is the thing under test.
    `REGISTRY_CACHE` still sets the cache for everything else.

    **Three questions, in order.** Do the remote bytes arrive; are they the
    bytes in this tree; and do they satisfy the row. The first two are what a
    wrong pin breaks, and the third is what the client will ask on everybody
    else's machine.
    """
    items = [i for i in select(conn, args.only) if i.pinned]
    if not items:
        print("no row carries a repo and a commit, so there is no pin to check. "
              "Publish first, then record.")
        return 0

    failures = 0
    with tempfile.TemporaryDirectory(prefix="registry-verify-") as tmp:
        was, fetch.CACHE = fetch.CACHE, Path(tmp)
        try:
            for item in items:
                print(f"  {item.ref}")
                print(f"    {item.repo}@{item.commit[:12]} : {item.path}")
                try:
                    remote = fetch.resolve(
                        artifact_path=item.path,
                        artifact_repo=item.repo,
                        artifact_commit=item.commit,
                    )
                except fetch.FetchError as unreachable:
                    print(f"    WRONG PIN  {unreachable}")
                    failures += 1
                    continue

                if remote != item.local.read_bytes():
                    print(f"    WRONG PIN  {len(remote)} bytes came back and "
                          f"they are not the {item.size} in {item.path}. The "
                          "commit names bytes this tree does not hold.")
                    failures += 1
                    continue

                try:
                    facts = artifact.confirmed(
                        remote,
                        artifact.Claim(shape=item.shape, dtype=item.dtype,
                                       sha256=item.sha256),
                        subject=item.ref,
                    )
                except artifact.MismatchedArtifact as mismatch:
                    print(f"    WRONG PIN  {mismatch}")
                    failures += 1
                    continue

                # The consumer path end to end, which is the sentence this whole
                # exercise is for: the client resolves a pinned reference to a
                # tensor on a machine with no checkout of the artifacts. Caught
                # rather than raised, so one bad row does not skip the rest of
                # the report, which is the thing an operator came here for.
                try:
                    vector = client.load(item.ref, database=args.db).vector()
                except (client.NotFound, client.Ambiguous,
                        artifact.MismatchedArtifact, fetch.FetchError) as refused:
                    print(f"    WRONG PIN  the client refuses it: {refused}")
                    failures += 1
                    continue

                print(f"    ok  {len(remote)} bytes, {facts.shape} {facts.dtype}, "
                      f"sha256 {facts.sha256[:16]}")
                print(f"        client.load(\"{item.ref}\").vector() -> "
                      f"{list(vector.shape)} {vector.dtype}")
        finally:
            fetch.CACHE = was

    if failures:
        print(f"\n{failures} pin(s) do not resolve to the bytes recorded for "
              "them. A row pointing at bytes that are not the artifact is worse "
              "than a row pointing at nothing: the client refuses it and names "
              "the author's own file as the substituted one. Fix the pin or "
              "re-upload before this is published.", file=sys.stderr)
        return 1

    print(f"\n{len(items)} pin(s) round-trip: fetched from the Hub, byte "
          "identical to this tree, and confirmed against the row.")
    return 0


# --------------------------------------------------------------------------- #


def main(argv: list[str] | None = None) -> int:
    # Shared options live on a parent so they are typed after the subcommand,
    # where anybody would look for them. Adding them to the top-level parser as
    # well would read the same and behave differently: a subparser's default
    # overwrites a value the top level already parsed, silently.
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--db", default=str(ROOT / "registry.db"))
    common.add_argument("--only", action="append",
                        help="an artifact_path; repeatable. Default is all of them.")

    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="command", required=True)

    plan = sub.add_parser("plan", parents=[common],
                          help="what would happen. No network.")
    plan.add_argument("--repo", default=DEFAULT_REPO)
    plan.set_defaults(fn=cmd_plan)

    push = sub.add_parser("push", parents=[common],
                          help="upload. Needs huggingface_hub and a token.")
    push.add_argument("--repo", default=DEFAULT_REPO)
    push.add_argument("--create", action="store_true",
                      help="create the repo if it is not there")
    push.add_argument("--message", default="Publish steering directions")
    push.set_defaults(fn=cmd_push)

    record = sub.add_parser("record", parents=[common],
                            help="write the pin into the record and the rows")
    record.add_argument("--repo", default=DEFAULT_REPO)
    record.add_argument("--commit", help="forty hex characters")
    record.add_argument("--at-head", action="store_true",
                        help="ask the Hub what the branch points at and freeze it")
    record.add_argument("--branch", default="main")
    record.set_defaults(fn=cmd_record)

    verify = sub.add_parser("verify", parents=[common],
                            help="fetch it back and check the bytes")
    verify.set_defaults(fn=cmd_verify)

    args = ap.parse_args(argv)
    conn = db.connect(args.db)
    try:
        return args.fn(args, conn)
    except (fetch.FetchError, PinError, ServedCopy,
            artifact.MismatchedArtifact) as refused:
        # A sentence, not a traceback. Every one of these is a refusal with the
        # reason already written into it, and the reader is an operator halfway
        # through publishing rather than somebody debugging this file.
        raise SystemExit(str(refused)) from refused


if __name__ == "__main__":
    raise SystemExit(main())
