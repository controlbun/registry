"""Resolving an artifact to bytes, and refusing the wrong ones.

Most of this runs against a local HTTP server rather than the Hub, so `make verify`
stays offline and rerunnable from a clean checkout. One test does hit the real Hub
and skips when there is no network, because the thing it checks cannot be faked:
that a real LFS object, which is what every artifact will be, redirects to a CDN
and still arrives byte-identical.

The stand-in serves two layouts, not one. A row carries its own URL template
since `schema/migrations/007`, and a test server that only knew the Hub's shape
could not tell a resolver that reads the template from one that ignores it.
"""

from __future__ import annotations

import hashlib
import http.server
import socket
import sqlite3
import sys
import threading
import urllib.error
import urllib.request
from pathlib import Path

import numpy as np
import pytest
from safetensors.numpy import load as load_bytes
from safetensors.numpy import save

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from controlbun import client, db, fetch  # noqa: E402

SHA = "c1e0da3fb595874da299e783c7ad9c08a95ce7e9"
BLOB = save({"t": np.arange(8, dtype=np.float32)})

# What the same repo, commit and path serve through a second layout. Standing in
# for the git-LFS pointer `raw.githubusercontent.com` returns where
# `media.githubusercontent.com` returns the object: one repo, one commit, one
# path, two templates, two sets of bytes. Confirmed against the real hosts on
# 2026-09-18; see `artifacts/source.py`.
OTHER = save({"t": np.arange(8, dtype=np.float32) + 100})

# A GitHub-shaped pin: the host the repo is on is not the host that serves the
# file, which is why a row records both and why neither derives from the other.
GITHUB_HOST = "github.com"


@pytest.fixture(autouse=True)
def isolated_cache(tmp_path, monkeypatch):
    """A cache per test.

    The real cache is keyed by URL and never expires, which is correct in
    production and would make these tests pass on yesterday's bytes.
    """
    monkeypatch.setattr(fetch, "CACHE", tmp_path / "cache")


@pytest.fixture
def server(monkeypatch):
    """Two layouts on one socket, with `HUB` pointed at it.

    `/org/repo/resolve/{sha}/...` is the Hub's, which is what a row recording no
    host of its own resolves under. `/media/org/repo/{sha}/...` stands in for
    GitHub's media host, which takes the commit in a different position and does
    not carry the host the repo is on anywhere in it.
    """
    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):  # noqa: N802
            hub = f"/org/repo/resolve/{SHA}/t.safetensors"
            media = f"/media/org/repo/{SHA}/t.safetensors"
            raw = f"/raw/org/repo/{SHA}/t.safetensors"
            if self.path in (hub, media):
                return self._send(BLOB)
            if self.path == raw:
                return self._send(OTHER)
            if self.path.endswith("/redirected.safetensors"):
                # LFS objects redirect to a CDN. The real fetch has to follow it.
                self.send_response(302)
                self.send_header("Location", hub)
                self.end_headers()
                return
            self.send_error(404)

        def _send(self, blob):
            self.send_response(200)
            self.send_header("Content-Length", str(len(blob)))
            self.end_headers()
            self.wfile.write(blob)

        def log_message(self, *a):
            pass

    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    httpd = http.server.HTTPServer(("127.0.0.1", port), Handler)
    # `poll_interval` rather than the 0.5s default, because `shutdown()`
    # blocks until this loop notices the flag. Two servers per test at
    # half a second each was a flat one second of teardown on every
    # test in this file, measured as the largest single cost in the
    # suite on 2026-09-20. It is a poll interval and not a sleep: the
    # shutdown still waits for the loop to actually exit, so nothing
    # here races.
    threading.Thread(
        target=lambda: httpd.serve_forever(poll_interval=0.01),
        daemon=True,
    ).start()
    monkeypatch.setattr(fetch, "HUB", f"http://127.0.0.1:{port}")
    yield f"127.0.0.1:{port}"
    httpd.shutdown()


def media_template(where: str) -> str:
    """GitHub's shape: the serving host is not the host the repo is on."""
    return f"http://{where}/media/{{repo}}/{{commit}}/{{path}}"


def raw_template(where: str) -> str:
    return f"http://{where}/raw/{{repo}}/{{commit}}/{{path}}"


# ------------------------------------------------------- a row with no host


def test_a_pinned_fetch_returns_the_bytes(server):
    assert fetch.from_repo(repo="org/repo", commit=SHA,
                           path="t.safetensors") == BLOB


def test_a_redirect_is_followed(server):
    """Every real artifact is an LFS object and every LFS object redirects."""
    assert fetch.from_repo(repo="org/repo", commit=SHA,
                           path="redirected.safetensors") == BLOB


def test_a_missing_commit_says_so_rather_than_falling_back(server):
    with pytest.raises(fetch.FetchError, match="no t.safetensors|does not exist"):
        fetch.from_repo(repo="org/repo", commit="b" * 40, path="t.safetensors")


def test_the_second_fetch_comes_from_cache(server, monkeypatch):
    fetch.from_repo(repo="org/repo", commit=SHA, path="t.safetensors")

    def explode(*a, **k):
        raise AssertionError("refetched something already cached")

    monkeypatch.setattr(urllib.request, "urlopen", explode)
    assert fetch.from_repo(repo="org/repo", commit=SHA,
                           path="t.safetensors") == BLOB


@pytest.mark.parametrize("ref", ["main", "v1.0", "abc123", "", "HEAD", "a" * 39])
def test_only_a_commit_sha_resolves(ref):
    """A tag is movable by the repo owner, so pinning to one pins to nothing."""
    with pytest.raises(fetch.FetchError, match="not a commit SHA"):
        fetch.pinned_url(host="h", repo="org/repo", commit=ref,
                         path="t.safetensors",
                         url_template="https://{host}/{repo}/{commit}/{path}")


def test_a_row_recording_no_host_resolves_where_it_always_did():
    """Absence is a state. Every row in this database is one of these."""
    host, template = fetch.hub_pin()
    url = fetch.pinned_url(host=host, repo="org/repo", commit=SHA,
                           path="t.safetensors", url_template=template)
    assert url.endswith(f"/org/repo/resolve/{SHA}/t.safetensors")
    assert url.startswith(fetch.HUB + "/")


# ------------------------------------------------- a row that names its host


def test_a_github_shaped_pin_resolves_through_its_own_template(server):
    """The read path stops knowing any host by name.

    Nothing in `controlbun.fetch` has heard of this layout. The row carries it,
    and that is the whole mechanism.
    """
    assert fetch.from_repo(
        repo="org/repo", commit=SHA, path="t.safetensors",
        host=GITHUB_HOST, url_template=media_template(server),
    ) == BLOB


def test_one_repo_and_two_templates_are_two_sets_of_bytes(server):
    """The cache key has to carry the template, and this is why.

    `github.com/soham-padia/steering-arena` at one commit and one path serves
    the LFS object through the media host and a 130-byte pointer through the
    raw host. Keyed on repo, commit and path, the second fetch here would hand
    back the first one's bytes.
    """
    through_media = fetch.from_repo(
        repo="org/repo", commit=SHA, path="t.safetensors",
        host=GITHUB_HOST, url_template=media_template(server))
    through_raw = fetch.from_repo(
        repo="org/repo", commit=SHA, path="t.safetensors",
        host=GITHUB_HOST, url_template=raw_template(server))
    assert through_media == BLOB
    assert through_raw == OTHER
    assert through_media != through_raw


def test_two_hosts_with_one_repo_slug_do_not_collide(server):
    """`github.com/a/b` and `huggingface.co/a/b` are two repositories.

    The collision `PinnedRepoFile` names on the way in, checked on the way out.
    """
    elsewhere = fetch.from_repo(
        repo="org/repo", commit=SHA, path="t.safetensors",
        host=GITHUB_HOST, url_template=raw_template(server))
    on_the_hub = fetch.from_repo(repo="org/repo", commit=SHA,
                                 path="t.safetensors")
    assert elsewhere == OTHER
    assert on_the_hub == BLOB


def test_a_template_may_name_a_host_nothing_here_has_heard_of(server):
    """No code change, no entry in a table, no asking anybody."""
    url = fetch.pinned_url(
        host="vectors.example.invalid", repo="a/b", commit=SHA, path="d.st",
        url_template="https://cdn.example.invalid/{repo}@{commit}/{path}")
    assert url == f"https://cdn.example.invalid/a/b@{SHA}/d.st"


# ------------------------------------------------------ what a template may not do


def test_a_template_that_drops_the_pin_is_refused():
    """V1.md's S2, closed.

    A repo carrying a `?` used to turn `{repo}/resolve/{commit}/{path}` into a
    query string on a bare repo URL. The fetch then returned whatever is at
    HEAD and nothing downstream could tell.
    """
    url = fetch.pinned_url(host="h.example", repo="org/repo?x", commit=SHA,
                           path="t.safetensors",
                           url_template="https://{host}/{repo}/resolve/{commit}/{path}")
    assert "?" not in url, "a repo may not end the path and start a query"
    assert SHA in url


def test_a_path_cannot_push_the_commit_into_a_fragment():
    url = fetch.pinned_url(host="h.example", repo="org/repo", commit=SHA,
                           path="#/../../elsewhere",
                           url_template="https://{host}/{repo}/{path}/{commit}")
    assert "#" not in url
    assert SHA in url


def test_a_template_with_no_commit_in_it_is_not_a_pin():
    with pytest.raises(fetch.FetchError, match="not a pinned fetch"):
        fetch.pinned_url(host="h.example", repo="org/repo", commit=SHA,
                         path="t.safetensors",
                         url_template="https://{host}/{repo}/main/{path}")


def test_a_commit_in_the_fragment_is_not_a_pin():
    """A fragment is never sent to the server, so it pins nothing."""
    with pytest.raises(fetch.FetchError, match="not a pinned fetch"):
        fetch.pinned_url(host="h.example", repo="org/repo", commit=SHA,
                         path="t.safetensors",
                         url_template="https://{host}/{repo}/{path}#{commit}")


def test_a_local_url_is_refused_rather_than_read(tmp_path):
    """A template is a fetch target that came out of a row.

    `file:` would make the client read the machine it is running on and hand
    the bytes back as an artifact. Refused because it cannot be verified by
    anybody else, not because of who the host is: any http or https host works.
    """
    secret = tmp_path / "secret"
    secret.write_bytes(b"not an artifact")
    with pytest.raises(fetch.FetchError, match="over the network"):
        fetch.pinned_url(host="", repo="x", commit=SHA, path="secret",
                         url_template=f"file://{tmp_path}/{{path}}?{{commit}}")


def test_a_template_that_will_not_format_says_which_fields_there_are():
    with pytest.raises(fetch.FetchError, match=r"\{host\}, \{repo\}"):
        fetch.pinned_url(host="h.example", repo="org/repo", commit=SHA,
                         path="t.safetensors",
                         url_template="https://{host}/{branch}/{commit}")


def test_a_format_spec_cannot_allocate_from_a_row():
    """`{repo:>200000000}` is 17 characters of template and 200 MB of string."""
    with pytest.raises(fetch.FetchError, match="format spec or a conversion"):
        fetch.pinned_url(host="h.example", repo="a", commit=SHA, path="t",
                         url_template="https://{host}/{repo:>200000000}/{commit}")


def test_a_template_cannot_reach_into_a_value():
    """`str.format` walks attributes. A URL is text and has no use for that."""
    with pytest.raises(fetch.FetchError, match="Attribute and index syntax"):
        fetch.pinned_url(host="h.example", repo="a/b", commit=SHA, path="t",
                         url_template="https://{host}/{repo.__class__}/{commit}")


def test_an_unclosed_brace_is_a_sentence_and_not_a_traceback():
    with pytest.raises(fetch.FetchError, match="not a URL template"):
        fetch.pinned_url(host="h.example", repo="a/b", commit=SHA, path="t",
                         url_template="https://{host}/{repo/{commit}")


# ------------------------------------------------------------------ ordering


def test_a_served_copy_wins_over_the_authors_repo(server, monkeypatch):
    """Ours first, because its availability is the thing we control."""
    asked = []
    real = fetch.from_repo
    monkeypatch.setattr(
        fetch, "from_repo",
        lambda **k: (asked.append(k["repo"]), real(**k))[1])
    fetch.resolve(artifact_path="t.safetensors",
                  served_repo="org/repo", served_commit=SHA,
                  artifact_repo="someone/else", artifact_commit="d" * 40)
    assert asked == ["org/repo"]


def test_a_served_copy_carries_its_own_host_too(server, monkeypatch):
    """004 keeps the two pairs apart; 007 widens both rather than one."""
    seen = {}
    real = fetch.from_repo
    monkeypatch.setattr(fetch, "from_repo",
                        lambda **k: (seen.update(k), real(**k))[1])
    fetch.resolve(artifact_path="t.safetensors",
                  served_repo="org/repo", served_commit=SHA,
                  served_host=GITHUB_HOST,
                  served_url_template=raw_template(server))
    assert seen["host"] == GITHUB_HOST
    assert seen["url_template"] == raw_template(server)


def test_a_local_path_is_used_when_no_repo_is_recorded(tmp_path, monkeypatch):
    """How the fixtures work, and how anyone runs this with no network."""
    monkeypatch.setattr(fetch, "ROOT", tmp_path)
    (tmp_path / "fixtures").mkdir()
    (tmp_path / "fixtures" / "x.safetensors").write_bytes(BLOB)
    assert fetch.resolve(artifact_path="fixtures/x.safetensors") == BLOB


def test_nothing_recorded_anywhere_is_an_error_not_an_empty_result():
    with pytest.raises(fetch.FetchError, match="no artifact recorded"):
        fetch.resolve(artifact_path=None)


# ------------------------------------------------------------ the read path


def _row(database: Path, **pin) -> None:
    """One submission and one intervention, enough for `client.load`.

    Every value here is structural. No score is recorded, because none was
    measured and this test is about where bytes come from.
    """
    conn = db.connect(database)
    db.migrate(conn)
    conn.execute(
        "INSERT INTO submission (author,model_id,label,version,definition,"
        "created_at,is_synthetic) VALUES ('t','m/none','pinned','v1',"
        "'A test row. Not a claim about any trait.','2026-09-18T00:00:00Z',1)")
    columns = ["author", "model_id", "label", "version", "id", "kind", "layer",
               "layer_convention", "hook_point", "shape", "dtype",
               "is_synthetic", *pin]
    values = ["t", "m/none", "pinned", "v1", "iv-t", "direction", 0,
              "block-0indexed", "resid_post", "[8]", "float32", 1, *pin.values()]
    conn.execute(
        f"INSERT INTO intervention ({','.join(columns)}) VALUES "
        f"({','.join('?' * len(values))})", values)
    conn.commit()
    conn.close()


def test_the_client_resolves_a_row_pinned_on_a_non_hub_host(server, tmp_path):
    """`client.load(...).vector()`, end to end, against a template in a row.

    The point of the whole change: the resolver has never heard of this layout
    and the row does not need it to.
    """
    database = tmp_path / "pinned.db"
    _row(database,
         artifact_path="t.safetensors",
         artifact_repo="org/repo",
         artifact_commit=SHA,
         artifact_host=GITHUB_HOST,
         artifact_url_template=media_template(server))
    tensor = client.load("t/pinned@v1", database=database).vector()
    assert tensor.tolist() == list(range(8))


def test_the_client_reads_the_template_and_not_only_the_repo(server, tmp_path):
    """Two rows differing only in template resolve to different tensors."""
    database = tmp_path / "raw.db"
    _row(database,
         artifact_path="t.safetensors",
         artifact_repo="org/repo",
         artifact_commit=SHA,
         artifact_host=GITHUB_HOST,
         artifact_url_template=raw_template(server))
    tensor = client.load("t/pinned@v1", database=database).vector()
    assert tensor.tolist() == [n + 100 for n in range(8)]


def test_a_row_with_no_host_is_not_an_error(server, tmp_path):
    """Every row in this database today, and none of them is broken."""
    database = tmp_path / "hostless.db"
    _row(database,
         artifact_path="t.safetensors",
         artifact_repo="org/repo",
         artifact_commit=SHA)
    tensor = client.load("t/pinned@v1", database=database).vector()
    assert tensor.tolist() == list(range(8))


def test_a_pre_007_database_upgrades_and_resolves_the_same(server, tmp_path):
    """The migration has to leave a pinned row pointing where it pointed.

    Built by applying everything up to 006 and pinning a row the way a row got
    pinned then, which is a repo and a commit and no host at all. Then 007, and
    then the same fetch. If this needed a backfill to pass, absence would not be
    a state.
    """
    database = tmp_path / "old.db"
    conn = db.connect(database)
    conn.execute("CREATE TABLE _migration (name TEXT PRIMARY KEY,"
                 " applied_at TEXT NOT NULL)")
    for sql in sorted(db.MIGRATIONS_DIR.glob("*.sql")):
        if sql.name.startswith("007"):
            break
        conn.executescript(sql.read_text())
        conn.execute("INSERT INTO _migration VALUES (?, 'before')", (sql.name,))
    # Written the way a row was written then, which is the point: the
    # submission carries no `model_id` because 010 had not happened, and the
    # only record of the model is on the intervention. 010 is what carries it
    # across, and this is the database that proves it does.
    conn.execute(
        "INSERT INTO submission (author,label,version,definition,"
        "created_at,is_synthetic) VALUES ('t','pinned','v1',"
        "'A row written before there was a host column.',"
        "'2026-09-18T00:00:00Z',1)")
    conn.execute(
        "INSERT INTO intervention (author,label,version,id,kind,model_id,layer,"
        "layer_convention,hook_point,shape,dtype,is_synthetic,artifact_path,"
        "artifact_repo,artifact_commit) VALUES ('t','pinned','v1','iv-t',"
        "'direction','m/none',0,'block-0indexed','resid_post','[8]','float32',"
        "1,'t.safetensors','org/repo',?)", (SHA,))
    conn.commit()

    # The first thing applied, not the only thing. This asserted the whole list
    # and so quietly became a claim about how many migrations exist after 007,
    # which broke on 008 and had nothing to do with what is under test here.
    applied = db.migrate(conn)
    assert applied and applied[0] == "007_any_host.sql", applied
    row = conn.execute(
        "SELECT artifact_host, artifact_url_template FROM intervention"
    ).fetchone()
    conn.close()
    assert tuple(row) == (None, None), (
        "the migration backfilled a host onto a row nobody recorded one for, "
        "which produces a string rather than a fact and reads exactly like a "
        "fact somebody checked"
    )
    assert client.load("t/pinned@v1", database=database).vector().tolist() \
        == list(range(8))


def test_the_schema_puts_no_check_on_either_column(tmp_path):
    """A host nobody has met has to be storable, which means no enumeration."""
    database = tmp_path / "open.db"
    _row(database,
         artifact_path="t.safetensors",
         artifact_repo="whoever/whatever",
         artifact_commit=SHA,
         artifact_host="a-host-nobody-has-met.invalid",
         artifact_url_template="gopher://{host}/{repo}/{commit}/{path}")
    conn = sqlite3.connect(database)
    stored = conn.execute(
        "SELECT artifact_host FROM intervention").fetchone()[0]
    assert stored == "a-host-nobody-has-met.invalid", (
        "the column stored it, which is the point. Whether a fetch can happen "
        "over that scheme is `controlbun.fetch`'s question and it answers it at "
        "fetch time, with a sentence, rather than by refusing the row."
    )


# -------------------------------------------------------------- the real Hub


def _online() -> bool:
    try:
        urllib.request.urlopen("https://huggingface.co", timeout=5)
        return True
    except Exception:
        return False


@pytest.mark.skipif(not _online(), reason="offline")
def test_the_real_hub_serves_a_real_lfs_object_byte_identical():
    """The one thing a local server cannot stand in for.

    `.safetensors` is LFS-tracked by the default gitattributes on a model repo no
    matter how small the file is, so this 96-byte object took the full LFS path on
    upload and comes back through a CDN redirect. Every real artifact will do the
    same, and this is the only test that proves our code survives it.
    """
    blob = fetch.from_repo(repo="controlbun/fetch-test", commit=SHA,
                           path="t.safetensors")
    assert hashlib.sha256(blob).hexdigest() == hashlib.sha256(BLOB).hexdigest()
    assert load_bytes(blob)["t"].tolist() == list(range(8))
