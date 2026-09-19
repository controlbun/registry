"""Publishing the author's own artifacts, and pinning what was published.

Offline, against a stand-in Hub, for the reason `tests/test_fetch.py` gives: the
gate has to run from a clean checkout with no network. What is exercised here is
the part a real upload cannot check afterwards, which is whether a recorded pin
resolves back to the bytes this tree holds.

The probe that matters is the wrong pin. A commit that resolves to *something*
looks identical to a commit that resolves to the right thing until somebody
compares the bytes, and the failure mode is not a missing file: it is a
published row whose artifact the client then refuses, naming the author's own
file as the substituted one.
"""

from __future__ import annotations

import http.server
import json
import shutil
import socket
import subprocess
import sys
import threading
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

# Most of this file drives `publish.py` as a subprocess in a copied tree, which
# is what an operator does. The token-diagnosis tests below call one pure
# function instead, so the module is imported too.
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "artifacts"))
import publish  # noqa: E402

# Forty hex characters, so it passes `fetch.commit_sha`. Not a commit anything
# made: the stand-in Hub below answers to it and nothing else does.
SHA = "a" * 40
REPO = "author/directions"
WRONG = "author/somethingelse"


@pytest.fixture(scope="module")
def tree(tmp_path_factory) -> Path:
    """A copy of the writable parts of the repo, with a corpus built in it.

    Copied rather than used in place, because `fixtures/build.py` writes into
    `fixtures/` and `publish.py record` writes into `artifacts/`. A test that
    edits tracked files is a test that leaves the working tree dirty.
    """
    dest = tmp_path_factory.mktemp("publish") / "repo"
    dest.mkdir()
    for part in ("artifacts", "falsifier", "fixtures", "schema", "src"):
        shutil.copytree(ROOT / part, dest / part,
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    for script in (dest / "fixtures" / "build.py", dest / "artifacts" / "seed.py"):
        done = subprocess.run(
            [sys.executable, str(script), "--db", str(dest / "registry.db")],
            capture_output=True, text=True,
        )
        assert done.returncode == 0, done.stderr
    return dest


@pytest.fixture(scope="module")
def hub(tree):
    """A stand-in Hub: one commit, the real artifacts, and a repo that lies."""
    files = {
        f"artifacts/soham/{p.name}": p.read_bytes()
        for p in sorted((tree / "artifacts" / "soham").glob("*.safetensors"))
    }
    # Different bytes under the same path, which is the substitution case. A
    # committed synthetic fixture, so nothing here is fabricated.
    other = (tree / "fixtures" / "alice_kindness_v1.safetensors").read_bytes()

    class Handler(http.server.BaseHTTPRequestHandler):
        def _send(self, blob: bytes) -> None:
            self.send_response(200)
            self.send_header("Content-Length", str(len(blob)))
            self.end_headers()
            self.wfile.write(blob)

        def do_GET(self):  # noqa: N802
            for repo in (REPO, WRONG):
                if self.path == f"/api/models/{repo}/revision/main":
                    return self._send(json.dumps({"sha": SHA}).encode())
                if self.path == f"/api/models/{repo}":
                    return self._send(json.dumps({"id": repo}).encode())
                prefix = f"/{repo}/resolve/{SHA}/"
                if self.path.startswith(prefix):
                    path = self.path[len(prefix):]
                    if repo == WRONG:
                        return self._send(other)
                    if path in files:
                        return self._send(files[path])
            self.send_error(404)

        def log_message(self, *a):
            pass

    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    httpd = http.server.HTTPServer(("127.0.0.1", port), Handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{port}"
    httpd.shutdown()


def run(tree: Path, *args: str, hub: str | None = None) -> subprocess.CompletedProcess:
    env = {"PATH": "/usr/bin:/bin"}
    if hub:
        env["REGISTRY_HUB"] = hub
    # `--db` after the subcommand, which is where the parser takes it.
    command, rest = args[0], args[1:]
    return subprocess.run(
        [sys.executable, str(tree / "artifacts" / "publish.py"),
         command, "--db", str(tree / "registry.db"), *rest],
        capture_output=True, text=True, env=env, cwd=tree,
    )


def rebuild(tree: Path) -> subprocess.CompletedProcess:
    """What `make site` does: drop the corpus and write it again.

    `artifacts/seed.py` inserts, so it cannot run twice against one database.
    The pin has to survive this, which is the reason it is not only a column.
    """
    done = subprocess.run(
        [sys.executable, str(tree / "fixtures" / "build.py"),
         "--db", str(tree / "registry.db")],
        capture_output=True, text=True,
    )
    assert done.returncode == 0, done.stderr
    return subprocess.run(
        [sys.executable, str(tree / "artifacts" / "seed.py"),
         "--db", str(tree / "registry.db")],
        capture_output=True, text=True,
    )


def rows(tree: Path) -> dict[str, tuple]:
    import sqlite3
    conn = sqlite3.connect(tree / "registry.db")
    return {
        path: (repo, commit)
        for path, repo, commit in conn.execute(
            "SELECT artifact_path, artifact_repo, artifact_commit FROM intervention"
        )
    }


# --------------------------------------------------------------------------- #
# the dry run


def test_plan_touches_the_network_for_nothing(tree):
    """A dry run that reaches the Hub behaves differently on a train.

    Pointed at a host nothing is listening on. A plan that reads anything
    remote fails here; one that does not is unaffected.
    """
    done = run(tree, "plan", hub="http://127.0.0.1:1")
    assert done.returncode == 0, done.stderr
    assert "nothing was uploaded" in done.stdout


def test_the_plan_puts_the_file_at_the_path_the_row_carries(tree):
    """`fetch.resolve` has one path field for three sources.

    So the path inside the Hub repo and the repository-relative path are the
    same string, or the remote fetch 404s while the local file keeps working
    and nobody notices until somebody without a checkout tries.
    """
    done = run(tree, "plan")
    lines = [l.split() for l in done.stdout.splitlines()]
    here = [w[1] for w in lines if w and w[0] == "from"]
    there = [w[3] for w in lines if w and w[0] == "to"]
    assert here and here == there, (
        f"the plan sends {here} to {there}. These are one field in the schema."
    )

    # The `hf upload` lines take the local path and the path in the repo as two
    # separate arguments, and this is the one place they can differ.
    uploads = [l.split() for l in done.stdout.splitlines()
               if l.strip().startswith("hf upload")]
    assert uploads, "the plan no longer prints the by-hand equivalent"
    for words in uploads:
        local, in_repo = words[3], words[4]
        assert local == in_repo, (
            f"the plan would upload {local} to {in_repo}. One path field is "
            "used against every source, so these cannot differ."
        )


def test_synthetic_fixtures_are_never_in_the_plan(tree):
    """Nothing in `fixtures/` is a measurement, and it does not get published."""
    done = run(tree, "plan")
    assert "fixtures/" not in done.stdout


# --------------------------------------------------------------------------- #
# the pin


def test_a_branch_name_is_not_a_pin(tree):
    done = run(tree, "record", "--repo", REPO, "--commit", "main")
    assert done.returncode != 0
    assert "not a commit SHA" in (done.stdout + done.stderr)


def test_record_writes_the_file_and_the_rows(tree, hub):
    done = run(tree, "record", "--repo", REPO, "--at-head", hub=hub)
    assert done.returncode == 0, done.stderr

    recorded = json.loads((tree / "artifacts" / "published.json").read_text())
    assert set(recorded["files"]) == {
        f"artifacts/soham/{p.name}"
        for p in (tree / "artifacts" / "soham").glob("*.safetensors")
    }
    # The host and the layout are half the pin since `schema/migrations/007`,
    # and they are recorded rather than assumed: derived from the host this
    # uploader actually pushed to, which under `REGISTRY_HUB` is the stand-in
    # above. A recorded Hub is what makes a recorded GitHub possible.
    host = hub.split("//", 1)[1]
    assert all(
        v == {"repo": REPO, "commit": SHA, "host": host,
              "url_template": "http://{host}/{repo}/resolve/{commit}/{path}"}
        for v in recorded["files"].values()
    ), recorded["files"]

    written = rows(tree)
    assert all(written[p] == (REPO, SHA) for p in recorded["files"])
    assert all(written[p] == (None, None) for p in written
               if p.startswith("fixtures/")), (
        "a pin reached a synthetic row"
    )


def test_a_rebuild_keeps_the_pin(tree, hub):
    """`make site` drops the database. A pin that lived only in a column is gone.

    This is the whole reason `published.json` exists, and the failure it guards
    is silent: the row falls back to the local file, which is present on the
    machine that ran the build and nowhere else.
    """
    done = rebuild(tree)
    assert done.returncode == 0, done.stderr
    written = rows(tree)
    assert any(v == (REPO, SHA) for v in written.values())


def test_a_pin_naming_no_row_is_refused(tree, hub):
    """A renamed artifact and an unrenamed pin. A zero-row update is silent."""
    pins = tree / "artifacts" / "published.json"
    kept = pins.read_text()
    try:
        record = json.loads(kept)
        record["files"]["artifacts/soham/not_a_file.safetensors"] = {
            "repo": REPO, "commit": SHA,
        }
        pins.write_text(json.dumps(record))
        done = rebuild(tree)
        assert done.returncode != 0
        assert "no non-synthetic intervention row" in done.stderr
    finally:
        pins.write_text(kept)
        assert rebuild(tree).returncode == 0


# --------------------------------------------------------------------------- #
# the round trip


def test_verify_round_trips_every_pinned_artifact(tree, hub):
    done = run(tree, "verify", hub=hub)
    assert done.returncode == 0, done.stdout + done.stderr
    assert "round-trip" in done.stdout
    assert "client.load" in done.stdout, (
        "the consumer path is the sentence this exercise is for and it is not "
        "in the output"
    )


def test_verify_refuses_a_commit_holding_other_bytes(tree, hub):
    """The failure a live upload cannot rule out by itself.

    The fetch succeeds, the file is there, the shape and the dtype are right for
    a great many tensors, and the artifact is not the one the row describes.
    """
    pins = tree / "artifacts" / "published.json"
    kept = pins.read_text()
    try:
        pins.write_text(kept.replace(REPO, WRONG))
        subprocess.run(
            [sys.executable, str(tree / "artifacts" / "publish.py"), "record",
             "--db", str(tree / "registry.db"),
             "--repo", WRONG, "--commit", SHA],
            capture_output=True, text=True, check=True,
        )
        done = run(tree, "verify", hub=hub)
        assert done.returncode == 1
        assert "WRONG PIN" in done.stdout
    finally:
        pins.write_text(kept)
        subprocess.run(
            [sys.executable, str(tree / "artifacts" / "publish.py"), "record",
             "--db", str(tree / "registry.db"),
             "--repo", REPO, "--commit", SHA],
            capture_output=True, text=True, check=True,
        )


def test_a_403_is_answered_with_what_the_token_can_reach(monkeypatch):
    """The Hub says "make sure your token has the correct permissions" and
    leaves the reader to find out which. A fine-grained token knows."""
    monkeypatch.setattr(publish, "_token", lambda: "hf_not_a_real_token")

    class Reply:
        def read(self): return json.dumps({
            "name": "someone",
            "auth": {"accessToken": {"displayName": "scoped", "fineGrained": {
                "scoped": [
                    {"entity": {"type": "org", "name": "controlbun"},
                     "permissions": ["repo.write"]},
                    {"entity": {"type": "user", "name": "someone"},
                     "permissions": []},
                ], "global": []}}},
        }).encode()
        def __enter__(self): return self
        def __exit__(self, *a): return False

    monkeypatch.setattr(publish.urllib.request, "urlopen", lambda *a, **k: Reply())
    said = str(publish._read_the_token(RuntimeError("403 Forbidden"),
                                       "someone/directions"))
    assert "no permissions at all" in said
    assert "can write to controlbun" in said
    assert "not an answer here" in said, "and why that namespace is refused"
    assert "settings/tokens" in said
    assert "Nothing was uploaded" in said


def test_a_failure_that_is_not_about_permissions_is_handed_back_untouched():
    original = RuntimeError("connection reset by peer")
    assert publish._read_the_token(original, "someone/x") is original
